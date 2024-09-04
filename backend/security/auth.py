import time
import uuid
from collections.abc import Callable
from typing import Any, Generic, TypeVar

import jwt
from django.db.models.base import Model
from django.http.request import HttpRequest
from loguru import logger
from ninja.errors import AuthenticationError
from ninja.security import APIKeyHeader, HttpBearer
from pydantic import BaseModel, Field
from redis import Redis

from backend.settings import REDIS_PREFIX, SECRET_KEY, get_redis_connection

TUser = TypeVar("TUser", bound=Model)
TToken = TypeVar("TToken", bound=BaseModel)


class JwtModel(BaseModel):
    iat: int = Field(default_factory=lambda: int(time.time()))
    uid: int | str


class AuthBearer(HttpBearer, Generic[TUser]):
    def __init__(
        self,
        user_model: type[TUser],
        uid_field: str = "id",
        cache_token_expires: int = 12 * 60 * 60,
        cache_token_prefix: str | None = None,
        redis_conn: "Redis[str] | None" = None,
        secret_key: str = SECRET_KEY,
        after_login_hook: Callable[[TUser], None] = lambda _: None,
    ):
        """
        user_model: 用户模型
        cache_token_expires: 缓存token的过期时间(秒)
        cache_token_prefix: 缓存token的前缀
        redis_conn: redis连接
        secret_key: jwt加密的密钥
        after_login_hook: 登录成功后执行的回调函数
        """
        self.user_model = user_model
        self.uid_field = uid_field
        if cache_token_prefix is None:
            cache_token_prefix = f"{REDIS_PREFIX}:{user_model.__name__}:token:"
        cache_token_prefix = cache_token_prefix.removesuffix(":")

        self.cache_token_prefix = cache_token_prefix
        self.cache_token_expires = cache_token_expires
        self.secret_key = secret_key
        self.after_login_hook = after_login_hook
        if redis_conn is None:
            redis_conn = get_redis_connection()
        self.redis_conn = redis_conn
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
        self.redis_conn.set(name=key, value=token, ex=self.cache_token_expires)

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
        user = self.user_model.objects.filter(
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
        self.after_login_hook(user)
        return user

    def generate_token(self, uid: int | str) -> str:
        """生成token"""
        payload = JwtModel(uid=uid).model_dump()
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        self.set_token(uid, token)
        return token

    def decode_token(self, token: str):
        """解析token"""
        try:
            data: dict = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return JwtModel.model_validate(data)
        except Exception as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError("Invalid token")


class AuthTokenDatabase(APIKeyHeader, Generic[TUser]):
    param_name = "Authorization"

    def __init__(
        self,
        user_model: type[TUser],
        token_to_user: Callable[[str], TUser | None],
        save_token_to_db: Callable[[TUser, str], None],
        after_login_hook: Callable[[TUser], None] = lambda _: None,
    ):
        self.user_model = user_model
        self.token_to_user = token_to_user
        self.after_login_hook = after_login_hook
        self.save_token_to_db = save_token_to_db

        super().__init__()

    def __call__(self, request: HttpRequest) -> TUser | None:
        # 返回的值保存在request.auth
        auth = super().__call__(request)
        return auth

    def authenticate(self, request: HttpRequest, token: str) -> TUser | None:
        return self.token_to_user(token)

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
        self.after_login_hook(user)
        return user

    def generate_token(self, user: TUser) -> str:
        """生成token"""
        token = uuid.uuid4().hex
        self.save_token_to_db(user, token)
        return token


class AuthBearerModel(HttpBearer, Generic[TUser, TToken]):
    def __init__(
        self,
        user_model: type[TUser],
        token_model: type[TToken],
        user_device_to_token_model: Callable[[TUser, str | None], TToken],
        token_model_to_user: Callable[[TToken], TUser | None],
        token_model_to_redis_key: Callable[[TToken], str],
        cache_token_expires: int = 12 * 60 * 60,
        redis_conn: Redis | None = None,
        secret_key: str = SECRET_KEY,
        after_login_hook: Callable[[TUser], Any] | None = None,
    ):
        self.user_model = user_model
        self.token_model = token_model
        self.user_device_to_token_model = user_device_to_token_model
        self.token_model_to_user = token_model_to_user
        self.token_model_to_redis_key = token_model_to_redis_key
        self.cache_token_expires = cache_token_expires
        self.secret_key = secret_key
        if redis_conn is None:
            redis_conn = get_redis_connection()
        self.redis_conn = redis_conn
        self.after_login_hook = after_login_hook
        super().__init__()

    def __call__(self, request: HttpRequest) -> TToken | None:
        # 返回的值保存在request.auth
        auth = super().__call__(request)
        return auth

    def authenticate(self, request: HttpRequest, token: str) -> TToken | None:
        info = self.decode_token(token)
        if self.get_token(info) != token:
            raise AuthenticationError("Token expired")
        self.set_token(info, token)
        return info

    def set_token(self, info: TToken, token: str):
        key = self.token_model_to_redis_key(info)
        self.redis_conn.set(name=key, value=token, ex=self.cache_token_expires)

    def get_token(self, info: TToken) -> str | None:
        key = self.token_model_to_redis_key(info)
        token_str = self.redis_conn.get(key)
        if token_str is None:
            return None
        if isinstance(token_str, bytes):
            token_str = token_str.decode()
        return str(token_str)

    def get_login_info_optional(self, request: HttpRequest) -> TToken | None:
        auth = None
        if hasattr(request, "auth"):
            auth = getattr(request, "auth")
        else:
            auth = self.__call__(request)
        return auth

    def get_login_user_optional(self, request: HttpRequest) -> TUser | None:
        info = self.get_login_info_optional(request)
        if info is None:
            return None
        user = self.token_model_to_user(info)
        return user

    def get_login_info(self, request: HttpRequest) -> TToken:
        info = self.get_login_info_optional(request)
        if not info:
            raise AuthenticationError("User not logged in")
        return info

    def get_login_user(self, request: HttpRequest) -> TUser:
        user = self.get_login_user_optional(request)
        if not user:
            raise AuthenticationError("User not found")
        if self.after_login_hook is not None:
            self.after_login_hook(user)
        return user

    def encode_token(self, info: TToken) -> str:
        payload = info.dict()
        token_str = jwt.encode(payload, self.secret_key, algorithm="HS256")
        self.set_token(info, token_str)
        return token_str

    def decode_token(self, token_str: str):
        try:
            data: dict = jwt.decode(token_str, self.secret_key, algorithms=["HS256"])
            info = self.token_model.model_validate(data)
        except Exception as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError("Invalid token")
        return info

    def generate_token(self, user: TUser, device: str | None = None) -> str:
        info = self.user_device_to_token_model(user, device)
        token_str = self.encode_token(info)
        self.set_token(info, token_str)
        return token_str
