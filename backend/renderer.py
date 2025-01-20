import datetime
import decimal
from collections.abc import Generator, Mapping

from django.db import models
from django.db.models.fields.files import FieldFile
from filebrowser.base import FileObject
from loguru import logger
from ninja.renderers import JSONRenderer
from ninja.responses import NinjaJSONEncoder

from backend.settings import USE_TZ


class CustomJsonEncoder(NinjaJSONEncoder):
    def default(self, o):
        if isinstance(o, FieldFile):
            return o.url
        if isinstance(o, FileObject):
            return o.url
        if isinstance(o, models.Model):
            return str(o)
        if isinstance(o, decimal.Decimal):
            return f"{o:f}"
        if not USE_TZ and isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, dict):
            return o
        if isinstance(o, Mapping):
            return dict(o)
        if isinstance(o, str):
            return o
        if isinstance(o, Generator):
            return list(o)
        try:
            return super().default(o)
        except TypeError:
            logger.error(f"Object of type {o.__class__.__name__} {repr(o)} is not JSON serializable")
            return repr(o)


class CustomJSONRenderer(JSONRenderer):
    encoder_class = CustomJsonEncoder
