from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import InvalidPage, Paginator
from django.http import HttpRequest
from ninja import Form, Header, Query, Router

from backend.settings import REDIS_PREFIX, get_logger
from backend.utils.auth import auth_admin
from backend.utils.response_types import Response

router = Router(tags=["用户"])

logger = get_logger()
