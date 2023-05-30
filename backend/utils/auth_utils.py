import logging
import time
from typing import Any, Callable, Generic, Optional, TYPE_CHECKING, cast
import jwt
from django.conf import settings
from django.db.models.base import Model

from django.http.request import HttpRequest
from backend.settings import get_redis_connection
from jwt.exceptions import InvalidTokenError
from ninja.errors import AuthenticationError
from ninja.security import HttpBearer
from redis import Redis
from typing_extensions import Type, TypeVar

logger = logging.getLogger("django")

_T = TypeVar("_T", bound=Model)


class AuthBearer(HttpBearer):
    def __init__(self, authenticate: Callable[[HttpRequest, str], Any]) -> None:
        self._authenticate = authenticate
        super().__init__()

    def authenticate(self, request: HttpRequest, token: str):
        return self._authenticate(request, token)


class AuthBearerHelper(Generic[_T]):
    def __init__(
        self,
        user_model: Type[_T],
        project_name: str,
        cache_token_expires: int = 12 * 60 * 60,
        redis_conn: Redis = get_redis_connection(),
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
        self.cache_token_key = f"{project_name}:{user_model.__name__}:token:"
        self.cache_token_expires = cache_token_expires
        self.secret_key = secret_key
        self.redis_conn = redis_conn
        self.auth = AuthBearer(authenticate=self.authenticate)

    def set_token(self, user_id: int, token: str):
        """设置token"""
        key = self.cache_token_key + str(user_id)
        self.redis_conn.set(name=key, value=token, ex=self.cache_token_expires)

    def get_token(self, user_id: int) -> Optional[str]:
        """获取token"""
        key = self.cache_token_key + str(user_id)
        token = self.redis_conn.get(key)
        if isinstance(token, bytes):
            token = token.decode()
        return token

    def token_check(self, user_id: int, token: str):
        """检查token"""
        return self.get_token(user_id) == token

    def get_login_uid_optional(self, request: HttpRequest) -> Optional[int]:
        """可选获取登录用户id, 未登录返回 None"""
        return self.auth(request)

    def get_login_user_optional(self, request: HttpRequest) -> Optional[_T]:
        """可选获取登录用户, 未登录返回 None"""
        user_id = self.get_login_uid_optional(request)
        user = self.user_model.objects.filter(id=user_id).first()
        if TYPE_CHECKING:
            user = cast(Optional[_T], user)
        return user

    def get_login_uid(self, request: HttpRequest) -> int:
        """获取登录用户id"""
        user_id = getattr(request, "auth", None)
        if not user_id:
            raise AuthenticationError()
        return user_id

    def get_login_user(self, request: HttpRequest) -> _T:
        """获取登录用户"""
        user_id = self.get_login_uid(request)
        user = self.user_model.objects.filter(id=user_id).first()
        if not user:
            raise AuthenticationError()
        if TYPE_CHECKING:
            user = cast(_T, user)
        return user

    def get_login_user_for_update(self, request: HttpRequest) -> _T:
        """获取登录用户(select_for_update)"""
        user_id = self.get_login_uid(request)
        user = self.user_model.objects.select_for_update().filter(id=user_id).first()
        if not user:
            raise AuthenticationError()
        if TYPE_CHECKING:
            user = cast(_T, user)
        return user

    def generate_token(self, user_id: int) -> str:
        """生成token"""
        timestamp = int(time.time())
        payload = {
            "user_id": user_id,
            "iat": timestamp,
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        if isinstance(token, bytes):
            token = token.decode()
        self.set_token(user_id, token)
        return token

    def decode_token(self, token: str):
        """解析token"""
        try:
            data = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return data
        except InvalidTokenError as e:
            raise AuthenticationError() from e

    def authenticate(self, request: HttpRequest, token: str):
        data = self.decode_token(token)
        user_id = data.get("user_id", 0)
        if self.token_check(user_id, token):
            # 续期
            self.set_token(user_id, token)
            return user_id
        else:
            return None

    def get_auth(self) -> AuthBearer:
        """获取认证类"""
        return self.auth
