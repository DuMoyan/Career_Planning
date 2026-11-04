from pathlib import Path
from uuid import uuid4

import pytest

from app.core.files import LocalFileStore


@pytest.mark.asyncio
async def test_local_file_store_uses_random_key_and_deletes_content() -> None:
    base = Path(".test-data") / str(uuid4())
    store = LocalFileStore(base)

    key = await store.save(b"resume-content")

    assert key != "resume-content"
    assert await store.read(key) == b"resume-content"
    await store.delete(key)
    assert not (base / key).exists()
    base.rmdir()
