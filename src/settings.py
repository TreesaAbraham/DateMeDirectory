from __future__ import annotations
import os
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Settings:
    directory_url: str = os.getenv("DIRECTORY_URL", "https://dateme.directory/browse")
    request_delay_ms: int = int(os.getenv("REQUEST_DELAY_MS", "1200"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "4"))
    retry_backoff_factor: float = float(os.getenv("RETRY_BACKOFF_FACTOR", "0.7"))
    timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "20"))
    user_agent: str = os.getenv("USER_AGENT", "DateMeDirectoryBot/1.0")
    snapshot_stamp: str = os.getenv("SNAPSHOT_STAMP", "auto")

    def __post_init__(self):
        if self.snapshot_stamp == "auto":
            object.__setattr__(self, "snapshot_stamp", datetime.now().strftime("%Y%m%d"))
        if not self.directory_url:
            raise SystemExit("DIRECTORY_URL is required. Set it in a .env file.")
