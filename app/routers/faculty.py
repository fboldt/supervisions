from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Faculty, FacultyOrientationPeriod, Role
from ..schemas import FacultyCreate, FacultyOut, OrientationPeriodBase
from ..services import faculty_orientation_summary

router = APIRouter(prefix="/faculty", tags=["faculty"])


@router.get("", response_model=list[FacultyOut])
def list_faculty(skip: int = 0, limit: int = Query(20, le=100), db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    return db.query(Faculty).offset(skip).limit(limit).all()


@router.post("", response_model=FacultyOut)
def create_faculty(payload: FacultyCreate, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    row = Faculty(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/{faculty_id}/periods")
def upsert_period(faculty_id: int, payload: OrientationPeriodBase, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    row = db.query(FacultyOrientationPeriod).filter_by(faculty_id=faculty_id, period=payload.period).first()
    if not db.query(Faculty).filter(Faculty.id == faculty_id).first():
        raise HTTPException(404, "Faculty not found")
    data = payload.model_dump()
    if row:
        for k, v in data.items():
            setattr(row, k, v)
    else:
        row = FacultyOrientationPeriod(faculty_id=faculty_id, **data)
        db.add(row)
    db.commit()
    return {"status": "ok"}


@router.get("/{faculty_id}/summary")
def get_summary(faculty_id: int, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(404, "Faculty not found")
    return faculty_orientation_summary(faculty)
