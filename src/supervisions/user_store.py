import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StoredUser:
    username: str
    password: str
    role: str
    category: str | None = None
    full_name: str | None = None
    lattes_link: str | None = None
    email: str | None = None
    sipap_number: str | None = None
    enroll_number: str | None = None
    telephone_number: str | None = None
    advisor_1: str | None = None
    advisor_2: str | None = None


class UserStore:
    def __init__(self, file_path: Path | None = None) -> None:
        self._file_path = file_path or self.default_file_path()

    @staticmethod
    def default_file_path() -> Path:
        project_root = Path(__file__).resolve().parents[2]
        return project_root / "data" / "users.json"

    def get(self, username: str) -> StoredUser | None:
        data = self._read_raw()
        record = data.get(username)
        if record is None:
            return None
        return StoredUser(
            username=username,
            password=record["password"],
            role=record["role"],
            category=record.get("category"),
            full_name=record.get("full_name"),
            lattes_link=record.get("lattes_link"),
            email=record.get("email"),
            sipap_number=record.get("sipap_number"),
            enroll_number=record.get("enroll_number"),
            telephone_number=record.get("telephone_number"),
            advisor_1=record.get("advisor_1"),
            advisor_2=record.get("advisor_2"),
        )

    def save(self, user: StoredUser) -> None:
        data = self._read_raw()
        data[user.username] = {
            "password": user.password,
            "role": user.role,
            "category": user.category,
            "full_name": user.full_name,
            "lattes_link": user.lattes_link,
            "email": user.email,
            "sipap_number": user.sipap_number,
            "enroll_number": user.enroll_number,
            "telephone_number": user.telephone_number,
            "advisor_1": user.advisor_1,
            "advisor_2": user.advisor_2,
        }
        self._write_raw(data)

    def delete(self, username: str) -> bool:
        data = self._read_raw()
        if username not in data:
            return False
        del data[username]
        self._write_raw(data)
        return True

    def all(self) -> list[StoredUser]:
        data = self._read_raw()
        return [
            StoredUser(
                username=username,
                password=record["password"],
                role=record["role"],
                category=record.get("category"),
                full_name=record.get("full_name"),
                lattes_link=record.get("lattes_link"),
                email=record.get("email"),
                sipap_number=record.get("sipap_number"),
                enroll_number=record.get("enroll_number"),
                telephone_number=record.get("telephone_number"),
                advisor_1=record.get("advisor_1"),
                advisor_2=record.get("advisor_2"),
            )
            for username, record in sorted(data.items())
        ]

    def _read_raw(self) -> dict[str, dict[str, str]]:
        if not self._file_path.exists():
            return {}
        with self._file_path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)

    def _write_raw(self, data: dict[str, dict[str, str]]) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        with self._file_path.open("w", encoding="utf-8") as file_handle:
            json.dump(data, file_handle, indent=2, sort_keys=True)
