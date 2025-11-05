from __future__ import annotations
import random, time, requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from src.settings import Settings

_s = None
def _settings():
    global _s
    if _s is None:
        _s = Settings()
    return _s

def _headers():
    s = _settings()
    uas = [
        s.user_agent,
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    ]
    return {"User-Agent": random.choice(uas), "Accept": "text/html,application/xhtml+xml"}

@retry(stop=stop_after_attempt(_settings().max_retries),
       wait=wait_exponential_jitter(initial=1, max=10))
def session_get(url: str, timeout: int):
    s = _settings()
    time.sleep(s.request_delay_ms / 1000.0)
    return requests.get(url, headers=_headers(), timeout=timeout)
