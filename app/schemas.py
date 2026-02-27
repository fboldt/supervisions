from datetime import date
from pydantic import BaseModel, Field, field_validator
from .models import OutcomeStatus, PersonType, Role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str
    password: str
    role: Role


class UserOut(BaseModel):
    id: int
    username: str
    role: Role

    class Config:
        from_attributes = True


class FacultyBase(BaseModel):
    name: str
    lattes_url: str | None = None


class FacultyCreate(FacultyBase):
    pass


class FacultyOut(FacultyBase):
    id: int

    class Config:
        from_attributes = True


class OrientationPeriodBase(BaseModel):
    period: str
    main_count: int = 0
    overall_count: int = 0
    completed_main: int = 0
    completed_overall: int = 0
    defenses_until_july_2026: int = 0
    total_main_2026_1: int = 0


class CohortBase(BaseModel):
    code: str
    active_students: int = 0
    entrants: int = 0
    dropouts: int = 0
    cancellations: int = 0
    defenses: int = 0
    scholarship_holders: int = 0
    paused_students: int = 0
    graduates: int = 0
    publications_total: int = 0
    projection_2025: int = 0
    projection_2026: int = 0
    projection_2027: int = 0
    projection_2028: int = 0


class CohortOut(CohortBase):
    id: int
    pnp: float

    class Config:
        from_attributes = True


class StudentCurrentBase(BaseModel):
    registration_id: str
    full_name: str
    lattes_url: str | None = None
    advisor_1_id: int
    advisor_2_id: int | None = None
    co_advisor: str | None = None
    qualification_date: date | None = None
    defense_date: date | None = None
    scholarship: bool = False
    observations: str | None = None
    cohort_id: int

    @field_validator("defense_date")
    @classmethod
    def validate_defense(cls, v, info):
        qual = info.data.get("qualification_date")
        if v and qual and v < qual:
            raise ValueError("defense_date must not precede qualification_date")
        return v


class StudentCurrentOut(StudentCurrentBase):
    id: int

    class Config:
        from_attributes = True


class StudentHistoryBase(BaseModel):
    name: str
    research_area: str | None = None
    advisor_1: str
    advisor_2: str | None = None
    publication_event_name: str | None = None
    publication_year: int | None = None
    submission_date: date | None = None
    acceptance_date: date | None = None
    status: OutcomeStatus = OutcomeStatus.ok
    detailed_notes: str | None = None


class StudentHistoryOut(StudentHistoryBase):
    id: int

    class Config:
        from_attributes = True


class EventBase(BaseModel):
    name: str
    rating: str | None = None
    year: int | None = None


class EventOut(EventBase):
    id: int

    class Config:
        from_attributes = True


class PublicationBase(BaseModel):
    student_id: int
    event_id: int
    title: str
    year: int
    accepted: bool = False


class PublicationOut(PublicationBase):
    id: int

    class Config:
        from_attributes = True


class LattesBase(BaseModel):
    person_id: int
    person_type: PersonType
    name: str
    lattes_url: str


class LattesOut(LattesBase):
    id: int

    class Config:
        from_attributes = True


class OrientationSummary(BaseModel):
    faculty_id: int
    name: str
    sum_main: int
    sum_overall: int
    completed_main: int
    completed_overall: int
    defenses_until_july_2026: int
    total_main_2026_1: int
    total_forecast: int
