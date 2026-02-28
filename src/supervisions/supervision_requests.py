import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class SupervisionRequest:
    id: int
    student_username: str
    student_name: str
    professor_name: str
    slot: str
    status: str


class SupervisionRequestStore:
    def __init__(self, file_path: Path | None = None) -> None:
        self._file_path = file_path or self.default_file_path()

    @staticmethod
    def default_file_path() -> Path:
        project_root = Path(__file__).resolve().parents[2]
        return project_root / "data" / "supervision_requests.json"

    def all(self) -> list[SupervisionRequest]:
        data = self._read_raw()
        return [SupervisionRequest(**item) for item in data]

    def create_pending(
        self,
        student_username: str,
        student_name: str,
        professor_name: str,
        slot: str,
    ) -> SupervisionRequest:
        requests = self.all()
        next_id = max((request.id for request in requests), default=0) + 1

        for request in requests:
            if (
                request.student_username == student_username
                and request.slot == slot
                and request.status == "pending"
            ):
                requests.remove(request)
                break

        created = SupervisionRequest(
            id=next_id,
            student_username=student_username,
            student_name=student_name,
            professor_name=professor_name,
            slot=slot,
            status="pending",
        )
        requests.append(created)
        self._write_requests(requests)
        return created

    def pending_for_professor(self, professor_name: str) -> list[SupervisionRequest]:
        return [
            request
            for request in self.all()
            if request.professor_name == professor_name and request.status == "pending"
        ]

    def pending_for_student(self, student_username: str) -> list[SupervisionRequest]:
        return [
            request
            for request in self.all()
            if request.student_username == student_username and request.status == "pending"
        ]

    def decide(self, request_id: int, professor_name: str, decision: str) -> SupervisionRequest | None:
        requests = self.all()
        for index, request in enumerate(requests):
            if request.id != request_id:
                continue
            if request.professor_name != professor_name or request.status != "pending":
                return None
            decided = SupervisionRequest(
                id=request.id,
                student_username=request.student_username,
                student_name=request.student_name,
                professor_name=request.professor_name,
                slot=request.slot,
                status=decision,
            )
            requests[index] = decided
            self._write_requests(requests)
            return decided
        return None

    def _read_raw(self) -> list[dict[str, object]]:
        if not self._file_path.exists():
            return []
        with self._file_path.open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)

    def _write_requests(self, requests: list[SupervisionRequest]) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(request) for request in requests]
        with self._file_path.open("w", encoding="utf-8") as file_handle:
            json.dump(data, file_handle, indent=2, sort_keys=True)
