from backend.apps.back.models import AdminPermission, AdminUser, Role


def test_permission(permission: AdminPermission):
    assert not permission.is_admin


def test_role(
    role: Role,
    permission: AdminPermission,
):
    assert role.permission_list == [permission.key]
    assert not role.is_admin


def test_admin_user_role(
    admin_user: AdminUser,
    role: Role,
    permission: AdminPermission,
):
    assert not admin_user.has_permission(permission.key)

    admin_user.role = role
    admin_user.save(update_fields=["role"])

    assert admin_user.has_permission(permission.key)


def test_superadmin_has_admin_permission(
    admin_user_root: AdminUser,
):
    assert admin_user_root.has_permission(AdminPermission.Keys.Admin)


def test_admin_no_admin_permission(
    admin_user: AdminUser,
):
    assert not admin_user.has_permission(AdminPermission.Keys.Admin)
