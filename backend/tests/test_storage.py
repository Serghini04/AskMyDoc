import hashlib
import io
from uuid import uuid4

import pytest

from app.exceptions import PayloadTooLargeError
from app.services import storage


def test_stage_upload_hashes_and_measures(upload_dir):
    data = b"x" * (3 * 1024 * 1024 + 7)  # spans several read chunks
    staged = storage.stage_upload(io.BytesIO(data), max_bytes=10 * 1024 * 1024)

    assert staged.size_bytes == len(data)
    assert staged.sha256 == hashlib.sha256(data).hexdigest()
    assert staged.temp_path.read_bytes() == data


def test_stage_upload_stops_at_limit_and_cleans_up(upload_dir):
    with pytest.raises(PayloadTooLargeError):
        storage.stage_upload(io.BytesIO(b"x" * 2048), max_bytes=1024)
    assert list(upload_dir.iterdir()) == []


def test_promote_uses_document_id_not_user_filename(upload_dir):
    staged = storage.stage_upload(io.BytesIO(b"data"), max_bytes=1024)
    document_id = uuid4()

    path = storage.promote(staged, document_id, "../../etc/Evil.PDF")

    assert path == upload_dir / f"{document_id}.pdf"
    assert path.read_bytes() == b"data"
    assert not staged.temp_path.exists()


def test_discard_is_safe_on_missing_file(upload_dir):
    storage.discard(upload_dir / "never-existed.txt")  # no error
