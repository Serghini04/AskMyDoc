"""
Uploaded-file storage on local disk: uploads/<document_id><ext>.

Files are named by document ID, never by the user's filename, which rules out
path traversal and name clashes.
"""

import hashlib
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from app.config import settings
from app.exceptions import PayloadTooLargeError

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = frozenset({".pdf", ".txt"})
_READ_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True)
class StagedUpload:
    """An upload written to a temporary file, not yet attached to a document."""

    temp_path: Path
    size_bytes: int
    sha256: str


def upload_dir() -> Path:
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def stored_file_path(document_id: UUID, filename: str) -> Path:
    return upload_dir() / f"{document_id}{file_extension(filename)}"


def stage_upload(source: BinaryIO, max_bytes: int) -> StagedUpload:
    """
    Stream `source` to a temp file, hashing as it goes. Raises
    PayloadTooLargeError as soon as the limit is crossed, so an oversized
    upload is never fully read or held in memory.
    """
    digest = hashlib.sha256()
    size = 0
    fd, temp_name = tempfile.mkstemp(dir=upload_dir(), prefix=".staging-")
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := source.read(_READ_CHUNK_BYTES):
                size += len(chunk)
                if size > max_bytes:
                    raise PayloadTooLargeError(
                        f"File exceeds the maximum allowed size of {max_bytes // (1024 * 1024)} MB."
                    )
                digest.update(chunk)
                out.write(chunk)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    return StagedUpload(temp_path=temp_path, size_bytes=size, sha256=digest.hexdigest())


def promote(staged: StagedUpload, document_id: UUID, filename: str) -> Path:
    """Move a staged upload to its permanent, ID-based location."""
    destination = stored_file_path(document_id, filename)
    staged.temp_path.replace(destination)
    return destination


def discard(path: Path) -> None:
    """Best-effort delete: a leftover file is harmless, a crash here is not."""
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("Failed to delete file %s: %s", path, exc)
