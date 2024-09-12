from collections.abc import Iterator

import pytest
from django.contrib.auth.hashers import make_password
from loguru import logger

from backend.apps.back.models import AdminPermission, AdminUser, Role


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


@pytest.fixture
def role(db, permission: AdminPermission):
    r = Role.objects.create(
        name="Test Role",
    )
    r.permission.add(permission)
    return r


# pytest-loguru
@pytest.fixture
def caplog(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    def filter_(record):
        return record["level"].no >= caplog.handler.level

    handler_id = logger.add(caplog.handler, level=0, format="{message}", filter=filter_)
    yield caplog
    logger.remove(handler_id)
