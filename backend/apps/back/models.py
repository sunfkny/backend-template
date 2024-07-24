from urllib.parse import urljoin

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from backend.settings import BASE_URL, DB_PREFIX


def get_default_avatar():
    return urljoin(BASE_URL, "media/default_avatar.svg")


class AdminPermission(models.Model):
    class Keys(models.TextChoices):
        Admin = "Admin", "超级管理员"

    key = models.CharField(unique=True, max_length=255, verbose_name="权限标识")
    name = models.CharField(max_length=255, verbose_name="权限名称")
    description = models.CharField(default="", max_length=255, verbose_name="权限描述")

    class Meta:
        db_table = f"{DB_PREFIX}_permission"
        verbose_name = "权限表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.key

    @staticmethod
    def sync_data():
        for i in AdminPermission.Keys:
            if not AdminPermission.objects.filter(key=i.value).exists():
                AdminPermission.objects.create(key=i.value, name=i.label)
            else:
                AdminPermission.objects.filter(key=i.value).update(name=i.label)

    @property
    def is_admin(self) -> bool:
        return AdminPermission.Keys.Admin == self.key


class RolePermission(models.Model):
    role: "models.ForeignKey[Role]"
    role = models.ForeignKey("Role", on_delete=models.PROTECT, verbose_name="角色")
    permission = models.ForeignKey(AdminPermission, on_delete=models.PROTECT, verbose_name="权限")

    class Meta:
        db_table = f"{DB_PREFIX}_role_permission"
        verbose_name = "角色权限表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class Role(models.Model):
    name = models.CharField(max_length=255, verbose_name="角色名称")
    description = models.CharField(default="", max_length=255, verbose_name="角色描述")
    permission = models.ManyToManyField(AdminPermission, through=RolePermission, verbose_name="权限")

    class Meta:
        db_table = f"{DB_PREFIX}_role"
        verbose_name = "角色表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    @property
    def permission_list(self):
        return list(self.permission.values_list("key", flat=True))

    @property
    def is_admin(self) -> bool:
        return AdminPermission.Keys.Admin in self.permission_list


class AdminUser(models.Model):
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    nickname = models.CharField(max_length=20, verbose_name="显示名称")
    username = models.CharField(unique=True, max_length=255, verbose_name="帐号")
    password = models.CharField(max_length=255, verbose_name="密码")
    avatar = models.CharField(default=get_default_avatar, max_length=255, verbose_name="头像")
    summary = models.CharField(default="", max_length=512, verbose_name="简介")
    is_superadmin = models.BooleanField(default=False, verbose_name="是否超级管理员")
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="角色")

    class Meta:
        db_table = f"{DB_PREFIX}_admin_user"
        verbose_name = "后台用户表"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    @property
    def role_name(self):
        return self.role.name if self.role else ""

    @property
    def permissions(self) -> list[str]:
        permission_list = self.role.permission_list if self.role else []
        if self.is_superadmin and AdminPermission.Keys.Admin not in permission_list:
            permission_list.append(AdminPermission.Keys.Admin)
        return permission_list

    def has_permission(self, permission: AdminPermission.Keys | str) -> bool:
        return permission in self.permissions

    def make_password(self, password: str):
        self.password = make_password(password)
        self.save(update_fields=["password"])

    def check_password(self, password: str | None) -> bool:
        return check_password(password=password, encoded=self.password)

    @property
    def is_admin(self) -> bool:
        return self.is_superadmin or self.has_permission(AdminPermission.Keys.Admin)
