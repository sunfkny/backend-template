import hashlib
import os
from contextlib import contextmanager
from urllib.parse import urljoin

from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.http.request import HttpRequest

from backend.settings import MEDIA_URL

absolute_base_url: str | None = None


class HashedFileSystemStorage(FileSystemStorage):
    _absolute_base_url: str | None = None

    def _get_content_name(self, name: str | None, content: File) -> str:
        dir_name, file_name = os.path.split(name or content.name)
        file_hash = self._compute_hash(content)
        _, file_ext = os.path.splitext(file_name)
        file_ext = file_ext.lower()
        return os.path.join(dir_name, file_hash + file_ext)

    def _compute_hash(self, content: File) -> str:
        hasher = hashlib.sha1()

        cursor = content.tell()
        content.seek(0)
        try:
            while chunk := content.read(File.DEFAULT_CHUNK_SIZE):
                hasher.update(chunk)
            return hasher.hexdigest()
        finally:
            content.seek(cursor)

    def save(self, name: str | None, content: File, max_length: int | None = None) -> str:
        name = self._get_content_name(name, content)
        if self.exists(name):
            return name
        return super().save(name, content, max_length)
