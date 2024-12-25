import functools
from collections.abc import Iterable

from django.core import checks
from tinymce.models import HTMLField

from backend.settings import BASE_URL, MEDIA_URL, MEDIA_URL_PATH


@functools.cache
def replace_image_src(html_content: str, from_prefix: str, to_prefix: str):
    from bs4 import BeautifulSoup, Tag  # type: ignore

    soup = BeautifulSoup(html_content, "html.parser")

    images: Iterable[Tag] = soup.find_all("img")

    for img in images:
        src = img.get("src")
        if not isinstance(src, str):
            continue

        if src.startswith(from_prefix):
            new_src = to_prefix + src[len(from_prefix) :]
            img["src"] = new_src

    return str(soup)


class MediaHtmlMixin:
    """
    Mixin to save relative media url to database and read as absolute url.
    """

    def check(self, **kwargs):
        return [
            *super().check(**kwargs),  # type: ignore
            *self._check_bs4_library_installed(),
        ]

    def _check_bs4_library_installed(self):
        try:
            from bs4 import BeautifulSoup, Tag  # type: ignore
        except ImportError:
            return [
                checks.Error(
                    "Cannot use MediaHtmlField because beautifulsoup4 is not installed.",
                    obj=self,
                )
            ]
        return []

    def _check_base_url(self):
        if not BASE_URL:
            return [
                checks.Error(
                    "Cannot use MediaHtmlField because BASE_URL is not set.",
                    obj=self,
                )
            ]
        return []

    def get_prep_value(self, value):
        if value:
            return replace_image_src(value, MEDIA_URL, MEDIA_URL_PATH)
        return value

    def from_db_value(self, value, expression, connection):
        if value:
            return replace_image_src(value, MEDIA_URL_PATH, MEDIA_URL)
        return value

    def to_python(self, value):
        if isinstance(value, str):
            return replace_image_src(value, MEDIA_URL_PATH, MEDIA_URL)
        return value


class MediaHtmlField(MediaHtmlMixin, HTMLField):
    pass
