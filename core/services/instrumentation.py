import re
import logging
from typing import List
from core.dtos.music import PartSlotDTO
from core.enum.instruments import InstrumentSectionEnum, InstrumentFamily

logger = logging.getLogger()

CODE_MAP = {
    "pic": [InstrumentSectionEnum.PICCOLO],
    "eh": [InstrumentSectionEnum.ENGLISH_HORN],
    "bcl": [InstrumentSectionEnum.BASS_CLARINET],
    "hp": [InstrumentSectionEnum.HARP],
    "cel": [InstrumentSectionEnum.CELESTA],
    "pf": [InstrumentSectionEnum.PIANO],
    "tmp": [InstrumentSectionEnum.TIMPANI],
    "str": [
        InstrumentSectionEnum.VIOLIN_1,
        InstrumentSectionEnum.VIOLIN_2,
        InstrumentSectionEnum.VIOLA,
        InstrumentSectionEnum.CELLO,
        InstrumentSectionEnum.DOUBLE_BASS,
    ],
    "electronica": [InstrumentSectionEnum.ELECTRONICA],
}

WOODWIND_ORDER = [
    InstrumentSectionEnum.FLUTE,
    InstrumentSectionEnum.OBOE,
    InstrumentSectionEnum.CLARINET,
    InstrumentSectionEnum.BASSOON,
]

BRASS_ORDER = [
    InstrumentSectionEnum.FRENCH_HORN,
    InstrumentSectionEnum.TRUMPET,
    InstrumentSectionEnum.TROMBONE,
    InstrumentSectionEnum.TUBA,
]

DASH_PATTERN = re.compile(r"\s*[—-]\s*")


def parse_instrumentation(notation: str) -> List[PartSlotDTO]:
    # Split on em dash / hyphen
    segments = [seg.strip() for seg in DASH_PATTERN.split(notation) if seg.strip()]
    result: List[PartSlotDTO] = []
    # result = {
    #     InstrumentFamily.WOODWINDS: [],
    #     InstrumentFamily.BRASS: [],
    #     InstrumentFamily.PERCUSSION: [],
    #     InstrumentFamily.AUXILIARY: [],
    #     InstrumentFamily.STRINGS: [],
    #     InstrumentFamily.VOICE: [],
    # }

    # 1) Woodwinds: by position
    if segments:
        winds = _parse_woodwinds(segments[0])
        # result[InstrumentFamily.WOODWINDS] = winds
        result.extend(winds)

    # 2) Brass: by position
    if len(segments) >= 2:
        brass = _parse_brass(segments[1])
        # result[InstrumentFamily.BRASS] = brass
        result.extend(brass)

    # 3) Percussion (optional)
    # continue_from = 2
    # if len(segments) >= 3 and _is_percussion_segment(segments[2]):
    #     percussion = _parse_percussion(segments[2])
    #     # result[InstrumentFamily.PERCUSSION] = percussion
    #     result.extend(percussion)
    #     continue_from = 3

    # 4) Everything after that can be auxiliary, electronic, perc, strings (hp, cel, pf, str, etc.)
    for seg in segments[2:]:
        code = _normalize_token(seg)
        if not code or _is_no_strings(code):
            continue

        # Is this a percussion segment?
        if _is_percussion_segment(seg):
            percussion = _parse_percussion(seg)
            # result[InstrumentFamily.PERCUSSION] = percussion
            result.extend(percussion)

        # Is there a doubling of some kind? (pf/cel)
        if "/" in code:
            instrument_sections = []
            primary_code, doubling_code = code.split("/", 1)

            # Figure out the primary instrument
            primary_code = _normalize_token(primary_code)
            primary_instrument = CODE_MAP.get(primary_code)
            if not primary_instrument:
                logger.warning(f"Unknown instrument code {code}")
                continue
            primary_instrument = primary_instrument[0]
            instrument_sections.append(primary_instrument)

            # Figure out the doubling
            doubling_code = _normalize_token(doubling_code)
            doubling_sections = CODE_MAP.get(doubling_code)
            if doubling_sections:
                for doubling in doubling_sections:
                    instrument_sections.append(doubling)

            part_slot = PartSlotDTO(
                family=InstrumentFamily.WOODWINDS,
                primary=primary_instrument,
                number=None,
                instrument_sections=instrument_sections,
            )
            result.append(part_slot)
            continue

        instrument_sections = CODE_MAP.get(code)
        if not instrument_sections:
            logger.warning(f"Unknown instrument code {code}")
            continue

        family = (
            InstrumentFamily.STRINGS if code == "str" else InstrumentFamily.AUXILIARY
        )
        for section in instrument_sections:
            result.append(
                PartSlotDTO(
                    family=family,  # FIX: use computed family
                    primary=section,
                    number=None,
                    instrument_sections=[section],
                )
            )

    return result


def _parse_woodwinds(segment: str) -> List[PartSlotDTO]:
    """
    Example WW segment:
        "2[1.2/pic] 2[1.2/eh] 2[1.2] 2[1.2]" → positionally: Fl, Ob, Cl, Bn
    """
    out: List[InstrumentSectionEnum] = []
    tokens = _normalize_woowinds_token(segment)
    for index, token in enumerate(tokens):
        if index >= len(WOODWIND_ORDER):
            break

        base_instrument_section = WOODWIND_ORDER[index]

        # Extract leading count and optional bracket
        m = re.match(r"(?P<woodwinds_count>\d+)(?P<woodwinds_details>.*)", token)
        if not m:
            continue

        woodwinds_count = int(m.group("woodwinds_count"))
        woodwinds_details = m.group("woodwinds_details")

        # Add base instruments
        for instrument_number in range(woodwinds_count):
            instrument_sections = []

            # Add the base instrument section
            instrument_sections.append(base_instrument_section)

            # Grab the instrument details for this instrument number
            bracket = re.search(
                r"\[(?P<instrument_details>[^\]]+)\]", woodwinds_details
            )

            # Handle doublings: e.g. [1.2/pic] or [1.2/Eh]
            if bracket:
                instrument_details = bracket.group("instrument_details")
                instrument_details = instrument_details.split(".")[instrument_number]

                if "/" in instrument_details:
                    _, doubling_code = instrument_details.split("/", 1)
                    doubling_code = doubling_code.strip().lower()
                    doubling_sections = CODE_MAP.get(doubling_code)
                    if doubling_sections:
                        for doubling in doubling_sections:
                            instrument_sections.append(doubling)

            part_slot = PartSlotDTO(
                family=InstrumentFamily.WOODWINDS,
                primary=base_instrument_section,
                number=instrument_number + 1,
                instrument_sections=instrument_sections,
            )
            out.append(part_slot)

    return out


def _parse_brass(segment: str) -> List[PartSlotDTO]:
    """
    Example Brass segment:
        "4 2 3 1" → positionally: 4Hn, 2Tpt, 3Tbn, 1Tba
    """
    out: List[InstrumentSectionEnum] = []
    segment = _normalize_token(segment)
    counts = [int(x) for x in segment.split() if x.isdigit()]
    for instrument_count, instrument_section in zip(counts, BRASS_ORDER):
        for instrument_number in range(instrument_count):
            part_slot = PartSlotDTO(
                family=InstrumentFamily.BRASS,
                primary=instrument_section,
                number=instrument_number + 1,
                instrument_sections=[instrument_section],
            )
            out.append(part_slot)
    return out


def _parse_percussion(segment: str) -> List[PartSlotDTO]:
    """
    Example perc segment:
        "tmp+1" → positionally: 1 Timpani, 1 Percussion
    """
    out: List[InstrumentSectionEnum] = []
    segment = _normalize_token(segment)
    if not segment:
        return

    m = re.match(r"(?P<code>[a-zA-Z]+)(?:\+(?P<percussion_count>\d+))?", segment)
    if not m:
        return

    code = m.group("code").lower()
    percussion_count = int(m.group("percussion_count") or 0)

    if code == "tmp":
        part_slot = PartSlotDTO(
            family=InstrumentFamily.PERCUSSION,
            primary=InstrumentSectionEnum.TIMPANI,
            number=1,
            instrument_sections=[InstrumentSectionEnum.TIMPANI],
        )
        out.append(part_slot)
        if percussion_count > 0:
            for percussion_number in range(percussion_count):
                part_slot = PartSlotDTO(
                    family=InstrumentFamily.PERCUSSION,
                    primary=InstrumentSectionEnum.PERCUSSION,
                    number=percussion_number + 1,
                    instrument_sections=[InstrumentSectionEnum.PERCUSSION],
                )
                out.append(part_slot)
    else:
        # TODO: Figure this out
        pass

    return out


def _normalize_token(seg: str) -> str:
    seg = re.sub(r"\bopt\b", "", seg)  # remove standalone "opt"
    seg = re.sub(r"\s+", " ", seg).strip().lower()
    return seg


def _normalize_woowinds_token(seg: str) -> list[str]:
    return seg.strip().lower().split()


def _is_no_strings(code: str) -> bool:
    return code in {"[no str]", "no str", "[nostr]", "nostr"}


def _is_percussion_segment(seg: str) -> bool:
    seg = seg.strip().lower()
    return seg.startswith("tmp")  # extend later if you add other perc codes
