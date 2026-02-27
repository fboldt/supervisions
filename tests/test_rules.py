from datetime import date
import pytest
from pydantic import ValidationError

from app.schemas import StudentCurrentBase
from app.services import compute_pnp
from app.models import Cohort


def test_defense_date_must_follow_qualification():
    with pytest.raises(ValidationError):
        StudentCurrentBase(
            registration_id="1",
            full_name="A",
            advisor_1_id=1,
            cohort_id=1,
            qualification_date=date(2025, 5, 1),
            defense_date=date(2025, 4, 1),
        )


def test_pnp_calculation():
    cohort = Cohort(code="2024", entrants=10, defenses=5, graduates=3, publications_total=4, dropouts=1, cancellations=1, paused_students=1)
    assert compute_pnp(cohort) == 0.9
