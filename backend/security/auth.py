import time
import uuid
from collections.abc import Callable
from typing import Generic, TypeVar

import jwt
from django.db import models
from django.db.models.base import Model
from django.http.request import HttpRequest
from loguru import logger
from ninja.errors import AuthenticationError
from ninja.security import APIKeyHeader, HttpBearer
from pydantic import BaseModel, Field
from redis import Redis

from backend.settings import REDIS_PREFIX, SECRET_KEY

TUser = TypeVar("TUser", bound=Model)
TToken = TypeVar("TToken", bound=BaseModel)


class JwtModel(BaseModel):
    iat: int
    exp: int
    uid: int | str

    @classmethod
    def new(cls, uid: int | str, expires: int):
        iat = int(time.time())
        exp = iat + expires
        return cls(
            uid=uid,
            iat=iat,
            exp=exp,
        )


class AuthJwt(HttpBearer, Generic[TUser]):
    def __init__(
        self,
        expires: int,
        user_model: type[TUser],
        uid_field: str = "id",
        secret_key: str = SECRET_KEY,
    ):
        """
        user_model: 用户模型
        expires: 缓存token的过期时间(秒)
        secret_key: jwt加密的密钥
        """
        self.user_model = user_model
        self.uid_field = uid_field
        self.expires = expires
        self.secret_key = secret_key
        super().__init__()

    def __call__(self, request: HttpRequest):
        # 返回的值保存在request.auth
        auth = super().__call__(request)
        return auth

    def authenticate(self, request: HttpRequest, token: str):
        uid = self.decode_token(token).uid
        return uid

    def get_login_uid_optional(self, request: HttpRequest) -> int | str | None:
        """可选获取登录用户uid, 未登录返回 None"""
        auth = None
        if hasattr(request, "auth"):
            auth = getattr(request, "auth")
        else:
            auth = self.__call__(request)
        return auth

    def get_login_user_optional(self, request: HttpRequest) -> TUser | None:
        """可选获取登录用户, 未登录返回 None"""
        uid = self.get_login_uid_optional(request)
        if uid is None:
            return None
        user = self.user_model._default_manager.filter(
            **{
                self.uid_field: uid,
            }
        ).first()
        return user

    def get_login_uid(self, request: HttpRequest) -> int | str:
        """获取登录用户uid"""
        uid = self.get_login_uid_optional(request)
        if not uid:
            raise AuthenticationError("Uid not found")
        return uid

    def get_login_user(self, request: HttpRequest) -> TUser:
        """获取登录用户"""
        user = self.get_login_user_optional(request)
        if not user:
            raise AuthenticationError("User not found")
        return user

    def generate_token(self, uid: int | str) -> str:
        """生成token"""
        model = JwtModel.new(uid=uid, expires=self.expires)
        payload = model.model_dump()
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return token

    def decode_token(self, token: str):
        """解析token"""
        try:
            data: dict = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return JwtModel.model_validate(data)
        except Exception as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError("Invalid token")


class BearerTokenModel(BaseModel):
    iat: int = Field(default_factory=lambda: int(time.time()))
    uid: int | str


class AuthBearerToken(HttpBearer, Generic[TUser]):
    def __init__(
        self,
        redis_conn: "Redis[str]",
        expires: int,
        user_model: type[TUser],
        cache_token_prefix: str | None = None,
        secret_key: str = SECRET_KEY,
    ):
        """
        redis_conn: redis连接
        expires: token的过期时间(秒)
        user_model: 用户模型
        cache_token_prefix: 缓存token的前缀
        secret_key: jwt加密的密钥
        after_login_hook: 登录成功后执行的回调函数
        """
        self.user_model = user_model
        if cache_token_prefix is None:
            cache_token_prefix = f"{REDIS_PREFIX}:{user_model.__name__}:token:"
        cache_token_prefix = cache_token_prefix.removesuffix(":")

        self.redis_conn = redis_conn
        self.expires = expires
        self.cache_token_prefix = cache_token_prefix
        self.secret_key = secret_key
        super().__init__()

    def __call__(self, request: HttpRequest):
        # 返回的值保存在request.auth
        auth = super().__call__(request)
        return auth

    def authenticate(self, request: HttpRequest, token: str):
        uid = self.decode_token(token).uid
        if self.token_check(uid, token):
            # 续期
            self.set_token(uid, token)
            return uid
        else:
            return None

    def set_token(self, uid: int | str, token: str):
        """设置token"""
        key = f"{self.cache_token_prefix}:{uid}"
        self.redis_conn.set(name=key, value=token, ex=self.expires)

    def get_token(self, uid: int | str) -> str | None:
        """获取token"""
        key = f"{self.cache_token_prefix}:{uid}"
        token = self.redis_conn.get(key)
        return token

    def token_check(self, uid: int | str, token: str):
        """检查token"""
        return self.get_token(uid) == token

    def get_login_uid_optional(self, request: HttpRequest) -> int | str | None:
        """可选获取登录用户uid, 未登录返回 None"""
        auth = None
        if hasattr(request, "auth"):
            auth = getattr(request, "auth")
        else:
            auth = self.__call__(request)
        return auth

    def get_login_user_optional(self, request: HttpRequest) -> TUser | None:
        """可选获取登录用户, 未登录返回 None"""
        uid = self.get_login_uid_optional(request)
        if uid is None:
            return None
        user = self.user_model._default_manager.filter(pk=uid).first()
        return user

    def get_login_uid(self, request: HttpRequest) -> int | str:
        """获取登录用户uid"""
        uid = self.get_login_uid_optional(request)
        if not uid:
            raise AuthenticationError("Uid not found")
        return uid

    def get_login_user(self, request: HttpRequest) -> TUser:
        """获取登录用户"""
        user = self.get_login_user_optional(request)
        if not user:
            raise AuthenticationError("User not found")
        return user

    def generate_token(self, uid: int | str) -> str:
        """生成token"""
        payload = BearerTokenModel(uid=uid).model_dump()
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        self.set_token(uid, token)
        return token

    def decode_token(self, token: str):
        """解析token"""
        try:
            data: dict = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return BearerTokenModel.model_validate(data)
        except Exception as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError("Invalid token")


class AuthBearerTokenDatabase(APIKeyHeader, Generic[TUser]):
    param_name = "Authorization"

    def __init__(
        self,
        user_model: type[TUser],
        token_field: str = "token",
    ):
        assert isinstance(
            user_model._meta.get_field(token_field),
            models.TextField | models.CharField,
        )
        self.user_model = user_model
        self.token_field = token_field

        super().__init__()

    def __call__(self, request: HttpRequest) -> TUser | None:
        # 返回的值保存在request.auth
        auth = super().__call__(request)
        return auth

    def authenticate(self, request: HttpRequest, token: str | None) -> TUser | None:
        return self.user_model._default_manager.filter(
            **{
                self.token_field: token,
            }
        ).first()

    def get_login_user_optional(self, request: HttpRequest) -> TUser | None:
        """可选获取登录用户, 未登录返回 None"""
        auth: TUser | None = None
        if hasattr(request, "auth"):
            auth = getattr(request, "auth")
        else:
            auth = self.__call__(request)
        return auth

    def get_login_user(self, request: HttpRequest) -> TUser:
        """获取登录用户"""
        user = self.get_login_user_optional(request)
        if user is None:
            raise AuthenticationError("Token not found")
        return user

    def generate_token(self, user: TUser) -> str:
        """生成token"""
        token = uuid.uuid4().hex
        self.user_model._default_manager.filter(pk=user.pk).update(**{self.token_field: token})
        return token

    def get_token(self, pk: int | str) -> str | None:
        """获取token"""
        user = self.user_model._default_manager.filter(pk=pk).only(self.token_field).first()
        return getattr(user, self.token_field)
