from supervisions.user_control import Role, User, parse_regular_category, parse_role
from supervisions.user_store import UserStore


def authenticate(username: str, password: str) -> User | None:
    store = UserStore()
    stored = store.get(username)

    if stored is None:
        return None
    if stored.password != password:
        return None

    role = parse_role(stored.role)
    category = None
    if role == Role.REGULAR:
        category = parse_regular_category(stored.category or "student")
    return User(username=stored.username, role=role, category=category)
