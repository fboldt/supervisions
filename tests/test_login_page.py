import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from supervisions.supervision_requests import SupervisionRequestStore
from supervisions.user_store import StoredUser, UserStore
from supervisions.web import app


class LoginPageTest(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        users_file = Path(self._temp_dir.name) / "users.json"
        requests_file = Path(self._temp_dir.name) / "supervision_requests.json"
        self._users_patch = patch(
            "supervisions.user_store.UserStore.default_file_path",
            return_value=users_file,
        )
        self._requests_patch = patch(
            "supervisions.supervision_requests.SupervisionRequestStore.default_file_path",
            return_value=requests_file,
        )
        self._users_patch.start()
        self._requests_patch.start()
        self.addCleanup(self._users_patch.stop)
        self.addCleanup(self._requests_patch.stop)
        self.addCleanup(self._temp_dir.cleanup)

        store = UserStore(file_path=users_file)
        store.save(StoredUser(username="alice", password="alice123", role="admin", category=None))
        store.save(StoredUser(username="bob", password="bob123", role="regular", category="student"))
        store.save(
            StoredUser(
                username="prof",
                password="prof123",
                role="regular",
                category="professor",
                full_name="",
                lattes_link="",
                email="",
                sipap_number="",
            )
        )

        self.client = app.test_client()

    def test_get_login_page(self) -> None:
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Login", response.data)

    def test_landing_page_shows_professors_with_students(self) -> None:
        self.client.post(
            "/login",
            data={"username": "prof", "password": "prof123"},
            follow_redirects=True,
        )
        self.client.post(
            "/profile",
            data={
                "full_name": "Professor Silva",
                "lattes_link": "https://lattes.cnpq.br/prof",
                "email": "prof.silva@example.com",
                "sipap_number": "SIPAP-2026-001",
            },
            follow_redirects=True,
        )
        self.client.post("/logout", follow_redirects=True)

        self.client.post(
            "/login",
            data={"username": "bob", "password": "bob123"},
            follow_redirects=True,
        )
        self.client.post(
            "/profile",
            data={
                "enroll_number": "2026-001",
                "full_name": "Student Braga",
                "lattes_link": "https://lattes.cnpq.br/student",
                "email": "student@example.com",
                "telephone_number": "+55 11 99999-9999",
                "advisor_1": "Professor Silva",
                "advisor_2": "",
            },
            follow_redirects=True,
        )
        self.client.post("/logout", follow_redirects=True)

        request_store = SupervisionRequestStore()
        pending = request_store.pending_for_professor("Professor Silva")
        self.assertEqual(len(pending), 1)

        self.client.post(
            "/login",
            data={"username": "prof", "password": "prof123"},
            follow_redirects=True,
        )
        self.client.post(
            "/supervision-requests/decision",
            data={"request_id": str(pending[0].id), "decision": "accepted"},
            follow_redirects=True,
        )

        landing = self.client.get("/")
        self.assertEqual(landing.status_code, 200)
        self.assertIn(b"Professors and their students", landing.data)
        self.assertIn(b"Professor Silva", landing.data)
        self.assertIn(b"Student Braga", landing.data)

    def test_dashboard_requires_login(self) -> None:
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_admin_login_success(self) -> None:
        response = self.client.post(
            "/login",
            data={"username": "alice", "password": "alice123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Dashboard", response.data)
        self.assertIn(b"Role:</strong> admin", response.data)

    def test_regular_login_success(self) -> None:
        response = self.client.post(
            "/login",
            data={"username": "bob", "password": "bob123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Role:</strong> regular", response.data)
        self.assertIn(b"Category:</strong> student", response.data)

    def test_login_failure(self) -> None:
        response = self.client.post(
            "/login",
            data={"username": "bob", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn(b"Invalid username or password", response.data)

    def test_logout_clears_session(self) -> None:
        self.client.post(
            "/login",
            data={"username": "alice", "password": "alice123"},
            follow_redirects=True,
        )
        response = self.client.post("/logout", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])
        protected = self.client.get("/dashboard")
        self.assertEqual(protected.status_code, 302)
        self.assertIn("/login", protected.headers["Location"])

    def test_admin_can_create_new_user(self) -> None:
        self.client.post(
            "/login",
            data={"username": "alice", "password": "alice123"},
            follow_redirects=True,
        )
        response = self.client.post(
            "/admin/users",
            data={
                "username": "carol",
                "role": "regular",
                "category": "professor",
                "password": "carol-pass",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"User &#39;carol&#39; created", response.data)
        self.assertIn(b"(professor)", response.data)

        self.client.post("/logout", follow_redirects=True)
        login = self.client.post(
            "/login",
            data={"username": "carol", "password": "carol-pass"},
            follow_redirects=True,
        )
        self.assertEqual(login.status_code, 200)
        self.assertIn(b"Role:</strong> regular", login.data)
        self.assertIn(b"Category:</strong> professor", login.data)

    def test_regular_cannot_create_new_user(self) -> None:
        self.client.post(
            "/login",
            data={"username": "bob", "password": "bob123"},
            follow_redirects=True,
        )
        response = self.client.post(
            "/admin/users",
            data={
                "username": "mallory",
                "role": "regular",
                "category": "student",
                "password": "mallory-pass",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"cannot &#39;users:create&#39;", response.data)

    def test_admin_can_delete_user(self) -> None:
        self.client.post(
            "/login",
            data={"username": "alice", "password": "alice123"},
            follow_redirects=True,
        )
        self.client.post(
            "/admin/users",
            data={"username": "trent", "role": "regular", "password": "trent-pass"},
            follow_redirects=True,
        )

        delete_response = self.client.post(
            "/admin/users/delete",
            data={"username": "trent"},
            follow_redirects=True,
        )
        self.assertEqual(delete_response.status_code, 200)
        self.assertIn(b"User &#39;trent&#39; deleted", delete_response.data)

        self.client.post("/logout", follow_redirects=True)
        login = self.client.post(
            "/login",
            data={"username": "trent", "password": "trent-pass"},
            follow_redirects=True,
        )
        self.assertEqual(login.status_code, 401)
        self.assertIn(b"Invalid username or password", login.data)

    def test_admin_delete_unknown_user_returns_not_found(self) -> None:
        self.client.post(
            "/login",
            data={"username": "alice", "password": "alice123"},
            follow_redirects=True,
        )
        response = self.client.post(
            "/admin/users/delete",
            data={"username": "ghost"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"User &#39;ghost&#39; not found", response.data)

    def test_regular_cannot_delete_user(self) -> None:
        self.client.post(
            "/login",
            data={"username": "bob", "password": "bob123"},
            follow_redirects=True,
        )
        response = self.client.post(
            "/admin/users/delete",
            data={"username": "alice"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"cannot &#39;users:delete&#39;", response.data)

    def test_professor_can_edit_own_profile(self) -> None:
        self.client.post(
            "/login",
            data={"username": "prof", "password": "prof123"},
            follow_redirects=True,
        )

        response = self.client.post(
            "/profile",
            data={
                "full_name": "Professor Silva",
                "lattes_link": "https://lattes.cnpq.br/1234567890",
                "email": "prof.silva@example.com",
                "sipap_number": "SIPAP-2026-001",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Profile updated", response.data)
        self.assertIn(b"Professor Silva", response.data)

        store = UserStore()
        saved = store.get("prof")
        self.assertIsNotNone(saved)
        assert saved is not None
        self.assertEqual(saved.full_name, "Professor Silva")
        self.assertEqual(saved.lattes_link, "https://lattes.cnpq.br/1234567890")
        self.assertEqual(saved.email, "prof.silva@example.com")
        self.assertEqual(saved.sipap_number, "SIPAP-2026-001")

    def test_student_cannot_edit_profile(self) -> None:
        self.client.post(
            "/login",
            data={"username": "bob", "password": "bob123"},
            follow_redirects=True,
        )

        response = self.client.post(
            "/profile",
            data={
                "full_name": "Student Name",
                "lattes_link": "https://lattes.cnpq.br/x",
                "email": "student@example.com",
                "enroll_number": "2026-001",
                "telephone_number": "+55 11 99999-9999",
                "advisor_1": "Professor A",
                "advisor_2": "Professor B",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Profile updated", response.data)

        store = UserStore()
        saved = store.get("bob")
        self.assertIsNotNone(saved)
        assert saved is not None
        self.assertEqual(saved.enroll_number, "2026-001")
        self.assertEqual(saved.full_name, "Student Name")
        self.assertEqual(saved.lattes_link, "https://lattes.cnpq.br/x")
        self.assertEqual(saved.email, "student@example.com")
        self.assertEqual(saved.telephone_number, "+55 11 99999-9999")
        self.assertIsNone(saved.advisor_1)
        self.assertIsNone(saved.advisor_2)

        request_store = SupervisionRequestStore()
        pending = request_store.pending_for_student("bob")
        self.assertEqual(len(pending), 2)
        self.assertEqual({request.professor_name for request in pending}, {"Professor A", "Professor B"})

    def test_student_profile_shows_professor_dropdown_options(self) -> None:
        self.client.post(
            "/login",
            data={"username": "prof", "password": "prof123"},
            follow_redirects=True,
        )
        self.client.post(
            "/profile",
            data={
                "full_name": "Professor Silva",
                "lattes_link": "https://lattes.cnpq.br/prof",
                "email": "prof.silva@example.com",
                "sipap_number": "SIPAP-2026-001",
            },
            follow_redirects=True,
        )
        self.client.post("/logout", follow_redirects=True)

        response = self.client.post(
            "/login",
            data={"username": "bob", "password": "bob123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"student-advisor-1", response.data)
        self.assertIn(b"student-advisor-2", response.data)
        self.assertIn(b"Professor Silva", response.data)

    def test_admin_cannot_edit_profile(self) -> None:
        self.client.post(
            "/login",
            data={"username": "alice", "password": "alice123"},
            follow_redirects=True,
        )

        response = self.client.post(
            "/profile",
            data={
                "full_name": "Admin Name",
                "email": "admin@example.com",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Only professor or student users can edit their profile", response.data)

    def test_professor_can_accept_supervision_request(self) -> None:
        self.client.post(
            "/login",
            data={"username": "prof", "password": "prof123"},
            follow_redirects=True,
        )
        self.client.post(
            "/profile",
            data={
                "full_name": "Professor Silva",
                "lattes_link": "https://lattes.cnpq.br/prof",
                "email": "prof.silva@example.com",
                "sipap_number": "SIPAP-2026-001",
            },
            follow_redirects=True,
        )
        self.client.post("/logout", follow_redirects=True)

        self.client.post(
            "/login",
            data={"username": "bob", "password": "bob123"},
            follow_redirects=True,
        )
        self.client.post(
            "/profile",
            data={
                "enroll_number": "2026-001",
                "full_name": "Student Name",
                "lattes_link": "https://lattes.cnpq.br/student",
                "email": "student@example.com",
                "telephone_number": "+55 11 99999-9999",
                "advisor_1": "Professor Silva",
                "advisor_2": "",
            },
            follow_redirects=True,
        )
        self.client.post("/logout", follow_redirects=True)

        request_store = SupervisionRequestStore()
        pending = request_store.pending_for_professor("Professor Silva")
        self.assertEqual(len(pending), 1)

        self.client.post(
            "/login",
            data={"username": "prof", "password": "prof123"},
            follow_redirects=True,
        )
        response = self.client.post(
            "/supervision-requests/decision",
            data={"request_id": str(pending[0].id), "decision": "accepted"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Request accepted", response.data)

        saved = UserStore().get("bob")
        self.assertIsNotNone(saved)
        assert saved is not None
        self.assertEqual(saved.advisor_1, "Professor Silva")

    def test_professor_can_reject_supervision_request(self) -> None:
        self.client.post(
            "/login",
            data={"username": "prof", "password": "prof123"},
            follow_redirects=True,
        )
        self.client.post(
            "/profile",
            data={
                "full_name": "Professor Silva",
                "lattes_link": "https://lattes.cnpq.br/prof",
                "email": "prof.silva@example.com",
                "sipap_number": "SIPAP-2026-001",
            },
            follow_redirects=True,
        )
        self.client.post("/logout", follow_redirects=True)

        self.client.post(
            "/login",
            data={"username": "bob", "password": "bob123"},
            follow_redirects=True,
        )
        self.client.post(
            "/profile",
            data={
                "enroll_number": "2026-001",
                "full_name": "Student Name",
                "lattes_link": "https://lattes.cnpq.br/student",
                "email": "student@example.com",
                "telephone_number": "+55 11 99999-9999",
                "advisor_1": "Professor Silva",
                "advisor_2": "",
            },
            follow_redirects=True,
        )
        self.client.post("/logout", follow_redirects=True)

        request_store = SupervisionRequestStore()
        pending = request_store.pending_for_professor("Professor Silva")
        self.assertEqual(len(pending), 1)

        self.client.post(
            "/login",
            data={"username": "prof", "password": "prof123"},
            follow_redirects=True,
        )
        response = self.client.post(
            "/supervision-requests/decision",
            data={"request_id": str(pending[0].id), "decision": "rejected"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Request rejected", response.data)

        saved = UserStore().get("bob")
        self.assertIsNotNone(saved)
        assert saved is not None
        self.assertIsNone(saved.advisor_1)


if __name__ == "__main__":
    unittest.main()
