import re
import uuid
import logging
from typing import List, Optional
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from core.dtos.music import (
    PieceDTO,
    PartDTO,
    PartAssetDTO,
    PartAssetUploadDTO,
    InstrumentDTO,
    InstrumentSectionDTO,
)
from core.enum.music import PartAssetType
from core.enum.instruments import (
    InstrumentEnum,
    InstrumentSectionEnum,
    INSTRUMENT_SECTIONS,
)
from core.enum.status import UploadStatus
from core.models.organizations import Musician, SetupChecklist
from core.models.music import (
    Piece,
    Part,
    PartAsset,
    PartInstrument,
    Instrument,
    InstrumentSection,
    MusicianInstrument,
)
from core.services.s3 import create_upload_url
from core.utils import get_file_extension, is_integer

logger = logging.getLogger()

# Codes used in parsing instrumentation notation
CODE_MAP = {
    "pic": [InstrumentEnum.PICCOLO],
    "picc": [InstrumentEnum.PICCOLO],
    "eh": [InstrumentEnum.ENGLISH_HORN],
    "bcl": [InstrumentEnum.BASS_CLARINET],
    "bkl": [InstrumentEnum.BASS_CLARINET],
    "hp": [InstrumentEnum.HARP],
    "cel": [InstrumentEnum.CELESTA],
    "pf": [InstrumentEnum.PIANO],
    "tmp": [InstrumentEnum.TIMPANI],
    "str": [
        InstrumentEnum.VIOLIN_1,
        InstrumentEnum.VIOLIN_2,
        InstrumentEnum.VIOLA,
        InstrumentEnum.CELLO,
        InstrumentEnum.DOUBLE_BASS,
    ],
    "cbn": [InstrumentEnum.CONTRABASSOON],
    "electronica": [InstrumentEnum.ELECTRONICA],
    "bd": [InstrumentEnum.BASS_DRUM],
    "sd": [InstrumentEnum.SNARE_DRUM],
    "tam-tam": [InstrumentEnum.TAM_TAM],
    "cym": [InstrumentEnum.CYMBAL],
    "tri": [InstrumentEnum.TRIANGLE],
}

# Aliases used in parsing part filenames
ALIAS_MAP = {
    InstrumentEnum.FRENCH_HORN: ["horn"],
    InstrumentEnum.ENGLISH_HORN: ["cor anglais"],
    InstrumentEnum.DOUBLE_BASS: ["bass"],
    InstrumentEnum.PERCUSSION: ["perc"],
}

WOODWIND_ORDER = [
    InstrumentEnum.FLUTE,
    InstrumentEnum.OBOE,
    InstrumentEnum.CLARINET,
    InstrumentEnum.BASSOON,
]

BRASS_ORDER = [
    InstrumentEnum.FRENCH_HORN,
    InstrumentEnum.TRUMPET,
    InstrumentEnum.TROMBONE,
    InstrumentEnum.TUBA,
]

DASH_PATTERN = re.compile(r"\s*[—-]\s*")


@transaction.atomic
def create_piece(
    organization_id: str,
    title: str,
    composer: str,
    instrumentation: str,
    duration: Optional[int],
    domo_id: Optional[str],
    composer_domo_id: Optional[str],
) -> PieceDTO:
    piece = Piece(
        organization_id=organization_id,
        title=title,
        composer=composer,
        instrumentation=instrumentation,
        duration=duration,
        domo_id=domo_id,
        composer_domo_id=composer_domo_id,
    )
    piece.save()

    create_parts_from_instrumentation(piece.id, piece.instrumentation)

    setup_checklist = SetupChecklist.objects.get(organization_id=organization_id)
    if not setup_checklist.completed:
        setup_checklist.piece_completed = True
        setup_checklist.completed = True
        setup_checklist.completed_date = timezone.now()
        setup_checklist.save()

    return PieceDTO.from_model(piece)


def get_piece(organization_id: str, piece_id: str) -> PieceDTO:
    piece = Piece.objects.get(id=piece_id, organization__id=organization_id)
    completed_parts = (
        Part.objects.filter(
            piece_id=piece_id, assets__status=UploadStatus.UPLOADED.value
        )
        .distinct()
        .count()
    )
    return PieceDTO.from_model(piece, completed_parts=completed_parts)


def get_pieces(organization_id: str) -> List[PieceDTO]:
    query = Q(organization__id=organization_id)
    piece_models = Piece.objects.filter(query).annotate(
        parts_count=Count("parts", distinct=True),
        completed_parts=Count(
            "parts",
            filter=Q(
                parts__assets__status=UploadStatus.UPLOADED.value,
                parts__assets__asset_type=PartAssetType.CLEAN.value,
            ),
            distinct=True,
        ),
    )
    return PieceDTO.from_models(piece_models)


def search_for_piece(
    title: Optional[str] = None,
    composer: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> List[PieceDTO]:
    search_query = Q()
    if title:
        search_query |= Q(title__icontains=title)
    if composer:
        search_query |= Q(composer__icontains=composer)

    pieces = Piece.objects.filter(search_query)
    if organization_id:
        pieces = pieces.filter(organization__id=organization_id)
    return PieceDTO.from_models(pieces)


def create_part(
    piece_id: str,
    primary: InstrumentEnum,
    instruments: List[InstrumentEnum],
    number: Optional[int] = None,
) -> PartDTO:
    part = Part(id=uuid.uuid4(), piece_id=str(piece_id), number=number)
    part.save()
    for instrument in instruments:
        instrument_model = get_instrument(instrument)
        part_instrument = PartInstrument(
            part_id=part.id,
            instrument_id=instrument_model.id,
            primary=True if instrument == primary else False,
        )
        part_instrument.save()

    return PartDTO.from_model(part)


@transaction.atomic
def create_part_asset(
    piece_id: str, filename: str, asset_type: PartAssetType
) -> PartAssetUploadDTO:
    piece = Piece.objects.get(id=piece_id)
    parts = Part.objects.filter(piece_id=piece_id)
    part_asset = PartAsset(id=uuid.uuid4(), piece_id=piece_id)
    part_asset.save()
    normalized_filename = _normalize_filename(filename)

    # Determine the corresponding part for the filename
    instruments = get_instruments_in_string(filename)
    numbered_instruments = _extract_numbered_instruments(filename, instruments)
    for part in parts:
        for part_instrument in part.instruments.all():
            instrument_enum = InstrumentEnum(part_instrument.instrument.name)
            if instrument_enum in instruments:
                numbers = numbered_instruments.get(instrument_enum)
                is_combined_part = not numbers
                if part.assets.exists() and not is_combined_part:
                    continue
                if numbers and part.number not in numbers:
                    continue
                part_asset.parts.add(part)
                break

    # Generate a pre-signed URL for upload (expires in 10 minutes)
    file_key = (
        str(piece_id)
        + "/"
        + str(part_asset.id)
        + get_file_extension(normalized_filename)
    )
    presigned_url = create_upload_url(
        organization_id=str(piece.organization.id),
        file_key=file_key,
        expiration=600,
    )

    part_asset.file_key = file_key
    part_asset.upload_url = presigned_url
    part_asset.upload_filename = filename
    part_asset.asset_type = asset_type.value
    part_asset.status = UploadStatus.PENDING.value
    part_asset.save()

    return PartAssetUploadDTO.from_model(part_asset)


@transaction.atomic
def update_part_asset(
    organization_id: str,
    part_asset_id: str,
    part_ids: Optional[List[str]] = None,
    status: Optional[UploadStatus] = None,
) -> PartAssetDTO:
    part_asset = PartAsset.objects.get(
        id=part_asset_id, piece__organization_id=organization_id
    )
    if status:
        part_asset.status = status.value
        part_asset.save()
    if part_ids:
        parts = Part.objects.filter(
            id__in=part_ids, piece__organization_id=organization_id
        )
        part_asset.parts.set(parts)
    else:
        part_asset.parts.set([])

    return PartAssetDTO.from_model(part_asset)


def delete_part_asset(organization_id: str, part_asset_id: str) -> None:
    PartAsset.objects.get(
        id=part_asset_id, piece__organization_id=organization_id
    ).delete()


def get_part_asset(organization_id: str, part_asset_id: str) -> PartAssetDTO:
    part_asset = PartAsset.objects.get(
        id=part_asset_id, piece__organization_id=organization_id
    )
    return PartAssetDTO.from_model(part_asset)


def get_part_assets(
    organization_id: str, piece_id: str, asset_type: PartAssetType
) -> List[PartAssetDTO]:
    piece = Piece.objects.get(id=piece_id, organization_id=organization_id)
    part_assets = PartAsset.objects.filter(
        piece_id=piece.id,
        asset_type=asset_type.value,
        piece__organization_id=organization_id,
    ).order_by("-upload_filename")
    return PartAssetDTO.from_models(part_assets)


def get_parts(organization_id: str, piece_id: str) -> List[PartDTO]:
    parts = Part.objects.filter(
        piece_id=piece_id, piece__organization_id=organization_id
    )
    return PartDTO.from_models(parts)


def get_instrument(
    instrument: InstrumentEnum,
) -> InstrumentDTO | None:
    instrument_model = Instrument.objects.filter(name=instrument.value).first()
    if instrument_model:
        return InstrumentDTO.from_model(instrument_model)
    else:
        return None


def get_instruments_in_string(filename: str) -> List[InstrumentEnum]:
    instruments = []
    tokens = _split_filename_tokens(filename)
    normalized_tokens = [re.sub(r"[^a-z0-9]", "", t.lower()) for t in tokens]
    for instrument in InstrumentEnum:
        needle = _normalize_instrument_name(instrument.value)

        # Look for the instrument name inside filename tokens
        matches_phrase = any(
            _instrument_token_match(needle, token) for token in normalized_tokens
        )

        # Handle Violin 1 and 2 edge cases since the number is part of the instrument/section name
        if not matches_phrase and instrument in {
            InstrumentEnum.VIOLIN_1,
            InstrumentEnum.VIOLIN_2,
        }:
            for index, token in enumerate(normalized_tokens):
                if token != "violin":
                    continue
                next_token = (
                    normalized_tokens[index + 1]
                    if index + 1 < len(normalized_tokens)
                    else ""
                )
                if next_token == "1" and instrument == InstrumentEnum.VIOLIN_1:
                    matches_phrase = True
                    break
                if next_token == "2" and instrument == InstrumentEnum.VIOLIN_2:
                    matches_phrase = True
                    break

        # Look for any instrument aliases inside the filename (if there are any)
        aliases = [
            _normalize_instrument_name(alias) for alias in ALIAS_MAP.get(instrument, [])
        ]
        matches_alias = any(
            _instrument_token_match(alias, token)
            for alias in aliases
            for token in normalized_tokens
        )
        if matches_phrase or matches_alias:
            instruments.append(instrument)
    return instruments


@transaction.atomic
def update_musician_instruments(musician_id: str, instruments: List[InstrumentEnum]):
    musician = Musician.objects.get(id=musician_id)
    instrument_strings = [instrument.value for instrument in instruments]

    instrument_models = list(Instrument.objects.filter(name__in=instrument_strings))

    # 1) Clear existing links
    MusicianInstrument.objects.filter(musician=musician).delete()

    # 2) Recreate
    MusicianInstrument.objects.bulk_create(
        [
            MusicianInstrument(musician=musician, instrument=instrument_model)
            for instrument_model in instrument_models
        ]
    )


@transaction.atomic
def create_parts_from_instrumentation(piece_id: str, notation: str) -> List[PartDTO]:
    # Split on em dash / hyphen
    segments = [seg.strip() for seg in DASH_PATTERN.split(notation) if seg.strip()]
    result: List[PartDTO] = []
    # 1) Woodwinds: by position
    if segments:
        winds = _parse_bracketable_section(piece_id, segments[0], "woodwinds")
        result.extend(winds)

    # 2) Brass: by position
    if len(segments) >= 2:
        brass = _parse_bracketable_section(piece_id, segments[1], "brass")
        result.extend(brass)

    # 3) Everything after that can be auxiliary, electronic, perc, strings (hp, cel, pf, str, etc.)
    for seg in segments[2:]:
        code = _normalize_filename_token(seg)
        if not code or _is_no_strings(code):
            continue

        # Is this a percussion segment?
        if _is_percussion_segment(seg):
            percussion = _parse_percussion(piece_id, seg)
            result.extend(percussion)
            continue

        # Is there a doubling of some kind? (pf/cel)
        if "/" in code:
            instruments = []
            primary_code, doubling_code = code.split("/", 1)

            # Figure out the primary instrument
            primary_code = _normalize_filename_token(primary_code)
            primary_instrument = CODE_MAP.get(primary_code)
            if not primary_instrument:
                logger.warning(f"Unknown instrument code {code}")
                continue
            primary_instrument = primary_instrument[0]
            instruments.append(primary_instrument)

            # Figure out the doubling
            doubling_code = _normalize_filename_token(doubling_code)
            doubling_sections = CODE_MAP.get(doubling_code)
            if doubling_sections:
                for doubling in doubling_sections:
                    instruments.append(doubling)

            part = create_part(
                piece_id=piece_id,
                primary=primary_instrument,
                instruments=instruments,
                number=None,
            )
            result.append(part)
            continue

        instruments = CODE_MAP.get(code)
        if not instruments:
            logger.warning(f"Unknown instrument code {code}")
            continue

        for section in instruments:
            part = create_part(
                piece_id=piece_id,
                primary=section,
                instruments=[section],
                number=None,
            )
            result.append(part)

    return result


def looks_like_numbered_part(tail: str) -> bool:
    # These are parts with numbers that don't correspond to the seat number (i.e. violin 1)
    # and need to be exempted from this check
    unnumbered_parts = [
        InstrumentEnum.VIOLIN_1.value.lower(),
        InstrumentEnum.VIOLIN_2.value.lower(),
    ]

    # e.g. " 2.pdf", "_ii.pdf", "-1", "(III)"
    PART_NUMBER_REGEX = re.compile(
        r"""(?:^|[^a-z0-9])(?:1|2|3|4|5|i|ii|iii|iv|v)(?:[^a-z0-9]|$)""", re.VERBOSE
    )
    return bool(PART_NUMBER_REGEX.search(tail)) and not any(
        unnumbered_part in tail for unnumbered_part in unnumbered_parts
    )


def get_instrument_section(
    instrument: InstrumentEnum,
) -> InstrumentSectionDTO:
    instrument_section = None
    if instrument in INSTRUMENT_SECTIONS[InstrumentSectionEnum.WOODWINDS]:
        instrument_section = InstrumentSectionEnum.WOODWINDS
    elif instrument in INSTRUMENT_SECTIONS[InstrumentSectionEnum.BRASS]:
        instrument_section = InstrumentSectionEnum.BRASS
    elif instrument in INSTRUMENT_SECTIONS[InstrumentSectionEnum.PERCUSSION]:
        instrument_section = InstrumentSectionEnum.PERCUSSION
    elif instrument in INSTRUMENT_SECTIONS[InstrumentSectionEnum.AUXILIARY]:
        instrument_section = InstrumentSectionEnum.AUXILIARY
    elif instrument in INSTRUMENT_SECTIONS[InstrumentSectionEnum.STRINGS]:
        instrument_section = InstrumentSectionEnum.STRINGS
    elif instrument in INSTRUMENT_SECTIONS[InstrumentSectionEnum.VOICE]:
        instrument_section = InstrumentSectionEnum.VOICE
    else:
        instrument_section = InstrumentSectionEnum.OTHER

    instrument_section_model = InstrumentSection.objects.get(
        name=instrument_section.value
    )
    return InstrumentSectionDTO.from_model(instrument_section_model)


def _parse_bracketable_section(
    piece_id: str, segment: str, section: str
) -> List[PartDTO]:
    """
    Parse a bracketable section (woodwinds or brass) and create parts.

    The segment uses positional counts with optional bracket details:
        "2[1.2/pic] 2[1.2/eh] 2[1.2] 2[1.2]" → Fl, Ob, Cl, Bn

    Bracket details can specify doublings (e.g. "/pic") or direct instrument codes.
    """
    out: List[InstrumentEnum] = []
    tokens = _normalize_instrumentation_token(segment).split()

    # Use the right instrument order based on the section
    if section == "brass":
        order = BRASS_ORDER
    elif section == "woodwinds":
        order = WOODWIND_ORDER

    for index, token in enumerate(tokens):
        if index >= len(order):
            break

        # Extract leading count and optional bracket
        match = re.match(r"(?P<instrument_count>\d+)(?P<section_details>.*)", token)
        if not match:
            continue

        # Determine the number of instruments
        instrument_count = int(match.group("instrument_count"))

        # Are there instrument details in bracket notation? e.g. [1.2/pic] or [1.2/Eh]
        # If so grab them and strip brackets
        section_details = match.group("section_details")
        if section_details:
            section_details = section_details.strip("[]()")

        # Add base instruments
        for instrument_number in range(instrument_count):
            instruments = []

            # Determine the details for this instrument number in section details
            if section_details:
                instrument_details = section_details.split(".")[instrument_number]

                # Is there a doubling?
                if "/" in instrument_details:
                    # Add the base instrument section
                    primary_instrument = order[index]
                    instruments.append(primary_instrument)

                    # Figure out and add the doubling
                    _, doubling_code = instrument_details.split("/", 1)
                    doubling_code = doubling_code.strip().lower()
                    doubling_instruments = CODE_MAP.get(doubling_code)
                    if not doubling_instruments:
                        raise Exception(
                            f"Unable to find instrument for abbreviation '{instrument_details}'"
                        )
                    if doubling_instruments:
                        for doubling in doubling_instruments:
                            instruments.append(doubling)
                # Is it just a numeric part that uses only the base instrument?
                elif is_integer(instrument_details):
                    primary_instrument = order[index]
                    instruments.append(primary_instrument)
                # Is it a dedicated part that uses a different instrument?
                else:
                    instruments = CODE_MAP.get(instrument_details)
                    if not instruments:
                        raise Exception(
                            f"Unable to find instrument for abbreviation '{instrument_details}'"
                        )
                    primary_instrument = instruments[0]
                    instruments = [primary_instrument]
            else:
                primary_instrument = order[index]
                instruments = [primary_instrument]

            # Create the part
            part = create_part(
                piece_id, primary_instrument, instruments, instrument_number + 1
            )
            out.append(part)

    return out


def _parse_percussion(piece_id: str, segment: str) -> List[PartDTO]:
    """
    Parse percussion segments and create timpani/percussion parts.

    Examples:
        "tmp+1"  -> 1 Timpani, 1 Percussion
        "timp+5" -> 1 Timpani, 5 Percussion
        "5perc"  -> 5 Percussion
    """
    out: List[InstrumentEnum] = []
    segment = _normalize_filename_token(segment)
    if not segment:
        return

    match = re.match(r"^(?P<code>timp|tmp)(?:\+(?P<percussion_count>\d+))?$", segment)
    if match:
        percussion_count = int(match.group("percussion_count") or 0)
        # Create the part
        part = create_part(
            piece_id=piece_id,
            primary=InstrumentEnum.TIMPANI,
            instruments=[InstrumentEnum.TIMPANI],
            number=1,
        )
        out.append(part)
        if percussion_count > 0:
            for percussion_number in range(percussion_count):
                part = create_part(
                    piece_id=piece_id,
                    primary=InstrumentEnum.PERCUSSION,
                    instruments=[InstrumentEnum.PERCUSSION],
                    number=percussion_number + 1,
                )
                out.append(part)
        return out

    match = re.match(r"^(?P<count>\d+)?perc$", segment)
    if match:
        percussion_count = int(match.group("count") or 1)
        for percussion_number in range(percussion_count):
            part = create_part(
                piece_id=piece_id,
                primary=InstrumentEnum.PERCUSSION,
                instruments=[InstrumentEnum.PERCUSSION],
                number=percussion_number + 1,
            )
            out.append(part)
        return out

    return out


def _extract_numbered_instruments(
    filename: str, instruments: List[InstrumentEnum]
) -> dict[InstrumentEnum, set[int]]:
    """
    For each instrument found in a filename, extract the set of part numbers
    that immediately follow that instrument name.
    """
    normalized_filename = _normalize_instrument_name(filename)
    out: dict[InstrumentEnum, set[int]] = {}
    for instrument in instruments:
        if instrument in {InstrumentEnum.VIOLIN_1, InstrumentEnum.VIOLIN_2}:
            continue
        needles = [_normalize_instrument_name(instrument.value)] + [
            _normalize_instrument_name(alias) for alias in ALIAS_MAP.get(instrument, [])
        ]
        for needle in needles:
            numbers = _extract_numbers_after_instrument(normalized_filename, needle)
            if numbers:
                out[instrument] = numbers
                break
    return out


def _extract_numbers_after_instrument(token: str, needle: str) -> Optional[set[int]]:
    """
    Extracts part numbers that immediately follow an instrument token.

    Examples:
        token="...flute1.pdf", needle="flute" -> {1}
        token="...trombone-1-2.pdf", needle="trombone" -> {1, 2}

    Notes:
        - Treats concatenated digits as separate part numbers (e.g., "12" -> {1, 2}).
        - Ignores zeros.
    """
    match = re.search(rf"{re.escape(needle)}(?P<num>[\d\-]+)", token)
    if not match:
        return None
    number_string = match.group("num")
    digits = [int(char) for char in number_string if char.isdigit() and char != "0"]
    if len(digits) == 1:
        return {digits[0]}
    numbers = set(digits)
    return numbers or None


def _instrument_token_match(needle: str, token: str) -> bool:
    """
    Return True if the normalized instrument name appears in a filename token.

    Ensures the match starts at a token boundary or before digits.
    """
    return re.search(rf"(?<![a-z]){re.escape(needle)}(?:(?=\d)|\b)", token) is not None


def _normalize_instrumentation_token(seg: str) -> str:
    """
    Normalize instrumentation notation tokens.

    - Removes "opt"
    - Normalizes dash/underscore to spaces
    - Collapses whitespace
    - Lowercases
    Example: "Violin-1" -> "violin 1"
    """
    # Remove tokens like "opt"
    seg = re.sub(r"\bopt\b", "", seg)
    seg = re.sub(r"[-_]+", " ", seg)  # violin-1, violin_1 -> violin 1
    seg = re.sub(r"\s+", " ", seg).lower()
    return seg


def _normalize_filename_token(seg: str) -> str:
    """
    Normalize filename tokens for instrument matching.

    - Removes "opt"
    - Strips separators between letters/digits (e.g., "violin-1" -> "violin1")
    - Lowercases
    """
    # Remove tokens like "opt"
    seg = re.sub(r"\bopt\b", "", seg)
    seg = re.sub(r"[-_]+", "", seg)  # violin-1, violin_1 -> violin1
    seg = re.sub(r"\s+", " ", seg).strip().lower()
    return seg


def _is_no_strings(code: str) -> bool:
    """Return True if the token indicates strings are explicitly omitted."""
    return code in {"[no str]", "no str", "[nostr]", "nostr"}


def _is_percussion_segment(seg: str) -> bool:
    """Return True if a segment represents percussion/timpani notation."""
    seg = seg.strip().lower()
    return bool(re.match(r"^(timp|tmp)(?:\+\d+)?$", seg) or re.match(r"^\d*perc$", seg))


def _normalize_filename(name: str) -> str:
    """
    Normalize full filenames for number extraction.

    - Lowercases
    - Converts separators to spaces
    - Collapses whitespace
    """
    name = name.lower()
    name = re.sub(r"[-_]+", " ", name)  # violin-1, violin_1 -> violin 1
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _split_filename_tokens(name: str) -> List[str]:
    """
    Split a filename into tokens on separators, keeping digits attached to words.
    """
    return [token for token in re.split(r"[\s._-]+", name) if token]


def _normalize_instrument_name(name: str) -> str:
    """
    Normalize an instrument name by removing all non-alphanumeric characters.
    """
    return re.sub(r"[^a-zA-Z0-9]", "", name).lower()
