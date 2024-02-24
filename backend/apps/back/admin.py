from django.contrib import admin

from backend.apps.back.models import AdminPermission, AdminUser, Role, RolePermission


@admin.register(AdminPermission)
class AdminPermissionAdmin(admin.ModelAdmin):
    pass


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    pass


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    pass
