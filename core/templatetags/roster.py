from django import template

register = template.Library()

# You can tweak these however you like
STRING_FAMILIES = {
    "violin",
    "violin i",
    "violin ii",
    "viola",
    "cello",
    "double bass",
    "bass",
}

WOODWINDS = {
    "flute",
    "piccolo",
    "oboe",
    "english horn",
    "clarinet",
    "bass clarinet",
    "bassoon",
    "contrabassoon",
}

BRASS = {
    "horn",
    "horn in f",
    "trumpet",
    "cornet",
    "trombone",
    "bass trombone",
    "tuba",
}

PERCUSSION = {
    "percussion",
    "timpani",
    "drums",
    "mallets",
}

KEYBOARD_HARP = {
    "piano",
    "celesta",
    "harpsichord",
    "organ",
    "harp",
}

CHOIR = {
    "soprano",
    "alto",
    "tenor",
    "bass (choir)",
    "choir",
    "chorus",
}


@register.filter
def section_pill_classes(section):
    """
    Given a section object or name, return Tailwind classes for the section pill.
    Usage: {{ musician.section|section_pill_classes }}
    """

    # Accept either an object with .name or a plain string
    if hasattr(section, "name"):
        name = (section.name or "").strip().lower()
    else:
        name = (section or "").strip().lower()

    # Basic normalization
    name = name.replace("–", "-")  # fancy dash to normal
    base_classes = (
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
    )

    # Strings
    if name in STRING_FAMILIES or name.startswith("violin"):
        return f"{base_classes} bg-amber-100 text-amber-800"

    # Woodwinds
    if name in WOODWINDS:
        return f"{base_classes} bg-emerald-100 text-emerald-800"

    # Brass
    if name in BRASS:
        return f"{base_classes} bg-rose-100 text-rose-800"

    # Percussion
    if name in PERCUSSION:
        return f"{base_classes} bg-sky-100 text-sky-800"

    # Keyboard / harp
    if name in KEYBOARD_HARP:
        return f"{base_classes} bg-indigo-100 text-indigo-800"

    # Choir / vocal
    if name in CHOIR:
        return f"{base_classes} bg-fuchsia-100 text-fuchsia-800"

    # Fallback
    return f"{base_classes} bg-slate-100 text-slate-700"
