from django.core.paginator import Paginator
from django.http import HttpRequest
from ninja import Body, Form, Header, Query, Router

from backend.response import Response
from backend.security import auth
from backend.settings import REDIS_PREFIX, get_logger

router = Router(tags=["用户"])

logger = get_logger()
