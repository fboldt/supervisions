import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from supervisions.main import execute_user_creation, get_message
from supervisions.auth import authenticate
from supervisions.user_control import User, UserRegistry, can, list_permissions, parse_role, require_permission
from supervisions.user_store import UserStore


class SmokeTest(unittest.TestCase):
    def test_default_message_uses_regular_role(self) -> None:
        message = get_message()
        self.assertIn("role=regular", message)
        self.assertIn("category=-", message)
        self.assertIn("profile:view", message)

    def test_admin_has_management_permissions(self) -> None:
        user = User(username="alice", role=parse_role("admin"))
        self.assertTrue(can(user, "users:create"))
        self.assertTrue(can(user, "users:delete"))
        self.assertIn("reports:view", list_permissions(user))

    def test_regular_cannot_create_users(self) -> None:
        user = User(username="bob", role=parse_role("regular"))
        self.assertFalse(can(user, "users:create"))
        with self.assertRaises(PermissionError):
            require_permission(user, "users:create")

    def test_invalid_role_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_role("manager")

    def test_admin_can_create_user_in_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = UserStore(file_path=Path(temp_dir) / "users.json")
            registry = UserRegistry(store=store)
            actor = User(username="alice", role=parse_role("admin"))
            created = registry.create_user(actor=actor, username="charlie", role="regular")
            self.assertEqual(created.username, "charlie")
            self.assertEqual(created.role.value, "regular")
            self.assertEqual(created.category.value, "student")
            self.assertEqual(len(registry.list_users()), 1)

    def test_regular_cannot_create_user_in_registry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = UserStore(file_path=Path(temp_dir) / "users.json")
            registry = UserRegistry(store=store)
            actor = User(username="bob", role=parse_role("regular"))
            with self.assertRaises(PermissionError):
                registry.create_user(actor=actor, username="charlie", role="regular")

    def test_execute_user_creation_returns_expected_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            users_file = Path(temp_dir) / "users.json"
            with patch("supervisions.user_store.UserStore.default_file_path", return_value=users_file):
                summary = execute_user_creation(
                    actor_role="admin",
                    actor_username="alice",
                    new_username="charlie",
                    new_role="regular",
                    new_password="charlie-pass",
                )
                self.assertIn("created=charlie:regular", summary)
                self.assertIn(":student", summary)
                self.assertIn("password=charlie-pass", summary)
                self.assertIn("users=[charlie:regular:student]", summary)

    def test_users_persist_across_registry_instances(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            users_file = Path(temp_dir) / "users.json"
            store = UserStore(file_path=users_file)
            actor = User(username="alice", role=parse_role("admin"))

            first_registry = UserRegistry(store=store)
            first_registry.create_user(
                actor=actor,
                username="diana",
                role="regular",
                password="diana-pass",
                category="professor",
            )

            second_registry = UserRegistry(store=UserStore(file_path=users_file))
            users = second_registry.list_users()
            self.assertEqual([user.username for user in users], ["diana"])
            self.assertIsNotNone(users[0].category)
            self.assertEqual(users[0].category.value, "professor")

    def test_authenticate_persisted_user(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            users_file = Path(temp_dir) / "users.json"
            store = UserStore(file_path=users_file)
            registry = UserRegistry(store=store)
            actor = User(username="alice", role=parse_role("admin"))
            registry.create_user(
                actor=actor,
                username="eve",
                role="regular",
                password="eve-pass",
                category="student",
            )

            with patch("supervisions.user_store.UserStore.default_file_path", return_value=users_file):
                authenticated = authenticate("eve", "eve-pass")
                self.assertIsNotNone(authenticated)
                assert authenticated is not None
                self.assertEqual(authenticated.username, "eve")
                self.assertEqual(authenticated.role.value, "regular")
                self.assertIsNotNone(authenticated.category)
                self.assertEqual(authenticated.category.value, "student")


if __name__ == "__main__":
    unittest.main()
