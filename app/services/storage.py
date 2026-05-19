from dataclasses import dataclass
from threading import Lock


@dataclass
class StoredResult:
    task: str
    json_data: str
    markdown_data: str
    pdf_bytes: bytes | None


class ResultStore:
    def __init__(self) -> None:
        self._results: dict[str, StoredResult] = {}
        self._lock = Lock()

    def put(self, result_id: str, result: StoredResult) -> None:
        with self._lock:
            self._results[result_id] = result

    def get(self, result_id: str) -> StoredResult | None:
        return self._results.get(result_id)


result_store = ResultStore()
