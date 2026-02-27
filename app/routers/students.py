from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import OutcomeStatus, Publication, Role, StudentCurrent, StudentHistory
from ..schemas import StudentCurrentBase, StudentHistoryBase
from ..services import publication_requirement_met

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/current")
def list_current(
    skip: int = 0,
    limit: int = Query(20, le=100),
    cohort_id: int | None = None,
    advisor_id: int | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.admin, Role.staff, Role.faculty)),
):
    q = db.query(StudentCurrent)
    if cohort_id:
        q = q.filter(StudentCurrent.cohort_id == cohort_id)
    if advisor_id:
        q = q.filter((StudentCurrent.advisor_1_id == advisor_id) | (StudentCurrent.advisor_2_id == advisor_id))
    return q.offset(skip).limit(limit).all()


@router.post("/current")
def create_current(payload: StudentCurrentBase, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    row = StudentCurrent(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/current/{student_id}")
def update_current(student_id: int, payload: StudentCurrentBase, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    row = db.query(StudentCurrent).filter(StudentCurrent.id == student_id).first()
    if not row:
        raise HTTPException(404, "Student not found")
    if payload.defense_date and not publication_requirement_met(db, student_id):
        raise HTTPException(400, "At least one publication is required before defense")
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.get("/history")
def list_history(
    skip: int = 0,
    limit: int = Query(20, le=100),
    year: int | None = None,
    event: str | None = None,
    advisor: str | None = None,
    status: OutcomeStatus | None = None,
    db: Session = Depends(get_db),
    _=Depends(require_roles(Role.admin, Role.staff, Role.faculty)),
):
    q = db.query(StudentHistory)
    if year:
        q = q.filter(StudentHistory.publication_year == year)
    if event:
        q = q.filter(StudentHistory.publication_event_name.ilike(f"%{event}%"))
    if advisor:
        q = q.filter((StudentHistory.advisor_1.ilike(f"%{advisor}%")) | (StudentHistory.advisor_2.ilike(f"%{advisor}%")))
    if status:
        q = q.filter(StudentHistory.status == status)
    return q.offset(skip).limit(limit).all()


@router.post("/history")
def create_history(payload: StudentHistoryBase, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    row = StudentHistory(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/history/{history_id}")
def update_history(history_id: int, payload: StudentHistoryBase, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    row = db.query(StudentHistory).filter(StudentHistory.id == history_id).first()
    if not row:
        raise HTTPException(404, "Record not found")
    if row.status in {OutcomeStatus.cancelled, OutcomeStatus.abandoned}:
        raise HTTPException(400, "Cancelled or abandoned records are immutable")
    for k, v in payload.model_dump().items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row
