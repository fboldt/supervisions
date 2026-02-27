from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Publication, Role
from ..schemas import PublicationBase

router = APIRouter(prefix="/publications", tags=["publications"])


@router.get("")
def list_publications(skip: int = 0, limit: int = Query(20, le=100), student_id: int | None = None, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    q = db.query(Publication)
    if student_id:
        q = q.filter(Publication.student_id == student_id)
    return q.offset(skip).limit(limit).all()


@router.post("")
def create_publication(payload: PublicationBase, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    row = Publication(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
