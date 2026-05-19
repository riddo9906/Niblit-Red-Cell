import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

from app.services.security import TIERS

RATE_LIMIT_WINDOW_SECONDS = 60


@dataclass
class UsageState:
    total_requests: int = 0
    recent_requests: deque[float] = field(default_factory=deque)


class UsageTracker:
    def __init__(self) -> None:
        self._store: dict[str, UsageState] = {}
        self._lock = Lock()

    def _state(self, api_key: str) -> UsageState:
        if api_key not in self._store:
            self._store[api_key] = UsageState()
        return self._store[api_key]

    def enforce_and_record(self, api_key: str, tier: str) -> tuple[bool, str]:
        cfg = TIERS[tier]
        now = time.time()
        with self._lock:
            state = self._state(api_key)
            while (
                state.recent_requests
                and now - state.recent_requests[0] > RATE_LIMIT_WINDOW_SECONDS
            ):
                state.recent_requests.popleft()
            if len(state.recent_requests) >= cfg.requests_per_minute:
                return False, "Rate limit exceeded"
            if state.total_requests >= cfg.monthly_requests:
                return False, "Monthly usage limit exceeded"
            state.recent_requests.append(now)
            state.total_requests += 1
            return True, "ok"

    def get_usage(self, api_key: str) -> UsageState:
        with self._lock:
            return self._state(api_key)


usage_tracker = UsageTracker()
