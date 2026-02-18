from collections import defaultdict
import re

from core.dtos.music import PartDTO
from core.dtos.programs import (
    ProgramDeliveryDTO,
    ProgramDeliveryDownloadFileDTO,
    ProgramDeliveryDownloadsDTO,
    ProgramDeliveryFileDTO,
    ProgramDeliveryPieceDTO,
)
from core.dtos.organizations import OrganizationDTO
from core.enum.instruments import INSTRUMENT_SECTIONS, InstrumentSectionEnum
from core.enum.music import PartAssetType
from core.enum.status import UploadStatus
from core.models.music import Part, PartAsset
from core.models.programs import Program, ProgramMusician, ProgramPartMusician
from core.services.music import get_part_instruments
from core.services.programs import get_program_musician_instruments
from core.services.s3 import create_download_url
from parthero.settings import DOWNLOAD_URL_EXPIRATION_SECONDS


def _get_delivery_part_ids_for_musician(program_id: str, musician_id: str) -> set[str]:
    """Resolve all part IDs this musician is allowed to download for a program.

    Sources of truth:
    - Explicit program part assignments (ProgramPartMusician)
    - Unassigned string parts that match the musician's roster string instruments
      (strings are not principal-assigned in this workflow)
    """
    assigned_part_ids = {
        str(part_id)
        for part_id in ProgramPartMusician.objects.filter(
            program_id=program_id,
            musician_id=musician_id,
        ).values_list("part_id", flat=True)
    }

    program_musician = (
        ProgramMusician.objects.filter(
            program_id=program_id,
            musician_id=musician_id,
        )
        .prefetch_related("instruments__instrument")
        .first()
    )
    if not program_musician:
        return assigned_part_ids

    # Program roster instrumentation drives string fallback eligibility.
    musician_instruments = get_program_musician_instruments(program_musician)
    if not musician_instruments:
        return assigned_part_ids

    # Strings are not principal-assigned in this workflow.
    # Include unassigned string parts for the musician's roster instruments.
    string_instruments = set(INSTRUMENT_SECTIONS[InstrumentSectionEnum.STRINGS])
    musician_string_instruments = musician_instruments.intersection(string_instruments)
    if not musician_string_instruments:
        return assigned_part_ids

    assigned_part_set = set(
        ProgramPartMusician.objects.filter(program_id=program_id).values_list(
            "part_id", flat=True
        )
    )
    unassigned_string_part_ids = set()
    candidate_parts = (
        Part.objects.filter(piece__programpiece__program_id=program_id)
        .prefetch_related("instruments__instrument")
        .distinct()
    )
    for part in candidate_parts:
        if part.id in assigned_part_set:
            continue
        if get_part_instruments(part).intersection(musician_string_instruments):
            unassigned_string_part_ids.add(str(part.id))

    return assigned_part_ids.union(unassigned_string_part_ids)


def _get_delivery_assets_for_musician(program_id: str, musician_id: str):
    """Return uploaded clean/bowing assets scoped to the musician's delivery parts."""
    delivery_part_ids = _get_delivery_part_ids_for_musician(
        program_id=program_id,
        musician_id=musician_id,
    )
    if not delivery_part_ids:
        return []

    return list(
        PartAsset.objects.filter(
            piece__programpiece__program_id=program_id,
            parts__id__in=delivery_part_ids,
            asset_type__in=[PartAssetType.CLEAN.value, PartAssetType.BOWING.value],
            status=UploadStatus.UPLOADED.value,
        )
        .select_related("piece")
        .prefetch_related("parts__instruments__instrument")
        .distinct()
        .order_by("piece__title", "upload_filename")
    )


def _sanitize_download_filename(value: str) -> str:
    """Strip characters that are unsafe in common local filesystem names."""
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", value).strip()
    return sanitized or "part"


def _delivery_download_filename(asset: PartAsset) -> str:
    """Build a friendly download filename from piece title + part descriptor."""
    part_names = sorted(
        [PartDTO.from_model(part).display_name for part in asset.parts.all()]
    )

    if asset.asset_type == PartAssetType.BOWING.value:
        descriptor = "Bowing"
    elif not part_names:
        descriptor = "Part"
    else:
        descriptor = part_names[0]
        if len(part_names) > 1:
            descriptor = f"{descriptor} (Combined)"

    base = _sanitize_download_filename(f"{asset.piece.title} - {descriptor}")
    return f"{base}.pdf"


def get_program_delivery_payload(
    program_id: str, musician_id: str
) -> ProgramDeliveryDTO:
    """Build piece-grouped delivery metadata shown on the magic-link page."""
    program = Program.objects.get(id=program_id)
    organization = OrganizationDTO.from_model(program.organization)
    part_assets = _get_delivery_assets_for_musician(
        program_id=program_id,
        musician_id=musician_id,
    )

    pieces_map: defaultdict[str, list[ProgramDeliveryFileDTO]] = defaultdict(list)
    pieces_meta: dict[str, tuple[str, str]] = {}
    for part_asset in part_assets:
        piece_id = str(part_asset.piece_id)
        pieces_meta[piece_id] = (part_asset.piece.title, part_asset.piece.composer)
        pieces_map[piece_id].append(
            ProgramDeliveryFileDTO(
                id=str(part_asset.id),
                piece_id=piece_id,
                filename=_delivery_download_filename(part_asset),
            )
        )

    pieces: list[ProgramDeliveryPieceDTO] = []
    for piece_id, files in pieces_map.items():
        title, composer = pieces_meta[piece_id]
        pieces.append(
            ProgramDeliveryPieceDTO(
                id=piece_id,
                title=title,
                composer=composer,
                files=files,
            )
        )
    pieces.sort(key=lambda p: p.title.lower())
    return ProgramDeliveryDTO(organization=organization, pieces=pieces)


def get_program_delivery_downloads(
    organization_id: str,
    program_id: str,
    musician_id: str,
    piece_id: str | None = None,
) -> ProgramDeliveryDownloadsDTO:
    """Create short-lived pre-signed download URLs for delivery assets.

    If ``piece_id`` is provided, only assets from that piece are returned.
    """
    assets = _get_delivery_assets_for_musician(
        program_id=program_id,
        musician_id=musician_id,
    )
    files: list[ProgramDeliveryDownloadFileDTO] = []
    for asset in assets:
        if piece_id and str(asset.piece_id) != str(piece_id):
            continue
        if not asset.file_key:
            continue
        url = create_download_url(
            organization_id=organization_id,
            file_key=asset.file_key,
            expiration=DOWNLOAD_URL_EXPIRATION_SECONDS,
            download_filename=_delivery_download_filename(asset),
        )
        if not url:
            continue
        files.append(
            ProgramDeliveryDownloadFileDTO(
                id=str(asset.id),
                filename=_delivery_download_filename(asset),
                url=url,
            )
        )
    return ProgramDeliveryDownloadsDTO(files=files)
