# supervisions

Fresh minimal scaffold for a Python project.

Includes a minimal user control feature with two roles:
- `admin`
- `regular`

Regular users have two categories:
- `professor`
- `student`

## Structure

```text
.
├── README.md
├── requirements.txt
├── src/
│   └── supervisions/
│       ├── __init__.py
│       ├── __main__.py
│       └── main.py
└── tests/
    └── test_smoke.py
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
python -m supervisions
python -m supervisions --role admin --username alice
python -m supervisions --role regular --username bob
python -m supervisions --role admin --username alice --create-user charlie --create-role regular
python -m supervisions --role admin --username alice --create-user charlie --create-role regular --create-category professor --create-password charlie-pass
python -m unittest discover -s tests -v
```

Created users are persisted in `data/users.json`.

## Login page

Run the web app:

```bash
make web
```

Public landing page:
- `http://127.0.0.1:8000/` shows all professors and their respective students.

Open http://127.0.0.1:8000/login and use demo credentials:
Create users first (persisted in `data/users.json`), for example:
- `python -m supervisions --role admin --username bootstrap --create-user alice --create-role admin --create-password alice123`
- `python -m supervisions --role admin --username alice --create-user bob --create-role regular --create-password bob123`

Flow:
- successful login redirects to `/dashboard`
- `/dashboard` requires an active session
- admins can create users directly from `/dashboard`
- admins can delete persisted users directly from `/dashboard`
- professor users can edit their own profile fields: Full name, Lattes link, email, SIPAP number
- student users can edit their own profile fields: Enroll number, Full name, Lattes link, email, Telephone number, Advisor 1, Advisor 2 (optional)
- student advisor selections create pending supervision requests
- professors can accept or reject pending supervision requests from their dashboard
- use **Logout** to clear session and return to `/login`

## Make targets

```bash
make install
make run
make web
make test
make clean
make reset
make demo
```
