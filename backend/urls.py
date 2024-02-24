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
import logging
from urllib.parse import urljoin

from django.contrib import admin
from django.core.paginator import InvalidPage
from django.db import models
from django.db.models.fields.files import FieldFile
from django.db.utils import DatabaseError
from django.http import HttpRequest, HttpResponse
from django.urls import include, path
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, ValidationError
from ninja.renderers import JSONRenderer
from ninja.responses import NinjaJSONEncoder
from requests import RequestException

from backend.settings import DEBUG

logger = logging.getLogger("django")


class CustomJsonEncoder(NinjaJSONEncoder):
    def default(self, o):
        if isinstance(o, FieldFile):
            return urljoin(MEDIA_BASE_URL, o.name)
        if isinstance(o, models.Model):
            return str(o)
        if not USE_TZ and isinstance(o, datetime.datetime):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        try:
            return super().default(o)
        except TypeError:
            logger.error((f"Object of type {o.__class__.__name__} {repr(o)} is not JSON serializable"))
            return repr(o)


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
        error_str = str(exc)
        if error_str:
            logger.warning(error_str)
        return api.create_response(
            request,
            {"code": 401, "msg": error_str or "登录失效"},
            status=401,
        )

    @api.exception_handler(ValidationError)
    def validation_error_handler(request: HttpRequest, exc: ValidationError) -> HttpResponse:
        logger.warning(exc.errors)
        if request.method == "POST":
            try:
                logger.warning(request.body)
            except Exception:
                pass
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

    @api.exception_handler(RequestException)
    def request_exception_handler(request: HttpRequest, exc: RequestException) -> HttpResponse:
        logger.warning(exc)
        return api.create_response(
            request,
            {"code": -1, "msg": "第三方接口错误"},
            status=200,
        )

    @api.exception_handler(DatabaseError)
    def database_error_handler(request: HttpRequest, exc: DatabaseError) -> HttpResponse:
        logger.error(exc)
        return api.create_response(
            request,
            {"code": -1, "msg": "数据库错误"},
            status=200,
        )

    @api.exception_handler(ValueError)
    def value_error_handler(request: HttpRequest, exc: ValueError) -> HttpResponse:
        logger.info(exc)
        return api.create_response(
            request,
            {"code": -1, "msg": f"{exc}"},
            status=200,
        )

    @api.exception_handler(Exception)
    def exception_handler(request: HttpRequest, exc: Exception) -> HttpResponse:
        logger.exception(exc)
        return api.create_response(
            request,
            {"code": 500, "msg": "内部错误"},
            status=500,
        )

    return (
        authentication_error_handler,
        validation_error_handler,
        invalid_page_handler,
        request_exception_handler,
        database_error_handler,
        value_error_handler,
        exception_handler,
    )


set_exception_handlers(api)
set_exception_handlers(api_back)

from backend.apps.back.api_back import router as back_back_router
from backend.apps.user.api import router as user_router

api.add_router("/", user_router)
api_back.add_router("/", back_back_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
    path("api/back/", api_back.urls),
]


if DEBUG:
    from backend.settings import DIST_ROOT, MEDIA_BASE_URL, MEDIA_ROOT, MEDIA_URL, STATIC_ROOT, STATIC_URL, USE_TZ
    from django.conf.urls.static import static

    urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
    urlpatterns += static("/", document_root=DIST_ROOT)
