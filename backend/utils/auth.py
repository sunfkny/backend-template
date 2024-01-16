from .auth_utils import AuthBearerHelper
from backend.settings import REDIS_PREFIX
from back.models import AdminUser
from user.models import User

# 后台登录验证
auth_admin = AuthBearerHelper(
    user_model=AdminUser,
    project_name=REDIS_PREFIX,
    cache_token_expires=12 * 60 * 60,
)
# 前端登录验证
auth = AuthBearerHelper(
    user_model=User,
    project_name=REDIS_PREFIX,
    cache_token_expires=30 * 24 * 60 * 60,
)
