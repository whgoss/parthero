from datetime import timedelta

import pytest
from django.utils import timezone

from core.enum.instruments import InstrumentEnum
from core.enum.notifications import MagicLinkType
from core.enum.music import PartAssetType
from core.enum.status import UploadStatus
from core.models.music import Instrument, Part, PartAsset, PartInstrument, Piece
from core.models.programs import ProgramChecklist, ProgramPartMusician, ProgramPiece
from core.models.users import User
from core.services.assignments import (
    assign_program_part_by_librarian,
    get_program_assignments_status,
)
from core.services.delivery import (
    get_program_delivery_downloads,
    get_program_delivery_payload,
)
from core.services.magic_links import create_magic_link
from core.services.organizations import create_musician
from core.services.programs import add_musician_to_program, create_program
from core.services.programs import update_program_checklist
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
        primary_instrument=InstrumentEnum.TRUMPET,
        secondary_instruments=[],
    )
    section = create_musician(
        organization_id=str(organization.id),
        first_name="Sec",
        last_name="Tion",
        email="section-status@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.TRUMPET,
        secondary_instruments=[],
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
    assert payload.summary.string_parts_total == 1
    assert payload.summary.string_parts_assigned == 0
    assert payload.summary.all_string_parts_assigned is False

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
        primary_instrument=InstrumentEnum.TRUMPET,
        secondary_instruments=[],
    )
    section = create_musician(
        organization_id=str(organization.id),
        first_name="Sec",
        last_name="Tion",
        email="section-status2@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.TRUMPET,
        secondary_instruments=[],
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
        primary_instrument=InstrumentEnum.TRUMPET,
        secondary_instruments=[],
    )
    section = create_musician(
        organization_id=str(organization.id),
        first_name="Sec",
        last_name="Tion",
        email="section-librarian@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.VIOLIN_1,
        secondary_instruments=[],
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


def test_program_delivery_payload_and_downloads_for_assigned_musician(monkeypatch):
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Delivery Payload Program",
        performance_dates=[],
    )
    musician = create_musician(
        organization_id=str(organization.id),
        first_name="Del",
        last_name="Ivery",
        email="delivery-payload@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.VIOLIN_1,
        secondary_instruments=[],
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(musician.id),
    )
    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Delivery Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    part = Part.objects.create(piece_id=piece.id)
    violin_1 = Instrument.objects.get(name=InstrumentEnum.VIOLIN_1.value)
    PartInstrument.objects.create(part=part, instrument=violin_1, primary=True)
    ProgramPartMusician.objects.create(
        program_id=program.id,
        part_id=part.id,
        musician_id=musician.id,
    )
    asset = PartAsset.objects.create(
        piece_id=piece.id,
        upload_filename="Violin 1.pdf",
        file_key="file-key.pdf",
        asset_type=PartAssetType.CLEAN.value,
        status=UploadStatus.UPLOADED.value,
    )
    asset.parts.add(part)
    bowed_asset = PartAsset.objects.create(
        piece_id=piece.id,
        upload_filename="Very Long and Nasty Bowing Filename.pdf",
        file_key="bowing-key.pdf",
        asset_type=PartAssetType.BOWING.value,
        status=UploadStatus.UPLOADED.value,
    )
    bowed_asset.parts.add(part)

    payload = get_program_delivery_payload(
        program_id=str(program.id),
        musician_id=str(musician.id),
    )
    assert len(payload.pieces) == 1
    assert payload.pieces[0].title == "Delivery Piece"
    payload_filenames = {f.filename for f in payload.pieces[0].files}
    assert payload_filenames == {
        "Delivery Piece - Violin 1 (Bowing).pdf",
        "Delivery Piece - Violin 1.pdf",
    }

    def _create_download_url(
        organization_id: str,
        file_key: str,
        expiration: int,
        download_filename: str | None = None,
    ):
        return f"https://downloads.test/{organization_id}/{file_key}?exp={expiration}"

    monkeypatch.setattr(
        "core.services.delivery.create_download_url",
        _create_download_url,
    )
    downloads = get_program_delivery_downloads(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(musician.id),
        piece_id=str(piece.id),
    )
    assert len(downloads.files) == 2
    assert {file.id for file in downloads.files} == {
        f"{asset.id}:{part.id}",
        f"{bowed_asset.id}:{part.id}",
    }
    assert all(f.url.startswith("https://downloads.test/") for f in downloads.files)


def test_delivery_payload_deduplicates_duplicate_clean_rows_for_same_part():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Delivery Dedup Program",
        performance_dates=[],
    )
    musician = create_musician(
        organization_id=str(organization.id),
        first_name="Doub",
        last_name="Ling",
        email="doubling-delivery@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.FLUTE,
        secondary_instruments=[InstrumentEnum.PICCOLO],
    )
    add_musician_to_program(
        organization_id=str(organization.id),
        program_id=str(program.id),
        musician_id=str(musician.id),
    )
    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Doubling Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    part = Part.objects.create(piece_id=piece.id, number=1)
    flute = Instrument.objects.get(name=InstrumentEnum.FLUTE.value)
    piccolo = Instrument.objects.get(name=InstrumentEnum.PICCOLO.value)
    PartInstrument.objects.create(part=part, instrument=flute, primary=True)
    PartInstrument.objects.create(part=part, instrument=piccolo, primary=False)
    ProgramPartMusician.objects.create(
        program_id=program.id,
        part_id=part.id,
        musician_id=musician.id,
    )
    asset_one = PartAsset.objects.create(
        piece_id=piece.id,
        upload_filename="Flute1_a.pdf",
        file_key="flute-1a.pdf",
        asset_type=PartAssetType.CLEAN.value,
        status=UploadStatus.UPLOADED.value,
    )
    asset_one.parts.add(part)
    asset_two = PartAsset.objects.create(
        piece_id=piece.id,
        upload_filename="Flute1_b.pdf",
        file_key="flute-1b.pdf",
        asset_type=PartAssetType.CLEAN.value,
        status=UploadStatus.UPLOADED.value,
    )
    asset_two.parts.add(part)

    payload = get_program_delivery_payload(
        program_id=str(program.id),
        musician_id=str(musician.id),
    )
    assert len(payload.pieces) == 1
    assert len(payload.pieces[0].files) == 1


def test_roster_complete_auto_assigns_unambiguous_string_harp_and_keyboard_parts():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="Roster Auto Assign Program",
        performance_dates=[],
    )
    user = User.objects.create_user(
        username="auto-assign-checklist-user",
        password="password123",
    )

    violinist = create_musician(
        organization_id=str(organization.id),
        first_name="Vi",
        last_name="Olin",
        email="violin-auto@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.VIOLIN_1,
        secondary_instruments=[],
    )
    harpist = create_musician(
        organization_id=str(organization.id),
        first_name="Ha",
        last_name="Rp",
        email="harp-auto@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.HARP,
        secondary_instruments=[],
    )
    pianist = create_musician(
        organization_id=str(organization.id),
        first_name="Pi",
        last_name="Ano",
        email="piano-auto@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.PIANO,
        secondary_instruments=[],
    )

    for musician in [violinist, harpist, pianist]:
        add_musician_to_program(
            organization_id=str(organization.id),
            program_id=str(program.id),
            musician_id=str(musician.id),
        )

    piece = Piece.objects.create(
        organization_id=organization.id,
        title="Auto Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)

    violin_part = Part.objects.create(piece_id=piece.id, number=1)
    harp_part = Part.objects.create(piece_id=piece.id)
    piano_part = Part.objects.create(piece_id=piece.id)
    violin_1 = Instrument.objects.get(name=InstrumentEnum.VIOLIN_1.value)
    harp = Instrument.objects.get(name=InstrumentEnum.HARP.value)
    piano = Instrument.objects.get(name=InstrumentEnum.PIANO.value)
    PartInstrument.objects.create(part=violin_part, instrument=violin_1, primary=True)
    PartInstrument.objects.create(part=harp_part, instrument=harp, primary=True)
    PartInstrument.objects.create(part=piano_part, instrument=piano, primary=True)

    update_program_checklist(
        organization_id=str(organization.id),
        program_id=str(program.id),
        user_id=str(user.id),
        roster_completed=True,
    )

    assignments = ProgramPartMusician.objects.filter(program_id=program.id)
    assert assignments.count() == 3
    assigned_by_part = {
        str(assignment.part_id): str(assignment.musician_id)
        for assignment in assignments
    }
    assert assigned_by_part[str(violin_part.id)] == str(violinist.id)
    assert assigned_by_part[str(harp_part.id)] == str(harpist.id)
    assert assigned_by_part[str(piano_part.id)] == str(pianist.id)


def test_roster_complete_auto_assigns_multiple_string_players_by_section():
    organization = create_organization()
    program = create_program(
        organization_id=str(organization.id),
        name="String Section Auto Assign Program",
        performance_dates=[],
    )
    user = User.objects.create_user(
        username="auto-assign-strings-user",
        password="password123",
    )

    violinist_a = create_musician(
        organization_id=str(organization.id),
        first_name="Amy",
        last_name="Alpha",
        email="amy-alpha@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.VIOLIN_1,
        secondary_instruments=[],
    )
    violinist_b = create_musician(
        organization_id=str(organization.id),
        first_name="Ben",
        last_name="Beta",
        email="ben-beta@example.com",
        principal=False,
        core_member=True,
        primary_instrument=InstrumentEnum.VIOLIN_1,
        secondary_instruments=[],
    )
    for musician in [violinist_a, violinist_b]:
        add_musician_to_program(
            organization_id=str(organization.id),
            program_id=str(program.id),
            musician_id=str(musician.id),
        )

    piece = Piece.objects.create(
        organization_id=organization.id,
        title="String Piece",
        composer="Composer",
        instrumentation="",
        duration=None,
    )
    ProgramPiece.objects.create(program_id=program.id, piece_id=piece.id)
    violin_part_1 = Part.objects.create(piece_id=piece.id, number=1)
    violin_part_2 = Part.objects.create(piece_id=piece.id, number=2)
    violin_1 = Instrument.objects.get(name=InstrumentEnum.VIOLIN_1.value)
    PartInstrument.objects.create(part=violin_part_1, instrument=violin_1, primary=True)
    PartInstrument.objects.create(part=violin_part_2, instrument=violin_1, primary=True)

    update_program_checklist(
        organization_id=str(organization.id),
        program_id=str(program.id),
        user_id=str(user.id),
        roster_completed=True,
    )

    assignments = ProgramPartMusician.objects.filter(
        program_id=program.id,
        part_id__in=[violin_part_1.id, violin_part_2.id],
    )
    assert assignments.count() == 2
    assigned_musicians = {str(assignment.musician_id) for assignment in assignments}
    assert assigned_musicians == {str(violinist_a.id), str(violinist_b.id)}
