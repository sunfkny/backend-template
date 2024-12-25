from django.contrib import admin

from backend.apps.back.models import AdminPermission, AdminUser, Role, RolePermission


@admin.register(AdminPermission)
class AdminPermissionAdmin(admin.ModelAdmin):
    pass


class RolePermissionInline(admin.TabularInline):
    model = RolePermission
    extra = 0


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    inlines = (RolePermissionInline,)


@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    pass
