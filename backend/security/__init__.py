from backend.apps.back.models import AdminUser
from backend.apps.user.models import User
from backend.settings import get_redis_connection

from .auth_utils import AuthBearer

redis_conn = get_redis_connection()


# 后台登录验证
auth_admin = AuthBearer(
    user_model=AdminUser,
    redis_conn=redis_conn,
    cache_token_expires=12 * 60 * 60,
)

# 前端登录验证
auth = AuthBearer(
    user_model=User,
    cache_token_expires=30 * 24 * 60 * 60,
    redis_conn=redis_conn,
)
