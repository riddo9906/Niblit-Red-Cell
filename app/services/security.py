import secrets
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class TierConfig:
    requests_per_minute: int
    monthly_requests: int


TIERS: dict[str, TierConfig] = {
    "free": TierConfig(requests_per_minute=20, monthly_requests=1000),
    "pro": TierConfig(requests_per_minute=120, monthly_requests=25000),
    "enterprise": TierConfig(requests_per_minute=600, monthly_requests=250000),
}


class ApiKeyRegistry:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._lock = Lock()

    def register(self, tier: str) -> str:
        if tier not in TIERS:
            raise ValueError("Invalid tier")
        api_key = f"muh_{secrets.token_urlsafe(24)}"
        with self._lock:
            self._store[api_key] = tier
        return api_key

    def get_tier(self, api_key: str) -> str | None:
        return self._store.get(api_key)


registry = ApiKeyRegistry()
