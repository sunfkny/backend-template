import hashlib
import os
from typing import IO

from django.core.files import File
from django.core.files.storage import FileSystemStorage


class HashedFileSystemStorage(FileSystemStorage):
    def _get_content_name(self, name: str | None, content: IO) -> str:
        dir_name, file_name = os.path.split(name or content.name or "")
        file_hash = self._compute_hash(content)
        _, file_ext = os.path.splitext(file_name)
        file_ext = file_ext.lower()
        return os.path.join(dir_name, file_hash + file_ext)

    def _compute_hash(self, content: IO) -> str:
        hasher = hashlib.sha1()

        cursor = content.tell()
        content.seek(0)
        try:
            while chunk := content.read(File.DEFAULT_CHUNK_SIZE):
                hasher.update(chunk)
            return hasher.hexdigest()
        finally:
            content.seek(cursor)

    def save(self, name: str | None, content: IO, max_length: int | None = None) -> str:
        name = self._get_content_name(name, content)
        if self.exists(name):
            return name
        return super().save(name, content, max_length)
