from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .database import Base


class Role(str, enum.Enum):
    admin = "admin"
    faculty = "faculty"
    staff = "staff"


class OutcomeStatus(str, enum.Enum):
    ok = "OK"
    cancelled = "cancelled"
    abandoned = "abandoned"
    trancado = "trancado"


class PersonType(str, enum.Enum):
    faculty = "faculty"
    student = "student"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)


class Faculty(Base):
    __tablename__ = "faculty"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    lattes_url: Mapped[str | None] = mapped_column(String(500))

    orientation_periods: Mapped[list["FacultyOrientationPeriod"]] = relationship(back_populates="faculty", cascade="all, delete-orphan")


class FacultyOrientationPeriod(Base):
    __tablename__ = "faculty_orientation_periods"
    __table_args__ = (UniqueConstraint("faculty_id", "period", name="uq_faculty_period"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id"), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    main_count: Mapped[int] = mapped_column(Integer, default=0)
    overall_count: Mapped[int] = mapped_column(Integer, default=0)
    completed_main: Mapped[int] = mapped_column(Integer, default=0)
    completed_overall: Mapped[int] = mapped_column(Integer, default=0)
    defenses_until_july_2026: Mapped[int] = mapped_column(Integer, default=0)
    total_main_2026_1: Mapped[int] = mapped_column(Integer, default=0)

    faculty: Mapped[Faculty] = relationship(back_populates="orientation_periods")


class Cohort(Base):
    __tablename__ = "cohorts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    active_students: Mapped[int] = mapped_column(Integer, default=0)
    entrants: Mapped[int] = mapped_column(Integer, default=0)
    dropouts: Mapped[int] = mapped_column(Integer, default=0)
    cancellations: Mapped[int] = mapped_column(Integer, default=0)
    defenses: Mapped[int] = mapped_column(Integer, default=0)
    scholarship_holders: Mapped[int] = mapped_column(Integer, default=0)
    paused_students: Mapped[int] = mapped_column(Integer, default=0)
    graduates: Mapped[int] = mapped_column(Integer, default=0)
    publications_total: Mapped[int] = mapped_column(Integer, default=0)
    projection_2025: Mapped[int] = mapped_column(Integer, default=0)
    projection_2026: Mapped[int] = mapped_column(Integer, default=0)
    projection_2027: Mapped[int] = mapped_column(Integer, default=0)
    projection_2028: Mapped[int] = mapped_column(Integer, default=0)


class StudentCurrent(Base):
    __tablename__ = "students_current"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registration_id: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(140), nullable=False)
    lattes_url: Mapped[str | None] = mapped_column(String(500))
    advisor_1_id: Mapped[int] = mapped_column(ForeignKey("faculty.id"), nullable=False)
    advisor_2_id: Mapped[int | None] = mapped_column(ForeignKey("faculty.id"))
    co_advisor: Mapped[str | None] = mapped_column(String(140))
    qualification_date: Mapped[date | None] = mapped_column(Date)
    defense_date: Mapped[date | None] = mapped_column(Date)
    scholarship: Mapped[bool] = mapped_column(Boolean, default=False)
    observations: Mapped[str | None] = mapped_column(Text)
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"), nullable=False)


class StudentHistory(Base):
    __tablename__ = "students_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    research_area: Mapped[str | None] = mapped_column(String(120))
    advisor_1: Mapped[str] = mapped_column(String(120), nullable=False)
    advisor_2: Mapped[str | None] = mapped_column(String(120))
    publication_event_name: Mapped[str | None] = mapped_column(String(180))
    publication_year: Mapped[int | None] = mapped_column(Integer)
    submission_date: Mapped[date | None] = mapped_column(Date)
    acceptance_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[OutcomeStatus] = mapped_column(Enum(OutcomeStatus), default=OutcomeStatus.ok)
    detailed_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    rating: Mapped[str | None] = mapped_column(String(20))
    year: Mapped[int | None] = mapped_column(Integer)


class Publication(Base):
    __tablename__ = "publications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students_current.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)


class LattesLink(Base):
    __tablename__ = "lattes_links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(Integer, nullable=False)
    person_type: Mapped[PersonType] = mapped_column(Enum(PersonType), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    lattes_url: Mapped[str] = mapped_column(String(500), nullable=False)
