"""Local disk storage for uploaded SBOM files."""

import os
import uuid
from pathlib import Path
from app.config import get_settings


class FileStorage:
    """Stores uploaded SBOM files on local disk with random UUIDs to prevent path traversal."""

    def __init__(self):
        settings = get_settings()
        self.base_path = Path(settings.SBOM_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes) -> str:
        """
        Save file content with a random UUID filename.

        Returns:
            The stored filename (UUID-based).
        """
        filename = f"{uuid.uuid4()}.json"
        filepath = self.base_path / filename
        filepath.write_bytes(content)
        return filename

    def read(self, filename: str) -> bytes:
        """Read a stored file by its storage key."""
        filepath = self.base_path / filename
        if not filepath.exists():
            raise FileNotFoundError(f"SBOM file not found: {filename}")
        return filepath.read_bytes()

    def delete(self, filename: str) -> None:
        """Delete a stored file."""
        filepath = self.base_path / filename
        if filepath.exists():
            filepath.unlink()


# Singleton
_storage = None


def get_file_storage() -> FileStorage:
    """Get or create the singleton file storage instance."""
    global _storage
    if _storage is None:
        _storage = FileStorage()
    return _storage
