from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Event, Role
from ..schemas import EventBase

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
def list_events(skip: int = 0, limit: int = Query(20, le=100), db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    return db.query(Event).offset(skip).limit(limit).all()


@router.post("")
def create_event(payload: EventBase, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff))):
    row = Event(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
