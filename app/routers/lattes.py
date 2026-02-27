from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import LattesLink, Role
from ..schemas import LattesBase

router = APIRouter(prefix="/lattes", tags=["lattes"])


@router.get("")
def list_links(skip: int = 0, limit: int = Query(50, le=200), person_type: str | None = None, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    q = db.query(LattesLink)
    if person_type:
        q = q.filter(LattesLink.person_type == person_type)
    return q.offset(skip).limit(limit).all()


@router.post("")
def create_link(payload: LattesBase, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    row = LattesLink(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
