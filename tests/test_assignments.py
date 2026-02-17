import pytest

from core.enum.instruments import InstrumentEnum
from core.models.music import Instrument, Part, PartInstrument, Piece
from core.models.programs import ProgramPiece
from core.services.assignments import get_assignment_payload
from core.services.organizations import create_musician
from core.services.programs import add_musician_to_program, create_program
from tests.mocks import create_organization

pytestmark = pytest.mark.django_db


def _create_part(piece_id: str, instrument: InstrumentEnum) -> str:
    part = Part.objects.create(piece_id=piece_id)
    instrument_model = Instrument.objects.get(name=instrument.value)
    PartInstrument.objects.create(
        part=part,
        instrument=instrument_model,
        primary=True,
    )
    return str(part.id)


def test_assignment_payload_scopes_to_principal_subsection():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Subsection Program",
        performance_dates=[],
    )

    principal_trombone = create_musician(
        organization_id=str(organization.id),
        first_name="Terry",
        last_name="Trombone",
        email="terry-trombone@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.TROMBONE],
    )
    section_trombone = create_musician(
        organization_id=str(organization.id),
        first_name="Bea",
        last_name="Bassbone",
        email="bea-bassbone@example.com",
        principal=False,
        core_member=True,
        instruments=[InstrumentEnum.BASS_TROMBONE],
    )
    trumpet = create_musician(
        organization_id=str(organization.id),
        first_name="Trent",
        last_name="Trumpet",
        email="trent-trumpet@example.com",
        principal=False,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )

    for musician in [principal_trombone, section_trombone, trumpet]:
        add_musician_to_program(
            organization_id=str(organization.id),
            program_id=str(program.id),
            musician_id=str(musician.id),
        )

    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Scoped Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)

    trombone_part_id = _create_part(str(piece.id), InstrumentEnum.TROMBONE)
    _create_part(str(piece.id), InstrumentEnum.TRUMPET)

    payload = get_assignment_payload(
        program_id=str(program.id),
        principal_musician_id=str(principal_trombone.id),
    )

    part_ids = {part.id for p in payload.pieces for part in p.parts}
    eligible_musician_ids = {m.id for m in payload.eligible_musicians}

    assert part_ids == {trombone_part_id}
    assert eligible_musician_ids == {
        str(principal_trombone.id),
        str(section_trombone.id),
    }
    assert str(trumpet.id) not in eligible_musician_ids


def test_assignment_payload_includes_piccolo_for_flute_principal():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Flute Program",
        performance_dates=[],
    )

    flute_principal = create_musician(
        organization_id=str(organization.id),
        first_name="Flo",
        last_name="Flute",
        email="flo-flute@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.FLUTE],
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(flute_principal.id),
    )

    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Woodwind Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)

    flute_part_id = _create_part(str(piece.id), InstrumentEnum.FLUTE)
    piccolo_part_id = _create_part(str(piece.id), InstrumentEnum.PICCOLO)

    payload = get_assignment_payload(
        program_id=str(program.id),
        principal_musician_id=str(flute_principal.id),
    )

    part_ids = {part.id for p in payload.pieces for part in p.parts}
    assert part_ids == {flute_part_id, piccolo_part_id}


def test_assignment_payload_includes_timpani_for_percussion_principal():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Percussion Program",
        performance_dates=[],
    )

    percussion_principal = create_musician(
        organization_id=str(organization.id),
        first_name="Percy",
        last_name="Principal",
        email="percussion-principal@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.PERCUSSION],
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(percussion_principal.id),
    )

    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Perc Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)

    _create_part(str(piece.id), InstrumentEnum.TIMPANI)

    payload = get_assignment_payload(
        program_id=str(program.id),
        principal_musician_id=str(percussion_principal.id),
    )

    part_names = {part.display_name for p in payload.pieces for part in p.parts}
    assert any("Timpani" in part_name for part_name in part_names)
