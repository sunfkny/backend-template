from django.core.paginator import Paginator
from django.http import HttpRequest
from ninja import Form, Header, Query, Body, Router

from backend.settings import REDIS_PREFIX, get_logger
from backend.utils.auth import auth
from backend.utils.response_types import Response

router = Router(tags=["用户"])

logger = get_logger()
