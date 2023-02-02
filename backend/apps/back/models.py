from django.db import models
from typing_extensions import Self, TypeAlias
from typing import List, Optional
from backend.settings import DB_PREFIX, DEFAULT_AVATAR_BACK


class Permission(models.Model):
    class Keys(models.TextChoices):
        Admin = "Admin"

    key = models.CharField(unique=True, max_length=255, verbose_name="权限标识")
    name = models.CharField(max_length=255, verbose_name="权限名称")
    description = models.CharField(default="", max_length=255, verbose_name="权限描述")

    @property
    def is_admin(self) -> bool:
        return Permission.Keys.Admin == self.key

    class Meta:
        db_table = f"{DB_PREFIX}_permission"
        verbose_name = "权限表"
        verbose_name_plural = verbose_name


class Role(models.Model):
    PermissionM2M: TypeAlias = "models.ManyToManyField[Permission, Self]"
    name = models.CharField(max_length=255, verbose_name="角色名称")
    description = models.CharField(default="", max_length=255, verbose_name="角色描述")
    permission: PermissionM2M = models.ManyToManyField(Permission, db_table="gmeta_role_permission", verbose_name="权限")

    @property
    def permission_list(self):
        return list(self.permission.values_list("key", flat=True))

    @property
    def is_admin(self) -> bool:
        return Permission.Keys.Admin in self.permission_list

    class Meta:
        db_table = f"{DB_PREFIX}_role"
        verbose_name = "角色表"
        verbose_name_plural = verbose_name


class AdminUser(models.Model):
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="修改时间")

    SelfForeignKey: TypeAlias = "models.ForeignKey[Optional[Self]]"
    PermissionM2M: TypeAlias = "models.ManyToManyField[Permission, Self]"

    nickname = models.CharField(max_length=20, verbose_name="显示名称")
    username = models.CharField(unique=True, max_length=255, verbose_name="帐号")
    password = models.CharField(max_length=255, verbose_name="密码")
    avatar = models.CharField(default=DEFAULT_AVATAR_BACK, max_length=255, verbose_name="头像")
    summary = models.CharField(default="", max_length=512, verbose_name="简介")
    is_superadmin = models.BooleanField(default=False, verbose_name="是否超级管理员")
    role = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="角色")

    class Meta:
        db_table = f"{DB_PREFIX}_admin_user"
        verbose_name = "后台用户表"
        verbose_name_plural = verbose_name

    @property
    def role_name(self):
        return self.role.name if self.role else ""

    @property
    def permissions(self) -> List[str]:
        permission_list = self.role.permission_list if self.role else []
        if self.is_superadmin and Permission.Keys.Admin not in permission_list:
            permission_list.append(Permission.Keys.Admin)
        return permission_list

    def has_permission(self, permission: Permission.Keys) -> bool:
        return permission in self.permissions

    @property
    def is_admin(self) -> bool:
        return self.is_superadmin or self.has_permission(Permission.Keys.Admin)

    def __str__(self):
        return self.username
