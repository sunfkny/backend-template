from django.db import models
from django.contrib.auth.hashers import make_password, check_password

from backend.settings import DB_PREFIX, DEFAULT_AVATAR


class User(models.Model):
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="修改时间")

    username = models.CharField(max_length=64, verbose_name="用户名")
    password = models.CharField(null=True, blank=True, max_length=255, verbose_name="密码")
    avatar = models.CharField(default=DEFAULT_AVATAR, max_length=255, verbose_name="头像")

    def make_password(self, password):
        self.password = make_password(password)
        self.save(update_fields=["password"])

    def check_password(self, password) -> bool:
        if self.password is None:
            return False
        return check_password(password=password, encoded=self.password)

    class Meta:
        db_table = f"{DB_PREFIX}_user"
        verbose_name = "用户表"
        verbose_name_plural = verbose_name
