from backend.apps.back.models import AdminUser
from backend.apps.user.models import User
from backend.security.auth import AuthBearerToken
from backend.settings import get_redis_connection

redis_conn = get_redis_connection()


# 后台登录验证
auth_admin = AuthBearerToken(
    user_model=AdminUser,
    expires=12 * 60 * 60,
    redis_conn=redis_conn,
)

# 前端登录验证
auth = AuthBearerToken(
    user_model=User,
    expires=30 * 24 * 60 * 60,
    redis_conn=redis_conn,
)
