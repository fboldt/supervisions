# PPCOMP Program Management Web Application

Full-stack FastAPI application for replacing spreadsheet-based PPCOMP management.

## Features
- Role-based authentication (admin/faculty/staff)
- CRUD APIs for faculty, students (current/history), cohorts, publications, events, lattes links
- Dashboard analytics and deadline alerts
- Automated calculations (faculty orientation totals, PNP, publication requirement validation)
- CSV/XLSX import-export endpoints and legacy migration script
- Front-end dashboard page with KPI cards and cohort trend chart

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open `http://localhost:8000`.

Default admin: `admin` / `admin123`

`/auth/token` now accepts JSON body:
```json
{"username": "admin", "password": "admin123"}
```

## API routes
- `/faculty`
- `/students/current`
- `/students/history`
- `/cohorts`
- `/publications`
- `/events`
- `/deadlines`
- `/dashboard/*`

## Legacy import
```bash
python scripts/import_legacy.py /path/to/legacy.xlsx
```
