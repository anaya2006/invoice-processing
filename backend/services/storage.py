from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Tuple

from fastapi import UploadFile

# Directory to store uploaded files – placed at project root 'uploads'
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def save_upload_file(file: UploadFile) -> Tuple[str, str]:
    """Save an uploaded file to disk and return its absolute path and SHA‑256 hash.

    Args:
        file: FastAPI ``UploadFile`` instance.
    Returns:
        Tuple containing the absolute file path (as a string) and the hex digest of the
        file's SHA‑256 hash.
    """
    # Determine a safe file path – use the original filename prefixed with a UUID to avoid collisions.
    import uuid

    suffix = Path(file.filename).suffix
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    dest_path = UPLOAD_DIR / unique_name

    # Compute hash while writing to avoid reading file twice.
    sha256 = hashlib.sha256()
    async with file.file as source, open(dest_path, "wb") as dest:
        while True:
            chunk = await source.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
            dest.write(chunk)

    return str(dest_path), sha256.hexdigest()
