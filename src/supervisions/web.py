from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

from supervisions.auth import authenticate
from supervisions.supervision_requests import SupervisionRequestStore
from supervisions.user_control import User, UserRegistry, parse_role
from supervisions.user_store import StoredUser, UserStore

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

app = Flask(__name__, template_folder=str(_TEMPLATE_DIR))
app.config["SECRET_KEY"] = "supervisions-dev-secret"


def _professor_full_names(store: UserStore) -> list[str]:
    names = {
        stored.full_name.strip()
        for stored in store.all()
        if stored.role == "regular"
        and stored.category == "professor"
        and stored.full_name
        and stored.full_name.strip()
    }
    return sorted(names)


def _dashboard_context(username: str, role: str, category: str) -> dict[str, object]:
    store = UserStore()
    request_store = SupervisionRequestStore()
    profile = store.get(username)
    professor_name = ""
    if profile and profile.full_name:
        professor_name = profile.full_name.strip()
    return {
        "username": username,
        "role": role,
        "category": category,
        "profile": profile,
        "users": UserRegistry(store=store).list_users(),
        "professor_names": _professor_full_names(store),
        "pending_requests": request_store.pending_for_professor(professor_name)
        if role == "regular" and category == "professor" and professor_name
        else [],
        "student_pending_requests": request_store.pending_for_student(username)
        if role == "regular" and category == "student"
        else [],
    }


@app.get("/")
def landing_page():
    store = UserStore()
    users = store.all()

    professor_entries: list[dict[str, object]] = []
    professors_by_name: dict[str, dict[str, object]] = {}

    for stored in users:
        if stored.role != "regular" or stored.category != "professor":
            continue
        professor_name = (stored.full_name or "").strip() or stored.username
        entry = {
            "name": professor_name,
            "username": stored.username,
            "students": [],
        }
        professor_entries.append(entry)
        professors_by_name[professor_name] = entry

    for stored in users:
        if stored.role != "regular" or stored.category != "student":
            continue
        student_name = (stored.full_name or "").strip() or stored.username
        student_entry = {"name": student_name, "username": stored.username}
        advisor_names = [stored.advisor_1, stored.advisor_2]
        for advisor_name in advisor_names:
            if advisor_name and advisor_name in professors_by_name:
                students = professors_by_name[advisor_name]["students"]
                if student_entry not in students:
                    students.append(student_entry)

    for professor in professor_entries:
        professor["students"].sort(key=lambda student: student["name"])

    professor_entries.sort(key=lambda professor: professor["name"])
    return render_template("landing.html", professors=professor_entries)


@app.get("/login")
def login_page():
    if "username" in session and "role" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html", error=None, result=None, username="")


@app.post("/login")
def login_submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = authenticate(username=username, password=password)
    if user is None:
        return (
            render_template(
                "login.html",
                error="Invalid username or password",
                result=None,
                username=username,
            ),
            401,
        )

    session["username"] = user.username
    session["role"] = user.role.value
    session["category"] = user.category.value if user.category else ""
    return redirect(url_for("dashboard"))


@app.get("/dashboard")
def dashboard():
    username = session.get("username")
    role = session.get("role")
    category = session.get("category", "")
    if not username or not role:
        return redirect(url_for("login_page"))

    context = _dashboard_context(username=username, role=role, category=category)
    return render_template(
        "dashboard.html",
        **context,
        error=None,
        result=None,
    )


@app.post("/profile")
def update_profile():
    username = session.get("username")
    role = session.get("role")
    category = session.get("category", "")
    if not username or not role:
        return redirect(url_for("login_page"))

    store = UserStore()
    context = _dashboard_context(username=username, role=role, category=category)
    current_user = context["profile"]
    if current_user is None:
        return redirect(url_for("login_page"))

    if role != "regular" or category not in {"professor", "student"}:
        return (
            render_template(
                "dashboard.html",
                **context,
                error="Only professor or student users can edit their profile",
                result=None,
            ),
            403,
        )

    full_name = request.form.get("full_name", "").strip() or None
    lattes_link = request.form.get("lattes_link", "").strip() or None
    email = request.form.get("email", "").strip() or None
    sipap_number = current_user.sipap_number
    enroll_number = current_user.enroll_number
    telephone_number = current_user.telephone_number
    advisor_1 = current_user.advisor_1
    advisor_2 = current_user.advisor_2

    if category == "professor":
        sipap_number = request.form.get("sipap_number", "").strip() or None

    if category == "student":
        enroll_number = request.form.get("enroll_number", "").strip() or None
        telephone_number = request.form.get("telephone_number", "").strip() or None
        requested_advisor_1 = request.form.get("advisor_1", "").strip() or None
        requested_advisor_2 = request.form.get("advisor_2", "").strip() or None

        request_store = SupervisionRequestStore()
        student_name = full_name or current_user.username
        if requested_advisor_1 and requested_advisor_1 != current_user.advisor_1:
            request_store.create_pending(
                student_username=current_user.username,
                student_name=student_name,
                professor_name=requested_advisor_1,
                slot="advisor_1",
            )
        if requested_advisor_2 and requested_advisor_2 != current_user.advisor_2:
            request_store.create_pending(
                student_username=current_user.username,
                student_name=student_name,
                professor_name=requested_advisor_2,
                slot="advisor_2",
            )

    updated = StoredUser(
        username=current_user.username,
        password=current_user.password,
        role=current_user.role,
        category=current_user.category,
        full_name=full_name,
        lattes_link=lattes_link,
        email=email,
        sipap_number=sipap_number,
        enroll_number=enroll_number,
        telephone_number=telephone_number,
        advisor_1=advisor_1,
        advisor_2=advisor_2,
    )
    store.save(updated)

    refreshed_context = _dashboard_context(username=username, role=role, category=category)

    return render_template(
        "dashboard.html",
        **refreshed_context,
        error=None,
        result=(
            "Profile updated and supervision request(s) submitted"
            if category == "student"
            else "Profile updated"
        ),
    )


@app.post("/supervision-requests/decision")
def decide_supervision_request():
    username = session.get("username")
    role = session.get("role")
    category = session.get("category", "")
    if not username or not role:
        return redirect(url_for("login_page"))

    context = _dashboard_context(username=username, role=role, category=category)
    profile = context["profile"]
    if role != "regular" or category != "professor" or profile is None or not profile.full_name:
        return (
            render_template(
                "dashboard.html",
                **context,
                error="Only professor users can decide supervision requests",
                result=None,
            ),
            403,
        )

    request_id_raw = request.form.get("request_id", "").strip()
    decision = request.form.get("decision", "").strip()
    if decision not in {"accepted", "rejected"}:
        return (
            render_template(
                "dashboard.html",
                **context,
                error="Invalid decision",
                result=None,
            ),
            400,
        )

    try:
        request_id = int(request_id_raw)
    except ValueError:
        return (
            render_template(
                "dashboard.html",
                **context,
                error="Invalid request id",
                result=None,
            ),
            400,
        )

    request_store = SupervisionRequestStore()
    decided = request_store.decide(
        request_id=request_id,
        professor_name=profile.full_name.strip(),
        decision=decision,
    )
    if decided is None:
        refreshed_context = _dashboard_context(username=username, role=role, category=category)
        return (
            render_template(
                "dashboard.html",
                **refreshed_context,
                error="Request not found",
                result=None,
            ),
            404,
        )

    if decision == "accepted":
        user_store = UserStore()
        student = user_store.get(decided.student_username)
        if student is not None:
            advisor_1 = student.advisor_1
            advisor_2 = student.advisor_2
            if decided.slot == "advisor_1":
                advisor_1 = decided.professor_name
            if decided.slot == "advisor_2":
                advisor_2 = decided.professor_name
            user_store.save(
                StoredUser(
                    username=student.username,
                    password=student.password,
                    role=student.role,
                    category=student.category,
                    full_name=student.full_name,
                    lattes_link=student.lattes_link,
                    email=student.email,
                    sipap_number=student.sipap_number,
                    enroll_number=student.enroll_number,
                    telephone_number=student.telephone_number,
                    advisor_1=advisor_1,
                    advisor_2=advisor_2,
                )
            )

    refreshed_context = _dashboard_context(username=username, role=role, category=category)
    return render_template(
        "dashboard.html",
        **refreshed_context,
        error=None,
        result=f"Request {decision}",
    )


@app.post("/admin/users")
def create_user():
    username = session.get("username")
    role = session.get("role")
    if not username or not role:
        return redirect(url_for("login_page"))

    actor = User(username=username, role=parse_role(role))
    new_username = request.form.get("username", "").strip()
    new_role = request.form.get("role", "regular").strip()
    new_category = request.form.get("category", "student").strip()
    new_password = request.form.get("password", "").strip() or None

    if not new_username:
        context = _dashboard_context(
            username=username,
            role=role,
            category=session.get("category", ""),
        )
        return (
            render_template(
                "dashboard.html",
                **context,
                error="Username is required",
                result=None,
            ),
            400,
        )

    registry = UserRegistry()
    try:
        created = registry.create_user(
            actor=actor,
            username=new_username,
            role=new_role,
            password=new_password,
            category=new_category,
        )
    except PermissionError as error:
        context = _dashboard_context(
            username=username,
            role=role,
            category=session.get("category", ""),
        )
        return (
            render_template(
                "dashboard.html",
                **context,
                error=str(error),
                result=None,
            ),
            403,
        )
    except ValueError as error:
        context = _dashboard_context(
            username=username,
            role=role,
            category=session.get("category", ""),
        )
        return (
            render_template(
                "dashboard.html",
                **context,
                error=str(error),
                result=None,
            ),
            400,
        )

    context = _dashboard_context(
        username=username,
        role=role,
        category=session.get("category", ""),
    )
    return render_template(
        "dashboard.html",
        **context,
        error=None,
        result=(
            f"User '{created.username}' created with role '{created.role.value}'"
            + (f" ({created.category.value})" if created.category else "")
        ),
    )


@app.post("/admin/users/delete")
def delete_user():
    username = session.get("username")
    role = session.get("role")
    if not username or not role:
        return redirect(url_for("login_page"))

    actor = User(username=username, role=parse_role(role))
    target_username = request.form.get("username", "").strip()

    if not target_username:
        context = _dashboard_context(
            username=username,
            role=role,
            category=session.get("category", ""),
        )
        return (
            render_template(
                "dashboard.html",
                **context,
                error="Username is required",
                result=None,
            ),
            400,
        )

    registry = UserRegistry()
    try:
        deleted = registry.delete_user(actor=actor, username=target_username)
    except PermissionError as error:
        context = _dashboard_context(
            username=username,
            role=role,
            category=session.get("category", ""),
        )
        return (
            render_template(
                "dashboard.html",
                **context,
                error=str(error),
                result=None,
            ),
            403,
        )

    context = _dashboard_context(
        username=username,
        role=role,
        category=session.get("category", ""),
    )
    if not deleted:
        return (
            render_template(
                "dashboard.html",
                **context,
                error=f"User '{target_username}' not found",
                result=None,
            ),
            404,
        )

    return render_template(
        "dashboard.html",
        **context,
        error=None,
        result=f"User '{target_username}' deleted",
    )


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


def main() -> None:
    app.run(host="127.0.0.1", port=8000, debug=False)


if __name__ == "__main__":
    main()
