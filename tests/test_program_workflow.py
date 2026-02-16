import uuid

import pytest

from core.models.programs import Program, ProgramChecklist
from core.models.users import User
from core.services.programs import (
    create_program,
    get_program_checklist,
    update_program_checklist,
)
from tests.mocks import create_organization

pytestmark = pytest.mark.django_db


def _create_user() -> User:
    return User.objects.create_user(
        username=f"workflow-{uuid.uuid4()}",
        password="password123",
    )


def _create_program_with_checklist() -> Program:
    organization = create_organization()
    program_dto = create_program(
        organization_id=str(organization.id),
        name="Workflow Program",
        performance_dates=[],
    )
    return Program.objects.get(id=program_dto.id)


def test_bowings_cannot_be_completed_before_pieces():
    user = _create_user()
    program = _create_program_with_checklist()

    with pytest.raises(ValueError, match="Bowings cannot be completed"):
        update_program_checklist(
            organization_id=str(program.organization_id),
            program_id=str(program.id),
            user_id=str(user.id),
            bowings_completed=True,
        )

    checklist = ProgramChecklist.objects.get(program_id=program.id)
    assert checklist.bowings_completed_on is None


def test_overrides_cannot_be_completed_before_pieces():
    user = _create_user()
    program = _create_program_with_checklist()

    with pytest.raises(ValueError, match="Overrides cannot be completed"):
        update_program_checklist(
            organization_id=str(program.organization_id),
            program_id=str(program.id),
            user_id=str(user.id),
            overrides_completed=True,
        )

    checklist = ProgramChecklist.objects.get(program_id=program.id)
    assert checklist.overrides_completed_on is None


def test_assignments_require_all_prior_workflow_steps():
    user = _create_user()
    program = _create_program_with_checklist()

    update_program_checklist(
        organization_id=str(program.organization_id),
        program_id=str(program.id),
        user_id=str(user.id),
        pieces_completed=True,
        roster_completed=True,
        bowings_completed=True,
    )

    with pytest.raises(ValueError, match="Assignments cannot be completed"):
        update_program_checklist(
            organization_id=str(program.organization_id),
            program_id=str(program.id),
            user_id=str(user.id),
            assignments_completed=True,
        )

    checklist = ProgramChecklist.objects.get(program_id=program.id)
    assert checklist.assignments_completed_on is None


def test_assignments_can_be_completed_after_all_prerequisites():
    user = _create_user()
    program = _create_program_with_checklist()

    update_program_checklist(
        organization_id=str(program.organization_id),
        program_id=str(program.id),
        user_id=str(user.id),
        pieces_completed=True,
        roster_completed=True,
        bowings_completed=True,
        overrides_completed=True,
    )
    result = update_program_checklist(
        organization_id=str(program.organization_id),
        program_id=str(program.id),
        user_id=str(user.id),
        assignments_completed=True,
    )

    assert result.assignments_completed is True


def test_marking_pieces_incomplete_clears_dependent_steps():
    user = _create_user()
    program = _create_program_with_checklist()

    update_program_checklist(
        organization_id=str(program.organization_id),
        program_id=str(program.id),
        user_id=str(user.id),
        pieces_completed=True,
        roster_completed=True,
        bowings_completed=True,
        overrides_completed=True,
        assignments_completed=True,
    )
    update_program_checklist(
        organization_id=str(program.organization_id),
        program_id=str(program.id),
        user_id=str(user.id),
        pieces_completed=False,
    )

    checklist = get_program_checklist(
        organization_id=str(program.organization_id),
        program_id=str(program.id),
    )
    assert checklist.pieces_completed is False
    assert checklist.bowings_completed is False
    assert checklist.overrides_completed is False
    assert checklist.assignments_completed is False


def test_delivery_cannot_be_sent_before_assignments_complete():
    user = _create_user()
    program = _create_program_with_checklist()

    with pytest.raises(ValueError, match="Delivery cannot be sent"):
        update_program_checklist(
            organization_id=str(program.organization_id),
            program_id=str(program.id),
            user_id=str(user.id),
            delivery_sent=True,
        )


def test_delivery_sent_sets_timestamp_and_user_after_assignments_complete():
    user = _create_user()
    program = _create_program_with_checklist()

    update_program_checklist(
        organization_id=str(program.organization_id),
        program_id=str(program.id),
        user_id=str(user.id),
        pieces_completed=True,
        roster_completed=True,
        bowings_completed=True,
        overrides_completed=True,
        assignments_completed=True,
    )

    result = update_program_checklist(
        organization_id=str(program.organization_id),
        program_id=str(program.id),
        user_id=str(user.id),
        delivery_sent=True,
    )

    assert result.delivery_sent is True
    assert result.delivery_sent_by is not None
    assert result.delivery_sent_by.id == str(user.id)
