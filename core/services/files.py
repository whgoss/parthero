import csv
import logging
from rapidfuzz import fuzz
from django.db import transaction
from core.dtos.music import MusicianDTO, InstrumentDTO
from core.enum.instruments import InstrumentEnum
from core.models.music import MusicianInstrument
from core.models.organizations import Musician
from core.services.music import get_instrument
from core.services.organizations import get_organization, musician_exists_by_email

logger = logging.getLogger()


@transaction.atomic
def upload_roster(file, organization_id: str):
    organization = get_organization(organization_id)
    if not organization:
        return []
    musicians = []
    reader = csv.DictReader(file)
    for row in reader:
        musician = None
        email = row.get("Email", None)
        if email:
            musician = None
            musician_exists = musician_exists_by_email(email, organization_id)
            if not musician_exists:
                musician = Musician(
                    first_name=normalize_text(row.get("First Name")),
                    last_name=normalize_text(row.get("Last Name")),
                    email=normalize_text(email),
                    principal=True if row.get("Principal") else False,
                    core_member=True if row.get("Core") else False,
                    organization_id=organization_id,
                )
                musician.save()

                instrument_section_string = row.get("Instrument", None)
                instrument = determine_instrument_section(instrument_section_string)
                if instrument:
                    musician_instrument = MusicianInstrument(
                        musician_id=musician.id,
                        instrument_id=instrument.id,
                    )
                    musician_instrument.save()
            else:
                musician = Musician.objects.filter(
                    email=email, organization_id=organization_id
                ).first()

            if musician:
                musicians.append(musician)
    return MusicianDTO.from_models(musicians)


def determine_instrument_section(
    instrument_string: str,
) -> InstrumentDTO | None:
    for instrument in InstrumentEnum:
        score = fuzz.ratio(
            instrument_string.strip().casefold(), instrument.value.strip().casefold()
        )
        if score > 95.0:
            return get_instrument(instrument)

    return None


def normalize_text(name: str) -> str:
    return name.strip()
