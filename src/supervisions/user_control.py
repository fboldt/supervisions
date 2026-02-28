from dataclasses import dataclass
from enum import Enum

from supervisions.user_store import StoredUser, UserStore


class Role(str, Enum):
    ADMIN = "admin"
    REGULAR = "regular"


class RegularCategory(str, Enum):
    PROFESSOR = "professor"
    STUDENT = "student"


PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"users:create", "users:delete", "reports:view", "profile:view"},
    Role.REGULAR: {"profile:view"},
}


@dataclass(frozen=True)
class User:
    username: str
    role: Role
    category: RegularCategory | None = None


def parse_role(value: str) -> Role:
    normalized = value.strip().lower()
    try:
        return Role(normalized)
    except ValueError as error:
        allowed = ", ".join(role.value for role in Role)
        raise ValueError(f"Invalid role '{value}'. Allowed roles: {allowed}") from error


def parse_regular_category(value: str) -> RegularCategory:
    normalized = value.strip().lower()
    try:
        return RegularCategory(normalized)
    except ValueError as error:
        allowed = ", ".join(category.value for category in RegularCategory)
        raise ValueError(
            f"Invalid regular category '{value}'. Allowed categories: {allowed}"
        ) from error


def can(user: User, permission: str) -> bool:
    return permission in PERMISSIONS[user.role]


def require_permission(user: User, permission: str) -> None:
    if not can(user, permission):
        raise PermissionError(
            f"User '{user.username}' with role '{user.role.value}' cannot '{permission}'"
        )


def list_permissions(user: User) -> list[str]:
    return sorted(PERMISSIONS[user.role])


class UserRegistry:
    def __init__(self, store: UserStore | None = None) -> None:
        self._store = store or UserStore()

    def create_user(
        self,
        actor: User,
        username: str,
        role: str,
        password: str | None = None,
        category: str | None = None,
    ) -> User:
        require_permission(actor, "users:create")

        user_role = parse_role(role)
        user_category: RegularCategory | None = None
        if user_role == Role.REGULAR:
            selected_category = category or RegularCategory.STUDENT.value
            user_category = parse_regular_category(selected_category)

        user_password = password or f"{username}123"
        created = User(username=username, role=user_role, category=user_category)
        self._store.save(
            StoredUser(
                username=created.username,
                password=user_password,
                role=created.role.value,
                category=created.category.value if created.category else None,
                full_name=None,
                lattes_link=None,
                email=None,
                sipap_number=None,
                enroll_number=None,
                telephone_number=None,
                advisor_1=None,
                advisor_2=None,
            )
        )
        return created

    def list_users(self) -> list[User]:
        users: list[User] = []
        for stored in self._store.all():
            role = parse_role(stored.role)
            category: RegularCategory | None = None
            if role == Role.REGULAR:
                category = parse_regular_category(stored.category or RegularCategory.STUDENT.value)
            users.append(User(username=stored.username, role=role, category=category))
        return users

    def delete_user(self, actor: User, username: str) -> bool:
        require_permission(actor, "users:delete")
        return self._store.delete(username)
