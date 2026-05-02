from __future__ import annotations

from collections import OrderedDict, deque
from ipaddress import ip_address, ip_network
from threading import Lock
from time import monotonic
from typing import Deque

from fastapi import HTTPException, Request, status

from config import Config


class InMemoryRateLimiter:
    def __init__(self, max_keys: int = 4096) -> None:
        self._max_keys = max_keys
        self._buckets: OrderedDict[str, Deque[float]] = OrderedDict()
        self._lock = Lock()

    def allow(self, key: str, limit: int, window_seconds: int = 60, now: float | None = None) -> bool:
        current_time = monotonic() if now is None else now
        cutoff = current_time - window_seconds

        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = deque()
                self._buckets[key] = bucket
            else:
                self._buckets.move_to_end(key)

            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                return False

            bucket.append(current_time)
            while len(self._buckets) > self._max_keys:
                self._buckets.popitem(last=False)
            return True

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request, config: Config) -> str:
    direct_ip = request.client.host if request.client else "unknown"
    if not config.trust_proxy_headers or not _is_trusted_proxy(direct_ip, config.trusted_proxy_cidrs):
        return direct_ip

    forwarded_for = request.headers.get("x-forwarded-for", "")
    forwarded_ip = forwarded_for.split(",", 1)[0].strip()
    if not forwarded_ip:
        return direct_ip

    try:
        ip_address(forwarded_ip)
    except ValueError:
        return direct_ip
    return forwarded_ip


def enforce_rate_limit(request: Request, config: Config, *, bucket: str, limit_per_minute: int) -> None:
    client_ip = get_client_ip(request, config)
    key = f"{bucket}:{client_ip}"
    if not rate_limiter.allow(key, limit=limit_per_minute):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before retrying.",
        )


def _is_trusted_proxy(direct_ip: str, trusted_cidrs: list[str]) -> bool:
    try:
        parsed_ip = ip_address(direct_ip)
    except ValueError:
        return False

    return any(parsed_ip in ip_network(cidr, strict=False) for cidr in trusted_cidrs)
