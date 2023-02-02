"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

import datetime
import logging
import traceback
from urllib.parse import urljoin

from django.contrib import admin
from django.db.models.fields.files import FieldFile
from django.urls import path, include
from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.renderers import JSONRenderer
from ninja.responses import NinjaJSONEncoder
from ninja.errors import ValidationError, AuthenticationError
from pydantic import BaseModel
import uuid

logger = logging.getLogger("django")


class CustomJsonEncoder(NinjaJSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, datetime.date):
            return o.strftime("%Y.%m.%d")
        return super().default(o)


class CustomJSONRenderer(JSONRenderer):
    encoder_class = CustomJsonEncoder


api = NinjaAPI(
    title="Open API",
    version="1.0.0",
    renderer=CustomJSONRenderer(),
)
api_back = NinjaAPI(
    title="Open API back",
    version="back 1.0.0",
    renderer=CustomJSONRenderer(),
)


# 自定义 django ninja 登录失效响应
@api.exception_handler(AuthenticationError)
def authentication_exception_handler(request: HttpRequest, exc: AuthenticationError):
    return api.create_response(
        request,
        {"code": 401, "msg": "未登录"},
        status=401,
    )


# 自定义 django ninja 参数错误响应
@api.exception_handler(ValidationError)
def validation_exception_handler(request: HttpRequest, exc: ValidationError):
    logger.warning(exc.errors)
    if request.method == "POST":
        logger.warning(request.body)
    return api.create_response(
        request,
        {"code": 422, "msg": "参数错误", "data": exc.errors},
        status=422,
    )


# 自定义 django ninja 500错误响应
@api.exception_handler(Exception)
def exception_handler(request: HttpRequest, exc: Exception):
    logger.exception(exc)
    return api.create_response(
        request,
        {"code": 500, "msg": "内部错误", "data": str(exc)},
        status=500,
    )


# 自定义 django ninja 登录失效响应
@api_back.exception_handler(AuthenticationError)
def authentication_exception_handler_back(request: HttpRequest, exc: AuthenticationError):
    return api.create_response(
        request,
        {"code": 401, "msg": "未登录"},
        status=401,
    )


# 自定义 django ninja 参数错误响应
@api_back.exception_handler(ValidationError)
def validation_exception_handler_back(request: HttpRequest, exc: ValidationError):
    logger.warning(exc.errors)
    if request.method == "POST":
        logger.warning(request.body)
    return api.create_response(
        request,
        {"code": 422, "msg": "参数错误", "data": exc.errors},
        status=422,
    )


# 自定义 django ninja 500错误响应
@api_back.exception_handler(Exception)
def exception_handler_back(request: HttpRequest, exc: Exception):
    logger.exception(exc)
    return api.create_response(
        request,
        {"code": 500, "msg": "内部错误", "data": str(exc)},
        status=500,
    )


from back.api import router as back_router

api_back.add_router("/", back_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("api/back", api_back.urls),
]
