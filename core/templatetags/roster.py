from django import template
from core.enum.instruments import InstrumentSectionEnum, INSTRUMENT_SECTIONS

register = template.Library()


@register.filter
def section_pill_classes(section):
    """
    Given a section object or name, return Tailwind classes for the section pill.
    Usage: {{ musician.section|section_pill_classes }}
    """

    # Basic normalization
    section = section.replace("–", "-").lower()  # fancy dash to normal
    base_classes = (
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
    )

    # Strings
    if section in INSTRUMENT_SECTIONS[
        InstrumentSectionEnum.STRINGS
    ] or section.startswith("violin"):
        return f"{base_classes} bg-blue-100 text-blue-800"

    # Woodwinds
    if section in INSTRUMENT_SECTIONS[InstrumentSectionEnum.WOODWINDS]:
        return f"{base_classes} bg-green-100 text-green-800"

    # Brass
    if section in INSTRUMENT_SECTIONS[InstrumentSectionEnum.BRASS]:
        return f"{base_classes} bg-yellow-100 text-yellow-800"

    # Percussion
    if section in INSTRUMENT_SECTIONS[InstrumentSectionEnum.PERCUSSION]:
        return f"{base_classes} bg-pink-100 text-pink-800"

    # Keyboard / harp
    if section in INSTRUMENT_SECTIONS[InstrumentSectionEnum.KEYBOARD]:
        return f"{base_classes} bg-purple-100 text-purple-800"

    # Choir / vocal
    if section in INSTRUMENT_SECTIONS[InstrumentSectionEnum.VOCAL]:
        return f"{base_classes} bg-red-100 text-red-900"

    # Fallback
    return f"{base_classes} bg-gray-100 text-gray-700"
