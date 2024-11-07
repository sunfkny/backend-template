import pytest
from ninja.testing import TestClient
from ninja.testing.client import NinjaResponse

from backend.apps.back.models import AdminPermission, AdminUser, Role


@pytest.fixture
def client(db):
    from backend.apps.back import api_back

    api_back.auth_admin.set_token = lambda *_, **__: None
    api_back.auth_admin.token_check = lambda *_, **__: True

    client = TestClient(api_back.router)

    response = client.post(
        "/admin/login",
        json={"username": "root", "password": "root@123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def check_business_code(response: NinjaResponse):
    assert response.status_code == 200, response.content
    assert response.json()["code"] == 200, response.content


def check_business_data(response: NinjaResponse):
    assert response.status_code == 200, response.content
    assert response.json()["code"] == 200, response.content
    assert response.json()["data"]


def test_post_admin_login(client: TestClient):
    with pytest.raises(ValueError, match="帐号或密码错误"):
        client.post(
            "/admin/login",
            json={"username": "root", "password": "wrongpassword"},
        )


def test_post_admin_password(client: TestClient):
    response = client.post(
        "/admin/password",
        json={"old_password": "root@123", "new_password": "root@1234"},
    )
    assert response.status_code == 200


def test_post_admin_password_reset(client: TestClient):
    response = client.post(
        "/admin/password/reset",
        json={"username": "root"},
    )
    check_business_code(response)


def test_get_admin_user_info(client: TestClient):
    response = client.get(
        "/admin/user/info",
    )
    check_business_code(response)


def test_post_admin_user_info_edit(client: TestClient):
    response = client.post(
        "/admin/user/info/edit",
        json={
            "admin_user_id": 1,
            "summary": "test summary",
            "nickname": "test nickname",
            "avatar": "test avatar",
        },
    )
    user = AdminUser.objects.get(id=1)
    assert user.summary == "test summary"
    assert user.nickname == "test nickname"
    assert user.avatar == "test avatar"
    check_business_code(response)


def test_get_admin_user_info_detail(client: TestClient):
    response = client.get(
        "/admin/user/info/detail",
        params={"admin_user_id": 1},
    )
    check_business_code(response)


def test_get_admin_user_info_list(client: TestClient):
    response = client.get(
        "/admin/user/info/list",
    )
    check_business_data(response)


def test_get_admin_permission_list(client: TestClient):
    response = client.get(
        "/admin/permission/list",
    )
    check_business_data(response)


def test_post_admin_permission_edit(client: TestClient):
    response = client.post(
        "/admin/permission/edit",
        json={
            "id": 1,
            "name": "test permission",
            "description": "test description",
        },
    )
    check_business_code(response)
    permission = AdminPermission.objects.get(id=1)
    assert permission.name == "test permission"
    assert permission.description == "test description"


def test_get_admin_role_list(client: TestClient):
    Role.objects.get_or_create(id=1, defaults={"name": "test role list", "description": "test description list"})
    response = client.get(
        "/admin/role/list",
    )
    check_business_data(response)


def test_post_admin_role_edit(client: TestClient):
    role, _ = Role.objects.get_or_create(id=1, defaults={"name": "test role", "description": "test description"})
    response = client.post(
        "/admin/role/edit",
        json={
            "id": 1,
            "name": "test role edit",
            "description": "test description edit",
        },
    )
    check_business_code(response)
    role.refresh_from_db()
    assert role.name == "test role edit"
    assert role.description == "test description edit"


def test_post_admin_role_add(client: TestClient):
    response = client.post(
        "/admin/role/add",
        json={
            "name": "test role add",
            "description": "test description add",
        },
    )
    check_business_code(response)
    assert Role.objects.filter(name="test role add").exists()


def test_get_admin_role_permission_list(client: TestClient):
    Role.objects.get_or_create(id=1, defaults={"name": "test role", "description": "test description"})
    response = client.get(
        "/admin/role/permission/list?id=1",
    )
    check_business_data(response)


def test_post_admin_role_permission_add(client: TestClient):
    role, _ = Role.objects.get_or_create(id=1, defaults={"name": "test role", "description": "test description"})
    permission = AdminPermission.objects.get(id=1)
    response = client.post(
        "/admin/role/permission/add",
        json={
            "role_id": 1,
            "permission_id": 1,
        },
    )
    check_business_code(response)
    role.refresh_from_db()
    assert permission.key in role.permission_list


def test_post_admin_role_permission_remove(client: TestClient):
    role, _ = Role.objects.get_or_create(id=1, defaults={"name": "test role", "description": "test description"})
    permission = AdminPermission.objects.get(id=1)
    role.permission.add(permission)
    role.refresh_from_db()
    assert permission.key in role.permission_list
    response = client.post(
        "/admin/role/permission/remove",
        json={
            "role_id": 1,
            "permission_id": 1,
        },
    )
    check_business_code(response)
    role.refresh_from_db()
    assert permission.key not in role.permission_list


def post_admin_user_add(client: TestClient):
    role, _ = Role.objects.get_or_create(id=1, defaults={"name": "test role", "description": "test description"})
    response = client.post(
        "/admin/user/add",
        json={
            "username": "test user add",
            "password": "test password add",
            "role_id": 1,
        },
    )
    check_business_code(response)
    assert AdminUser.objects.filter(username="test user add").exists()


def test_get_admin_dropdown_role_list(client: TestClient):
    role, _ = Role.objects.get_or_create(id=1, defaults={"name": "test role", "description": "test description"})
    response = client.get(
        "/admin/dropdown/role",
    )
    check_business_data(response)


def test_get_admin_dropdown_permission_list(client: TestClient):
    response = client.get(
        "/admin/dropdown/permission",
    )
    check_business_data(response)


def test_post_admin_user_role_edit(client: TestClient):
    role, _ = Role.objects.get_or_create(id=1, defaults={"name": "test role", "description": "test description"})
    user = AdminUser.objects.create(username="test user", password="test password")
    response = client.post(
        "/admin/user/role/edit",
        json={
            "admin_user_id": user.pk,
            "role_id": 1,
        },
    )
    check_business_code(response)
    user.refresh_from_db()
    assert user.role == role
