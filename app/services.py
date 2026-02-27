from datetime import date, timedelta
from sqlalchemy.orm import Session

from .models import Cohort, Faculty, FacultyOrientationPeriod, Publication, StudentCurrent


def faculty_orientation_summary(faculty: Faculty):
    rows = faculty.orientation_periods
    sum_main = sum(r.main_count for r in rows)
    sum_overall = sum(r.overall_count for r in rows)
    completed_main = sum(r.completed_main for r in rows)
    completed_overall = sum(r.completed_overall for r in rows)
    defenses = sum(r.defenses_until_july_2026 for r in rows)
    total_main_2026_1 = sum(r.total_main_2026_1 for r in rows)
    total_forecast = sum_overall + defenses + total_main_2026_1
    return {
        "faculty_id": faculty.id,
        "name": faculty.name,
        "sum_main": sum_main,
        "sum_overall": sum_overall,
        "completed_main": completed_main,
        "completed_overall": completed_overall,
        "defenses_until_july_2026": defenses,
        "total_main_2026_1": total_main_2026_1,
        "total_forecast": total_forecast,
    }


def compute_pnp(cohort: Cohort) -> float:
    base = cohort.entrants or 1
    score = (cohort.defenses + cohort.graduates + cohort.publications_total) / base
    penalties = (cohort.dropouts + cohort.cancellations + cohort.paused_students) / base
    return round(score - penalties, 3)


def publication_requirement_met(db: Session, student_id: int) -> bool:
    count = db.query(Publication).filter(Publication.student_id == student_id).count()
    return count > 0


def upcoming_deadlines(db: Session, window_days: int = 60):
    today = date.today()
    limit = today + timedelta(days=window_days)
    students = db.query(StudentCurrent).all()
    alerts = []
    for s in students:
        if s.qualification_date and today <= s.qualification_date <= limit:
            alerts.append({"type": "qualification", "student": s.full_name, "date": s.qualification_date.isoformat()})
        if s.defense_date and today <= s.defense_date <= limit:
            alerts.append({"type": "defense", "student": s.full_name, "date": s.defense_date.isoformat()})
    return alerts


def dashboard_overview(db: Session):
    active = db.query(StudentCurrent).count()
    cohorts = db.query(Cohort).all()
    avg_pnp = round(sum(compute_pnp(c) for c in cohorts) / len(cohorts), 3) if cohorts else 0
    publications = db.query(Publication).count()
    return {
        "active_students": active,
        "cohorts": len(cohorts),
        "avg_pnp": avg_pnp,
        "publications": publications,
    }
