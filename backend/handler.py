from django.core.paginator import InvalidPage
from django.db.utils import DatabaseError
from django.http import HttpRequest, HttpResponse
from loguru import logger
from ninja import NinjaAPI
from ninja.errors import AuthenticationError, ValidationError
from requests import RequestException


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
