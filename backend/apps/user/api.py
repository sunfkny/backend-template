from django.core.paginator import Paginator
from django.http import HttpRequest
from ninja import Body, Form, Header, Query, Router

from backend.decorator.response import schema_response
from backend.response import D, L, Response
from backend.settings import get_logger

router = Router(tags=["user"])

logger = get_logger()
