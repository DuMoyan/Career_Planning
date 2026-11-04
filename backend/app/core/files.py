import asyncio
from pathlib import Path
from uuid import uuid4


class LocalFileStore:
    """Docker 持久卷上的随机键文件存储。"""

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path

    async def save(self, content: bytes) -> str:
        key = uuid4().hex
        await asyncio.to_thread(self.base_path.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread((self.base_path / key).write_bytes, content)
        return key

    async def read(self, key: str) -> bytes:
        return await asyncio.to_thread((self.base_path / key).read_bytes)

    async def delete(self, key: str) -> None:
        path = self.base_path / key
        if path.exists():
            await asyncio.to_thread(path.unlink)
