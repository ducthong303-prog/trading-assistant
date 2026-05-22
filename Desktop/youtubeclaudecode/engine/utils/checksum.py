"""YouTube AI Factory v4.1 — File Checksum & Validation"""
import hashlib
from pathlib import Path
from typing import Union


def sha256(filepath: Union[str, Path]) -> str:
    """Return SHA256 hex digest of file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(filepath: Union[str, Path], expected_hash: str) -> bool:
    """Verify file matches expected SHA256."""
    return sha256(filepath) == expected_hash


def size_kb(filepath: Union[str, Path]) -> float:
    return Path(filepath).stat().st_size / 1024


def exists_and_not_empty(filepath: Union[str, Path]) -> bool:
    p = Path(filepath)
    return p.exists() and p.stat().st_size > 0
