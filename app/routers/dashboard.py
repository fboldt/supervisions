from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Cohort, Role, StudentHistory
from ..services import compute_pnp, dashboard_overview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview(db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    return dashboard_overview(db)


@router.get("/cohorts")
def cohorts_metrics(db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    cohorts = db.query(Cohort).all()
    return [{"cohort": c.code, "pnp": compute_pnp(c), "graduates": c.graduates, "defenses": c.defenses} for c in cohorts]


@router.get("/status-overview")
def status_overview(db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    rows = db.query(StudentHistory).all()
    counts = {"OK": 0, "cancelled": 0, "abandoned": 0, "trancado": 0}
    for r in rows:
        counts[r.status.value] += 1
    return counts
