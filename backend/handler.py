from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.paginator import InvalidPage
from django.db.utils import DatabaseError
from django.http import HttpRequest, HttpResponse
from loguru import logger
from ninja import NinjaAPI
from ninja.errors import AuthenticationError
from ninja.errors import ValidationError as NinjaValidationError
from pydantic import ValidationError as PydanticValidationError


def set_exception_handlers(api: NinjaAPI):
    @api.exception_handler(AuthenticationError)
    def _(request: HttpRequest, exc: AuthenticationError) -> HttpResponse:
        error_str = str(exc)
        if error_str:
            logger.warning(error_str)
        return api.create_response(
            request,
            {"code": 401, "msg": error_str or "登录失效"},
            status=401,
        )

    @api.exception_handler(NinjaValidationError)
    def _(request: HttpRequest, exc: NinjaValidationError) -> HttpResponse:
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

    @api.exception_handler(DjangoValidationError)
    def _(request: HttpRequest, exc: DjangoValidationError) -> HttpResponse:
        logger.warning(exc)
        return api.create_response(
            request,
            {"code": -1, "msg": exc.message, "data": exc.params},
            status=200,
        )

    @api.exception_handler(PydanticValidationError)
    def _(request: HttpRequest, exc: PydanticValidationError) -> HttpResponse:
        logger.warning(exc)
        data = exc.errors(include_url=False, include_context=False, include_input=False)
        return api.create_response(
            request,
            {"code": -1, "msg": "数据校验错误", "data": data},
            status=200,
        )

    @api.exception_handler(InvalidPage)
    def _(request: HttpRequest, exc: InvalidPage) -> HttpResponse:
        return api.create_response(
            request,
            {"code": 400, "msg": f"{exc}"},
            status=400,
        )

    @api.exception_handler(DatabaseError)
    def _(request: HttpRequest, exc: DatabaseError) -> HttpResponse:
        logger.error(exc)
        return api.create_response(
            request,
            {"code": -1, "msg": "数据库错误"},
            status=200,
        )

    @api.exception_handler(ValueError)
    def _(request: HttpRequest, exc: ValueError) -> HttpResponse:
        logger.info(exc)
        return api.create_response(
            request,
            {"code": -1, "msg": f"{exc}"},
            status=200,
        )

    @api.exception_handler(Exception)
    def _(request: HttpRequest, exc: Exception) -> HttpResponse:
        logger.exception(exc)
        return api.create_response(
            request,
            {"code": 500, "msg": "内部错误"},
            status=500,
        )
