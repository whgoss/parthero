from datetime import timedelta

import pytest
from django.utils import timezone

from core.enum.instruments import InstrumentEnum
from core.enum.notifications import MagicLinkType
from core.models.music import Instrument, Part, PartInstrument, Piece
from core.models.programs import ProgramChecklist, ProgramPartMusician, ProgramPiece
from core.services.assignments import (
    assign_program_part_by_librarian,
    get_program_assignments_status,
)
from core.services.magic_links import create_magic_link
from core.services.organizations import create_musician
from core.services.programs import add_musician_to_program, create_program
from tests.mocks import create_organization

pytestmark = pytest.mark.django_db


def test_program_assignments_status_includes_part_and_principal_link_status():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Status Program",
        performance_dates=[],
    )

    principal = create_musician(
        organization_id=str(organization.id),
        first_name="Pri",
        last_name="Ncipal",
        email="principal-status@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )
    section = create_musician(
        organization_id=str(organization.id),
        first_name="Sec",
        last_name="Tion",
        email="section-status@example.com",
        principal=False,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )

    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal.id),
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(section.id),
    )

    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Status Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)

    part = Part.objects.create(piece_id=piece.id)
    trumpet = Instrument.objects.get(name=InstrumentEnum.TRUMPET.value)
    PartInstrument.objects.create(part=part, instrument=trumpet, primary=True)
    strings_part = Part.objects.create(piece_id=piece.id)
    violin_1 = Instrument.objects.get(name=InstrumentEnum.VIOLIN_1.value)
    PartInstrument.objects.create(part=strings_part, instrument=violin_1, primary=True)

    ProgramPartMusician.objects.create(
        program_id=program.id,
        part_id=part.id,
        musician_id=section.id,
    )

    ProgramChecklist.objects.filter(program_id=program.id).update(
        assignments_sent_on=timezone.now()
    )

    link = create_magic_link(
        program_id=str(program.id),
        musician_id=str(principal.id),
        link_type=MagicLinkType.ASSIGNMENT,
    )
    link.last_accessed_on = timezone.now() - timedelta(minutes=5)
    link.completed_on = timezone.now()
    link.save(update_fields=["last_accessed_on", "completed_on"])

    payload = get_program_assignments_status(
        organization_id=str(organization.id),
        program_id=str(program.id),
    )

    assert payload.summary.total_parts == 1
    assert payload.summary.assigned_parts == 1
    assert payload.summary.all_assigned is True

    assert len(payload.pieces) == 1
    assert len(payload.pieces[0].parts) == 1
    assert payload.pieces[0].parts[0].status == "Assigned"
    assert payload.pieces[0].parts[0].assigned_musician.id == str(section.id)

    assert len(payload.principals) == 1
    assert payload.principals[0].id == str(principal.id)
    assert payload.principals[0].status == "Completed"


def test_program_assignments_status_marks_completed_when_all_parts_assigned_without_confirm():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Status Program 2",
        performance_dates=[],
    )

    principal = create_musician(
        organization_id=str(organization.id),
        first_name="Pri",
        last_name="Ncipal",
        email="principal-status2@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )
    section = create_musician(
        organization_id=str(organization.id),
        first_name="Sec",
        last_name="Tion",
        email="section-status2@example.com",
        principal=False,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )

    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal.id),
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(section.id),
    )

    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Status Piece 2",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    part = Part.objects.create(piece_id=piece.id)
    trumpet = Instrument.objects.get(name=InstrumentEnum.TRUMPET.value)
    PartInstrument.objects.create(part=part, instrument=trumpet, primary=True)
    ProgramPartMusician.objects.create(
        program_id=program.id,
        part_id=part.id,
        musician_id=section.id,
    )

    ProgramChecklist.objects.filter(program_id=program.id).update(
        assignments_sent_on=timezone.now()
    )

    payload = get_program_assignments_status(
        organization_id=str(organization.id),
        program_id=str(program.id),
    )

    assert len(payload.principals) == 1
    assert payload.principals[0].status == "Completed"
    assert payload.principals[0].link_accessed is True


def test_librarian_can_assign_any_roster_musician_to_part():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Librarian Assignment Program",
        performance_dates=[],
    )

    principal = create_musician(
        organization_id=str(organization.id),
        first_name="Pri",
        last_name="Ncipal",
        email="principal-librarian@example.com",
        principal=True,
        core_member=True,
        instruments=[InstrumentEnum.TRUMPET],
    )
    section = create_musician(
        organization_id=str(organization.id),
        first_name="Sec",
        last_name="Tion",
        email="section-librarian@example.com",
        principal=False,
        core_member=True,
        instruments=[InstrumentEnum.VIOLIN_1],
    )

    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(principal.id),
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(section.id),
    )

    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Librarian Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    part = Part.objects.create(piece_id=piece.id)
    trumpet = Instrument.objects.get(name=InstrumentEnum.TRUMPET.value)
    PartInstrument.objects.create(part=part, instrument=trumpet, primary=True)

    payload = assign_program_part_by_librarian(
        organization_id=str(organization.id),
        program_id=str(program.id),
        part_id=str(part.id),
        musician_id=str(section.id),
    )

    assignment = ProgramPartMusician.objects.filter(
        program_id=program.id,
        part_id=part.id,
    ).first()
    assert assignment is not None
    assert str(assignment.musician_id) == str(section.id)
    assert any(m.id == str(section.id) for m in payload.roster_musicians)
