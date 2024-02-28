from backend.apps.back.models import AdminUser
from backend.apps.user.models import User
from backend.settings import REDIS_PREFIX

from .auth_utils import AuthBearerHelper

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
