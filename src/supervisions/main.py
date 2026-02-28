import argparse

from supervisions.user_control import User, UserRegistry, list_permissions, parse_role


def get_message(role: str = "regular", username: str = "demo") -> str:
    user = User(username=username, role=parse_role(role))
    permissions = ", ".join(list_permissions(user))
    category = user.category.value if user.category else "-"
    return (
        f"user={user.username} role={user.role.value} category={category} "
        f"permissions=[{permissions}]"
    )


def execute_user_creation(
    actor_role: str,
    actor_username: str,
    new_username: str,
    new_role: str,
    new_password: str | None = None,
    new_category: str | None = None,
) -> str:
    actor = User(username=actor_username, role=parse_role(actor_role))
    registry = UserRegistry()
    created_password = new_password or f"{new_username}123"
    created = registry.create_user(
        actor=actor,
        username=new_username,
        role=new_role,
        password=created_password,
        category=new_category,
    )
    users = ", ".join(
        f"{user.username}:{user.role.value}:{user.category.value if user.category else '-'}"
        for user in registry.list_users()
    )
    created_category = created.category.value if created.category else "-"
    return (
        f"created={created.username}:{created.role.value}:{created_category} "
        f"password={created_password} users=[{users}]"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Supervisions role demo")
    parser.add_argument(
        "--role",
        default="regular",
        help="User role: admin or regular",
    )
    parser.add_argument(
        "--username",
        default="demo",
        help="User name",
    )
    parser.add_argument(
        "--create-user",
        default="",
        help="Optional username to create (admin only)",
    )
    parser.add_argument(
        "--create-role",
        default="regular",
        help="Role for created user: admin or regular",
    )
    parser.add_argument(
        "--create-password",
        default="",
        help="Optional password for created user (default: <username>123)",
    )
    parser.add_argument(
        "--create-category",
        default="student",
        help="Regular user category: professor or student (used when create-role=regular)",
    )
    args = parser.parse_args()

    if args.create_user:
        try:
            print(
                execute_user_creation(
                    actor_role=args.role,
                    actor_username=args.username,
                    new_username=args.create_user,
                    new_role=args.create_role,
                    new_password=args.create_password or None,
                    new_category=args.create_category,
                )
            )
        except (PermissionError, ValueError) as error:
            print(f"error: {error}")
            raise SystemExit(1) from error
        return

    print(get_message(role=args.role, username=args.username))


if __name__ == "__main__":
    main()
