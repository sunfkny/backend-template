import time
import uuid
from typing import Callable, Generic

import jwt
from django.db.models.base import Model
from django.http.request import HttpRequest
from ninja.errors import AuthenticationError
from ninja.security import APIKeyHeader, HttpBearer
from pydantic import BaseModel, Field
from redis import Redis
from typing_extensions import Type, TypeVar

from backend.settings import REDIS_PREFIX, SECRET_KEY, get_redis_connection

TUser = TypeVar("TUser", bound=Model)
TToken = TypeVar("TToken", bound=BaseModel)


class JwtModel(BaseModel):
    iat: int = Field(default_factory=lambda: int(time.time()))
    uid: int | str


class AuthBearer(HttpBearer, Generic[TUser]):
    def __init__(
        self,
        user_model: Type[TUser],
        uid_field: str = "id",
        cache_token_expires: int = 12 * 60 * 60,
        cache_token_prefix: str | None = None,
        redis_conn: Redis | None = None,
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
        else:
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
        if isinstance(token, bytes):
            token = token.decode()
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
            raise AuthenticationError("not auth")
        return uid

    def get_login_user(self, request: HttpRequest) -> TUser:
        """获取登录用户"""
        user = self.get_login_user_optional(request)
        if not user:
            raise AuthenticationError("uid not found")
        self.after_login_hook(user)
        return user

    def generate_token(self, uid: int | str) -> str:
        """生成token"""
        payload = JwtModel(uid=uid).dict()
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode()
        self.set_token(uid, token)
        return token

    def decode_token(self, token: str):
        """解析token"""
        try:
            data: dict = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return JwtModel.parse_obj(data)
        except Exception as e:
            raise AuthenticationError(f"{e.__class__.__name__}: {e}")


class AuthTokenDatabase(APIKeyHeader, Generic[TUser]):
    param_name = "Authorization"

    def __init__(
        self,
        user_model: Type[TUser],
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
            raise AuthenticationError("token not found")
        self.after_login_hook(user)
        return user

    def generate_token(self, user: TUser) -> str:
        """生成token"""
        token = uuid.uuid4().hex
        self.save_token_to_db(user, token)
        return token
