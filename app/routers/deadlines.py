from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Role
from ..services import upcoming_deadlines

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


@router.get("")
def get_deadlines(window_days: int = Query(60, ge=1, le=365), db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.staff, Role.faculty))):
    return upcoming_deadlines(db, window_days)
