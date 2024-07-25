from django.core.paginator import Paginator
from django.http import HttpRequest
from ninja import Body, Form, Header, Query, Router

from backend.security import auth
from backend.settings import REDIS_PREFIX, get_logger
from backend.utils.response_types import Response

router = Router(tags=["用户"])

logger = get_logger()
