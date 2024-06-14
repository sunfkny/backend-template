import datetime
import decimal
from urllib.parse import urljoin

from django.db import models
from django.db.models.fields.files import FieldFile
from loguru import logger
from ninja.renderers import JSONRenderer
from ninja.responses import NinjaJSONEncoder

from backend.settings import MEDIA_BASE_URL, USE_TZ


class CustomJsonEncoder(NinjaJSONEncoder):
    def default(self, o):
        if isinstance(o, FieldFile):
            return urljoin(MEDIA_BASE_URL, o.name)
        if isinstance(o, models.Model):
            return str(o)
        if isinstance(o, decimal.Decimal):
            return f"{o:f}"
        if not USE_TZ and isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        try:
            return super().default(o)
        except TypeError:
            logger.error(f"Object of type {o.__class__.__name__} {repr(o)} is not JSON serializable")
            return repr(o)


class CustomJSONRenderer(JSONRenderer):
    encoder_class = CustomJsonEncoder
