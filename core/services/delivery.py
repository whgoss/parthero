from collections import defaultdict
import re
from typing import List
from core.dtos.music import PartDTO
from core.dtos.programs import (
    ProgramDeliveryDTO,
    ProgramDeliveryDownloadFileDTO,
    ProgramDeliveryDownloadsDTO,
    ProgramDeliveryFileDTO,
    ProgramDeliveryPieceDTO,
)
from core.dtos.organizations import OrganizationDTO
from core.enum.music import PartAssetType
from core.enum.status import UploadStatus
from core.models.music import PartAsset
from core.models.programs import Program, ProgramPartMusician
from core.services.s3 import create_download_url
from parthero.settings import DOWNLOAD_URL_EXPIRATION_SECONDS


def _get_delivery_assignments_for_musician(
    program_id: str, musician_id: str
) -> List[ProgramPartMusician]:
    """Return explicit part assignments for the musician on this program."""
    return list(
        ProgramPartMusician.objects.filter(
            program_id=program_id,
            musician_id=musician_id,
        )
        .select_related("part__piece")
        .prefetch_related("part__instruments__instrument")
        .order_by("part__piece__title", "part__number", "id")
    )


def _get_delivery_assets_for_part_ids(
    program_id: str, part_ids: set[str]
) -> List[PartAsset]:
    """Return uploaded clean/bowing assets scoped to part IDs."""
    if not part_ids:
        return []

    return list(
        PartAsset.objects.filter(
            piece__programpiece__program_id=program_id,
            parts__id__in=part_ids,
            asset_type__in=[PartAssetType.CLEAN.value, PartAssetType.BOWING.value],
            status=UploadStatus.UPLOADED.value,
        )
        .select_related("piece")
        .prefetch_related("parts")
        .distinct()
        .order_by("piece__title", "asset_type", "upload_filename")
    )


def _sanitize_download_filename(value: str) -> str:
    """Strip characters that are unsafe in common local filesystem names."""
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", value).strip()
    return sanitized or "part"


def _delivery_download_filename(asset: PartAsset, part_display_name: str) -> str:
    """Build a friendly filename from piece title + assigned part descriptor."""
    if asset.asset_type == PartAssetType.BOWING.value:
        descriptor = f"{part_display_name} (Bowing)"
    else:
        descriptor = f"{part_display_name}"

    base = _sanitize_download_filename(f"{asset.piece.title} - {descriptor}")
    return f"{base}.pdf"


def _get_delivery_file_rows(program_id: str, musician_id: str) -> list[dict]:
    """Return flattened delivery rows for a musician on a program.

    Each row represents one downloadable file entry on the delivery page.
    Rows are keyed by the tuple (asset, assigned part) so combined assets can
    appear once per assigned part with chair-specific filenames.
    """
    assignments = _get_delivery_assignments_for_musician(
        program_id=program_id,
        musician_id=musician_id,
    )
    if not assignments:
        return []

    part_ids = {str(assignment.part_id) for assignment in assignments}
    assets = _get_delivery_assets_for_part_ids(program_id=program_id, part_ids=part_ids)
    if not assets:
        return []

    assets_by_part_id: defaultdict[str, list[PartAsset]] = defaultdict(list)
    for asset in assets:
        # A single asset may be linked to multiple parts (combined parts), so index
        # each asset under every relevant assigned part.
        for part in asset.parts.all():
            part_id = str(part.id)
            if part_id in part_ids:
                assets_by_part_id[part_id].append(asset)

    for bucket in assets_by_part_id.values():
        # Keep deterministic ordering for stable UI rendering and tests.
        bucket.sort(
            key=lambda asset: (
                asset.asset_type != PartAssetType.CLEAN.value,
                (asset.upload_filename or "").lower(),
                str(asset.id),
            )
        )

    rows: list[dict] = []
    for assignment in assignments:
        part_id = str(assignment.part_id)
        part_display_name = PartDTO.from_model(assignment.part).display_name
        for asset in assets_by_part_id.get(part_id, []):
            rows.append(
                {
                    # Composite ID is intentional: one asset can yield multiple rows
                    # (one per assigned part), and frontend row keys must be unique.
                    "id": f"{asset.id}:{part_id}",
                    "piece_id": str(assignment.part.piece_id),
                    "piece_title": assignment.part.piece.title,
                    "piece_composer": assignment.part.piece.composer,
                    "filename": _delivery_download_filename(
                        asset=asset,
                        part_display_name=part_display_name,
                    ),
                    "asset": asset,
                }
            )
    return rows


def get_program_delivery_payload(
    program_id: str, musician_id: str
) -> ProgramDeliveryDTO:
    """Build piece-grouped delivery metadata shown on the magic-link page.

    This payload powers the delivery table UI and contains piece groupings with
    display filenames, but no pre-signed URLs yet.
    """
    program = Program.objects.get(id=program_id)
    organization = OrganizationDTO.from_model(program.organization)
    rows = _get_delivery_file_rows(
        program_id=program_id,
        musician_id=musician_id,
    )

    parts_map: defaultdict[str, list[ProgramDeliveryFileDTO]] = defaultdict(list)
    pieces_meta: dict[str, tuple[str, str]] = {}
    for row in rows:
        piece_id = row["piece_id"]
        pieces_meta[piece_id] = (row["piece_title"], row["piece_composer"])
        parts_map[piece_id].append(
            ProgramDeliveryFileDTO(
                id=row["id"],
                piece_id=piece_id,
                filename=row["filename"],
            )
        )

    pieces: list[ProgramDeliveryPieceDTO] = []
    for piece_id, files in parts_map.items():
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

    If ``piece_id`` is provided, only download rows for that piece are returned.
    IDs in the response are row IDs (asset+part), not raw asset IDs.
    """
    rows = _get_delivery_file_rows(
        program_id=program_id,
        musician_id=musician_id,
    )
    files: list[ProgramDeliveryDownloadFileDTO] = []
    for row in rows:
        if piece_id and row["piece_id"] != str(piece_id):
            continue
        asset = row["asset"]
        if not asset.file_key:
            continue
        url = create_download_url(
            organization_id=organization_id,
            file_key=asset.file_key,
            expiration=DOWNLOAD_URL_EXPIRATION_SECONDS,
            download_filename=row["filename"],
        )
        if not url:
            continue
        files.append(
            ProgramDeliveryDownloadFileDTO(
                id=row["id"],
                filename=row["filename"],
                url=url,
            )
        )
    return ProgramDeliveryDownloadsDTO(files=files)
