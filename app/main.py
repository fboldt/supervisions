from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import get_password_hash
from .database import Base, SessionLocal, engine
from .models import Role, User
from .routers import auth, cohorts, dashboard, deadlines, events, faculty, import_export, lattes, publications, students

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PPCOMP Program Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(faculty.router)
app.include_router(students.router)
app.include_router(cohorts.router)
app.include_router(publications.router)
app.include_router(events.router)
app.include_router(lattes.router)
app.include_router(deadlines.router)
app.include_router(dashboard.router)
app.include_router(import_export.router)


@app.on_event("startup")
def ensure_default_admin():
    db = SessionLocal()
    if not db.query(User).filter(User.username == "admin").first():
        db.add(User(username="admin", hashed_password=get_password_hash("admin123"), role=Role.admin))
        db.commit()
    db.close()


@app.get("/")
def home():
    return FileResponse("app/templates/index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse("app/static/favicon.ico")
