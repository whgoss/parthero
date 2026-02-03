import re
import csv
import logging
from rapidfuzz import fuzz
from django.db import transaction
from core.dtos.music import MusicianDTO, InstrumentDTO
from core.enum.instruments import InstrumentEnum
from core.models.music import MusicianInstrument
from core.models.organizations import Musician, SetupChecklist
from core.services.music import get_instrument
from core.services.organizations import get_organization, musician_exists_by_email

logger = logging.getLogger()


@transaction.atomic
def upload_roster(file, organization_id: str):
    organization = get_organization(organization_id)
    if not organization:
        return []
    musicians = []

    # Read first line to get and normalize headers
    reader = csv.reader(file)
    raw_headers = next(reader)
    clean_headers = [_normalize_header(h) for h in raw_headers]

    # Read file and pull out musicians
    reader = csv.DictReader(file, fieldnames=clean_headers)
    for row in reader:
        musician = None
        email = row.get("email", None)
        if email:
            musician = None
            musician_exists = musician_exists_by_email(email, organization_id)
            if not musician_exists:
                musician = Musician(
                    organization_id=organization_id,
                    first_name=_normalize_text(row.get("firstname")),
                    last_name=_normalize_text(row.get("lastname")),
                    email=_normalize_text(email),
                    principal=True
                    if _normalize_text(row.get("principal")) == "Yes"
                    else False,
                    core_member=True
                    if _normalize_text(row.get("core")) == "Yes"
                    else False,
                    address=row.get("address", None),
                )
                musician.save()

                # Determine primary instrument
                instrument_string = row.get("instrument", None)
                instrument = determine_instrument_section(
                    _strip_non_alphanumeric_re(instrument_string)
                )
                if instrument:
                    musician_instrument = MusicianInstrument(
                        musician_id=musician.id,
                        instrument_id=instrument.id,
                    )
                    musician_instrument.save()

                # Determine secondary instrument
                secondary_instrument_string = row.get("secondaryinstrument", None)
                if secondary_instrument_string:
                    secondary_instrument = determine_instrument_section(
                        secondary_instrument_string
                    )
                    if secondary_instrument:
                        musician_secondary_instrument = MusicianInstrument(
                            musician_id=musician.id,
                            instrument_id=secondary_instrument.id,
                        )
                        musician_secondary_instrument.save()
            else:
                musician = Musician.objects.filter(
                    email=email, organization_id=organization_id
                ).first()

            if musician:
                musicians.append(musician)

    setup_checklist = SetupChecklist.objects.get(organization_id=organization_id)
    if not setup_checklist.completed:
        setup_checklist.roster_uploaded = True
        setup_checklist.save()
    return MusicianDTO.from_models(musicians)


def determine_instrument_section(
    instrument_string: str,
) -> InstrumentDTO | None:
    for instrument in InstrumentEnum:
        score = fuzz.ratio(
            instrument_string.replace(" ", "").casefold(),
            instrument.value.replace(" ", "").casefold(),
        )
        if score > 95.0:
            return get_instrument(instrument)

    return None


def _normalize_text(name: str) -> str:
    if name is None:
        return None
    return name.strip()


def _normalize_header(header: str) -> str:
    header = header.strip().lower()
    header = _strip_non_alphanumeric_re(header)
    return header


def _strip_non_alphanumeric_re(text):
    # The pattern '[^a-zA-Z0-9]' matches any character NOT (^) in the specified ranges.
    # The '\W+' pattern can also be used but includes the underscore character,
    # so '[^a-zA-Z0-9]' gives more precise control for this case.
    return re.sub(r"[^a-zA-Z0-9]", "", text)
