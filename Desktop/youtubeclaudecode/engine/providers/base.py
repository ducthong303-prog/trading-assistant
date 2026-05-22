"""YouTube AI Factory v4.1 — Provider Base Class"""
import time
from engine.utils.logger import Logger


class AbstractProvider:
    def __init__(self, name: str, logger: Logger = None):
        self.name = name
        self.log = logger or Logger()

    def retry_with_backoff(self, fn, max_retries: int = 3,
                           backoff_seconds: list = None, label: str = ""):
        """Execute fn() with exponential retry. Returns (result, None) or (None, error)."""
        backoff = backoff_seconds or [2, 4, 8]
        last_error = None
        for attempt in range(max_retries):
            try:
                result = fn()
                return result, None
            except Exception as e:
                last_error = str(e)
                self.log.warn(f"{self.name}: {label} attempt {attempt+1}/{max_retries} failed: {last_error}")
                if attempt < max_retries - 1:
                    wait = backoff[min(attempt, len(backoff)-1)]
                    time.sleep(wait)
        self.log.error(f"{self.name}: {label} all retries exhausted: {last_error}")
        return None, last_error
