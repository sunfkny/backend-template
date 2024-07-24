import pytest
from django.contrib.auth.hashers import check_password, make_password

from .models import AdminPermission, AdminUser, Role, RolePermission


@pytest.fixture
def admin_user_root(db):
    user = AdminUser.objects.create(
        nickname="root",
        username="root",
        password=make_password("root"),
        is_superadmin=True,
    )
    AdminPermission.sync_data()
    return user


@pytest.fixture
def admin_user(db):
    user = AdminUser.objects.create(
        nickname="admin",
        username="admin",
        password=make_password("admin"),
        is_superadmin=False,
    )
    return user


@pytest.fixture
def permission(db):
    return AdminPermission.objects.create(
        key="Test",
        name="Test",
    )


def test_permission(permission: AdminPermission):
    assert not permission.is_admin


@pytest.fixture
def role(db, permission: AdminPermission):
    r = Role.objects.create(
        name="Test Role",
    )
    r.permission.add(permission)
    return r


def test_role(role: Role, permission: AdminPermission):
    assert role.permission_list == [permission.key]
    assert not role.is_admin


def test_admin_user_role(admin_user: AdminUser, role: Role, permission: AdminPermission):
    assert not admin_user.has_permission(permission.key)
    admin_user.role = role
    admin_user.save(update_fields=["role"])
    assert admin_user.has_permission(permission.key)


def test_superadmin_has_admin_permission(admin_user_root: AdminUser):
    assert admin_user_root.has_permission(AdminPermission.Keys.Admin)


def test_admin_no_admin_permission(admin_user: AdminUser):
    assert not admin_user.has_permission(AdminPermission.Keys.Admin)
