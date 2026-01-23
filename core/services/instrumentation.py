import re
from typing import List
from core.dtos.music import PartSlotDTO
from core.enum.instruments import InstrumentSectionEnum, InstrumentFamily

CODE_MAP = {
    "pic": [InstrumentSectionEnum.PICCOLO],
    "eh": [InstrumentSectionEnum.ENGLISH_HORN],
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

    # 3) Percussion (e.g., "tmp+1")
    if len(segments) >= 3:
        percussion = _parse_percussion(segments[2])
        # result[InstrumentFamily.PERCUSSION] = percussion
        result.extend(percussion)

    # 4) Everything after that is one-per-token (hp, cel, pf, str, etc.)
    if len(segments) > 3:
        for seg in segments[3:]:
            code = seg.strip().lower()
            if not code:
                continue
            sections = CODE_MAP.get(code)
            family = InstrumentFamily.AUXILIARY
            if code == "str":
                family = InstrumentFamily.STRINGS
            for section in sections:
                part_slot = PartSlotDTO(
                    family=InstrumentFamily.PERCUSSION,
                    primary=section,
                    number=None,
                    instrument_sections=[section],
                )
                # result[family].append(part_slot)
                result.append(part_slot)

    return result


def _parse_woodwinds(segment: str) -> List[PartSlotDTO]:
    """
    Example WW segment:
        "2[1.2/pic] 2[1.2/Eh] 2[1.2] 2[1.2]" → positionally: Fl, Ob, Cl, Bn
    """
    out: List[InstrumentSectionEnum] = []
    tokens = segment.split()
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

            # Grab the instrument details for this instrument number
            bracket = re.search(
                r"\[(?P<instrument_details>[^\]]+)\]", woodwinds_details
            )
            if bracket:
                instrument_details = bracket.group("instrument_details")
                instrument_details = instrument_details.split(".")[instrument_number]

                # Handle doublings: e.g. [1.2/pic] or [1.2/Eh]
                instrument_sections.append(base_instrument_section)
                if "/" in instrument_details:
                    _, doubling_code = instrument_details.split("/", 1)
                    doubling_code = doubling_code.strip().lower()
                    doubling_sections = CODE_MAP.get(doubling_code)
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
    segment = segment.strip()
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
