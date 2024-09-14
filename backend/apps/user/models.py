from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from backend.settings import DB_PREFIX


class User(models.Model):
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    username = models.CharField(max_length=64, verbose_name="用户名")
    password = models.CharField(null=True, blank=True, max_length=255, verbose_name="密码")

    def make_password(self, password: str):
        self.password = make_password(password)
        self.save(update_fields=["password"])

    def check_password(self, password: str) -> bool:
        if self.password is None:
            return False
        return check_password(password=password, encoded=self.password)

    class Meta:
        db_table = f"{DB_PREFIX}_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name
