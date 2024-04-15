import time
from typing import TYPE_CHECKING, Generic, cast

import jwt
from django.conf import settings
from django.db.models.base import Model
from django.http.request import HttpRequest
from ninja.errors import AuthenticationError
from ninja.security import HttpBearer
from pydantic import BaseModel, Field
from redis import Redis
from typing_extensions import Type, TypeVar

from backend.settings import get_redis_connection

_T = TypeVar("_T", bound=Model)


class JwtModel(BaseModel):
    iat: int = Field(default_factory=lambda: int(time.time()))
    uid: int | str


class AuthBearer(HttpBearer, Generic[_T]):
    def __init__(
        self,
        project_name: str,
        user_model: Type[_T],
        uid_field: str = "id",
        cache_token_expires: int = 12 * 60 * 60,
        redis_conn: Redis | None = None,
        secret_key: str = settings.SECRET_KEY,
    ):
        """
        user_model: 用户模型
        project_name: 项目名称
        cache_token_expires: 缓存token的过期时间(秒)
        redis_conn: redis连接
        secret_key: jwt加密的密钥
        """
        self.user_model = user_model
        self.uid_field = uid_field
        self.cache_token_key = f"{project_name}:{user_model.__name__}:token:"
        self.cache_token_expires = cache_token_expires
        self.secret_key = secret_key
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
        key = self.cache_token_key + str(uid)
        self.redis_conn.set(name=key, value=token, ex=self.cache_token_expires)

    def get_token(self, uid: int | str) -> str | None:
        """获取token"""
        key = self.cache_token_key + str(uid)
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

    def get_login_user_optional(self, request: HttpRequest) -> _T | None:
        """可选获取登录用户, 未登录返回 None"""
        uid = self.get_login_uid_optional(request)
        user = self.user_model.objects.filter(
            **{
                self.uid_field: uid,
            }
        ).first()
        if TYPE_CHECKING:
            user = cast(_T | None, user)
        return user

    def get_login_uid(self, request: HttpRequest) -> int | str:
        """获取登录用户uid"""
        uid = self.get_login_uid_optional(request)
        if not uid:
            raise AuthenticationError("not auth")
        return uid

    def get_login_user(self, request: HttpRequest) -> _T:
        """获取登录用户"""
        user = self.get_login_user_optional(request)
        if not user:
            raise AuthenticationError("uid not found")
        if TYPE_CHECKING:
            user = cast(_T, user)
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
