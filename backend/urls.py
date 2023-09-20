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
import datetime
from functools import partial
import logging
from typing import Type, TypeAlias, Union

from django.contrib import admin
from django.core.paginator import InvalidPage
from django.db.models.fields.files import FieldFile
from django.http import HttpRequest, HttpResponse
from django.urls import include, path
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, ValidationError
from ninja.renderers import JSONRenderer
from ninja.responses import NinjaJSONEncoder

logger = logging.getLogger("django")


class CustomJsonEncoder(NinjaJSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, datetime.date):
            return o.strftime("%Y.%m.%d")
        try:
            return super().default(o)
        except TypeError:
            logger.error((f"Object of type {o.__class__.__name__} {repr(o)} is not JSON serializable"))
            return {"type": o.__class__.__name__, "repr": repr(o)}


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


def set_exception_handlers(api: NinjaAPI):
    @api.exception_handler(AuthenticationError)
    def authentication_error_handler(request: HttpRequest, exc: AuthenticationError) -> HttpResponse:
        return api.create_response(
            request,
            {"code": 401, "msg": "登录失效"},
            status=401,
        )

    @api.exception_handler(ValidationError)
    def validation_error_handler(request: HttpRequest, exc: ValidationError) -> HttpResponse:
        logger.warning(exc.errors)
        if request.method == "POST":
            logger.warning(request.body)
        return api.create_response(
            request,
            {"code": 422, "msg": "参数错误", "data": exc.errors},
            status=422,
        )

    @api.exception_handler(InvalidPage)
    def invalid_page_handler(request: HttpRequest, exc: InvalidPage) -> HttpResponse:
        return api.create_response(
            request,
            {"code": 400, "msg": f"页码错误: {exc}"},
            status=400,
        )

    @api.exception_handler(Exception)
    def exception_handler(request: HttpRequest, exc: Exception) -> HttpResponse:
        logger.exception(exc)
        return api.create_response(
            request,
            {"code": 500, "msg": f"内部错误: {exc}"},
            status=500,
        )

    return (
        authentication_error_handler,
        validation_error_handler,
        invalid_page_handler,
        exception_handler,
    )


set_exception_handlers(api)
set_exception_handlers(api_back)

from user.api import router as user_router
from back.api_back import router as back_back_router

api.add_router("/", user_router)
api_back.add_router("/", back_back_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("api/back/", api_back.urls),
]
