import logging

from back.models import AdminUser, AdminPermission, Role
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import InvalidPage, Paginator
from django.http import HttpRequest
from ninja import Form, Query, Router

from backend.utils.auth import auth_admin
from backend.utils.response_types import Response
from backend.settings import get_redis_connection, REDIS_PREFIX

router = Router(tags=["用户"])
from loguru import logger
