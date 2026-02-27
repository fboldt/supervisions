from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Cohort, Role
from ..schemas import CohortBase
from ..services import compute_pnp

router = APIRouter(prefix="/cohorts", tags=["cohorts"])


@router.get("")
def list_cohorts(skip: int = 0, limit: int = Query(20, le=100), db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    items = db.query(Cohort).offset(skip).limit(limit).all()
    return [{**c.__dict__, "pnp": compute_pnp(c)} for c in items]


@router.post("")
def create_cohort(payload: CohortBase, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    c = Cohort(**payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return {**c.__dict__, "pnp": compute_pnp(c)}
