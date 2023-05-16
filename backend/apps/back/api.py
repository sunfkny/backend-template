import logging

from back.models import AdminUser, AdminPermission, Role
from django.contrib.auth.hashers import check_password, make_password
from django.core.paginator import InvalidPage, Paginator
from django.http import HttpRequest
from ninja import Form, Query, Router

from backend.utils.auth import auth_admin
from backend.utils.response_types import Response
from backend.settings import get_redis_connection, REDIS_PREFIX

router = Router(tags=["后台"])
logger = logging.getLogger("django")
redis_conn = get_redis_connection()


@router.post("login", summary="后台登录")
def admin_user_login(
    request: HttpRequest,
    username: str = Form(..., description="账号"),
    password: str = Form(..., description="密码"),
):
    user = AdminUser.objects.filter(username=username).first()
    if user and user.check_password(password):
        token = auth_admin.generate_token(user.pk)
        data = {
            "token": token,
        }
        return Response.data(data)

    return Response.error(msg="帐号或密码错误")


@router.post("password", auth=auth_admin.get_auth(), summary="后台修改密码")
def admin_password(
    request: HttpRequest,
    old_password: str = Form(..., description="旧密码"),
    new_password: str = Form(..., description="新密码"),
):
    user = auth_admin.get_login_user(request)
    if not user.check_password(old_password):
        return Response.error(msg="密码错误")

    user.make_password(new_password)
    return Response.ok()


@router.post("password/reset", auth=auth_admin.get_auth(), summary="超级管理员后台重置密码")
def admin_password_reset(
    request: HttpRequest,
    username: str = Form(..., description="用户名"),
):
    user = auth_admin.get_login_user(request)
    if not user.is_admin:
        return Response.error(msg="没有权限")

    user = AdminUser.objects.filter(username=username).first()
    if not user:
        return Response.error(msg="用户不存在")

    user.make_password(user.username)

    return Response.ok()


@router.get("user/info", auth=auth_admin.get_auth(), summary="后台用户信息")
def admin_user_info(
    request: HttpRequest,
):
    user = auth_admin.get_login_user(request)
    data = {
        "id": user.pk,
        "introduction": user.summary,
        "role_name": user.role_name,
        "roles": user.permissions,
        "avatar": user.avatar,
        "nickname": user.nickname,
    }
    return Response.data(data)


@router.post("user/info/edit", auth=auth_admin.get_auth(), summary="后台用户信息修改")
def admin_user_info_edit(
    request: HttpRequest,
    admin_user_id: int = Form(0, alias="id", description="后台用户id(Admin权限)"),
    summary: str = Form(..., description="简介"),
    nickname: str = Form(..., description="显示名称"),
    avatar: str = Form(..., description="头像"),
):
    admin_user = auth_admin.get_login_user(request)
    if admin_user.is_admin and admin_user_id:
        admin_user = AdminUser.objects.filter(id=admin_user_id).first()
        if not admin_user:
            return Response.error(msg="后台用户不存在")

    admin_user.summary = summary
    admin_user.nickname = nickname
    admin_user.avatar = avatar
    admin_user.save()
    return Response.ok()


@router.get("user/info/detail", auth=auth_admin.get_auth(), summary="后台用户信息详情")
def admin_user_info_detail(
    request: HttpRequest,
    admin_user_id: int = Query(0, alias="id", description="后台用户id(Admin权限)"),
):
    admin_user = auth_admin.get_login_user(request)
    if admin_user.is_admin and admin_user_id:
        admin_user = AdminUser.objects.filter(id=admin_user_id).first()
        if not admin_user:
            return Response.error(msg="后台用户不存在")

    data = {
        "id": admin_user.pk,
        "nickname": admin_user.nickname,
        "summary": admin_user.summary,
    }
    return Response.data(data)


@router.get("user/info/list", auth=auth_admin.get_auth(), summary="后台用户列表")
def admin_user_info_list(
    request: HttpRequest,
    page: int = Query(1, description="页码"),
    size: int = Query(10, description="每页数量"),
    nickname: str = Query("", description="显示名称筛选"),
    username: str = Query("", description="登录名称筛选"),
):
    admin_user = auth_admin.get_login_user(request)
    queryset = AdminUser.objects.order_by("-id")
    if not admin_user.is_admin:
        queryset = queryset.filter(id=admin_user.pk)
    if nickname:
        queryset = queryset.filter(nickname__icontains=nickname)
    if username:
        queryset = queryset.filter(username__icontains=username)

    paginator = Paginator(queryset, size)
    try:
        page_business = paginator.page(page)
    except InvalidPage:
        return Response.error(msg="页数错误")
    data = [
        {
            "id": i.pk,
            "nickname": i.nickname,
            "summary": i.summary,
            "username": i.username,
            "role_id": i.role.pk if i.role else 0,
            "role_name": i.role_name,
        }
        for i in page_business
    ]
    return Response.page_list(data, total_page=paginator.num_pages, total=paginator.count)


@router.get("admin/permission/list", auth=auth_admin.get_auth(), summary="权限列表")
def admin_permission_list(
    request: HttpRequest,
    page: int = Query(..., description="页数"),
    size: int = Query(..., description="每页数量"),
):
    admin_user = auth_admin.get_login_user(request)
    if not admin_user.is_admin:
        return Response.error(msg="没有权限")

    queryset = AdminPermission.objects.all().order_by("id")
    try:
        page_permission = Paginator(queryset, size).page(page)
    except InvalidPage:
        return Response.error(msg="页数错误")
    data = []
    for i in page_permission:
        data.append(
            {
                "id": i.pk,
                "key": i.key,
                "name": i.name,
                "description": i.description,
            }
        )

    return Response.page_list(
        data=data,
        total_page=page_permission.paginator.num_pages,
        total=page_permission.paginator.count,
    )


@router.post("admin/permission/edit", auth=auth_admin.get_auth(), summary="权限修改")
def admin_permission_edit(
    request: HttpRequest,
    permission_id: int = Form(..., description="权限id", alias="id"),
    # key: str = Form(..., description="权限标识"),
    name: str = Form(..., description="权限名称"),
    description: str = Form(..., description="权限描述"),
):
    admin_user = auth_admin.get_login_user(request)
    if not admin_user.is_admin:
        return Response.error(msg="没有权限")

    permission = AdminPermission.objects.filter(id=permission_id).first()
    if not permission:
        return Response.error(msg="权限不存在")

    # permission.key = key
    permission.name = name
    permission.description = description
    permission.save()
    return Response.ok()


@router.get("admin/role/list", auth=auth_admin.get_auth(), summary="角色列表")
def admin_role_list(
    request: HttpRequest,
    page: int = Query(1, description="页数"),
    size: int = Query(10, description="每页数量"),
):
    admin_user = auth_admin.get_login_user(request)
    if not admin_user.is_admin:
        return Response.error(msg="没有权限")

    queryset = Role.objects.order_by("id")
    try:
        page_role = Paginator(queryset, size).page(page)
    except InvalidPage:
        return Response.error(msg="页数错误")
    data = []
    for i in page_role:
        data.append(
            {
                "id": i.pk,
                "name": i.name,
                "description": i.description,
            }
        )

    return Response.page_list(
        data=data,
        total_page=page_role.paginator.num_pages,
        total=page_role.paginator.count,
    )


@router.post("admin/role/edit", auth=auth_admin.get_auth(), summary="角色修改")
def admin_role_edit(
    request: HttpRequest,
    role_id: int = Form(..., description="角色id", alias="id"),
    name: str = Form(..., description="角色名称"),
    description: str = Form(..., description="角色描述"),
):
    admin_user = auth_admin.get_login_user(request)
    if not admin_user.is_admin:
        return Response.error(msg="没有权限")

    role = Role.objects.filter(id=role_id).first()
    if not role:
        return Response.error(msg="角色不存在")

    role.name = name
    role.description = description
    role.save()
    return Response.ok()


@router.post("admin/role/add", auth=auth_admin.get_auth(), summary="角色添加")
def admin_role_add(
    request: HttpRequest,
    name: str = Form(..., description="角色名称"),
    description: str = Form(..., description="角色描述"),
):
    admin_user = auth_admin.get_login_user(request)
    if not admin_user.is_admin:
        return Response.error(msg="没有权限")

    role = Role.objects.filter(name=name).first()
    if role:
        return Response.error(msg="角色已存在")
    Role.objects.create(name=name, description=description)
    return Response.ok()


@router.get("admin/role/permission/list", auth=auth_admin.get_auth(), summary="角色权限列表")
def admin_role_permission_list(
    request: HttpRequest,
    role_id: int = Query(..., description="角色id", alias="id"),
):
    admin_user = auth_admin.get_login_user(request)
    if not admin_user.is_admin:
        return Response.error(msg="没有权限")

    role = Role.objects.filter(id=role_id).first()
    if not role:
        return Response.error(msg="角色不存在")

    permissions = []
    if role.permission:
        role_permission = role.permission.all()
        permissions = [
            {
                "id": i.pk,
                "key": i.key,
                "name": i.name,
                "description": i.description,
            }
            for i in role_permission
        ]

    data = {
        "role": {
            "id": role.pk,
            "name": role.name,
        },
        "permissions": permissions,
    }
    return Response.data(data)


@router.post("admin/role/permission/add", auth=auth_admin.get_auth(), summary="角色权限增加")
def admin_role_permission_add(
    request: HttpRequest,
    role_id: int = Form(..., description="角色id"),
    permission_id: int = Form(..., description="权限id"),
):
    admin_user = auth_admin.get_login_user(request)
    if not admin_user.is_admin:
        return Response.error(msg="没有权限")

    role = Role.objects.filter(id=role_id).first()
    if not role:
        return Response.error(msg="角色不存在")

    permission = AdminPermission.objects.filter(id=permission_id).first()
    if not permission:
        return Response.error(msg="权限不存在")

    role.permission.add(permission)
    return Response.ok()


@router.post("admin/role/permission/remove", auth=auth_admin.get_auth(), summary="角色权限移除")
def admin_role_permission_remove(
    request: HttpRequest,
    role_id: int = Form(..., description="角色id"),
    permission_id: int = Form(..., description="权限id"),
):
    admin_user = auth_admin.get_login_user(request)
    if not admin_user.is_admin:
        return Response.error(msg="没有权限")

    role = Role.objects.filter(id=role_id).first()
    if not role:
        return Response.error(msg="角色不存在")

    permission = AdminPermission.objects.filter(id=permission_id).first()
    if not permission:
        return Response.error(msg="权限不存在")

    role.permission.remove(permission)
    return Response.ok()


@router.post("admin/user/add", auth=auth_admin.get_auth(), summary="后台用户创建")
def admin_user_add(
    request: HttpRequest,
    nickname: str = Form(..., description="后台用户名称"),
    username: str = Form(..., description="后台用户名"),
    password: str = Form(..., description="后台用户密码"),
    role_id: int = Form(..., description="角色id"),
):
    admin_user = auth_admin.get_login_user(request)
    if not admin_user.is_admin:
        return Response.error(msg="没有权限")

    role = Role.objects.filter(id=role_id).first()
    if not role:
        return Response.error(msg="角色不存在")

    if AdminUser.objects.filter(username=username).first():
        return Response.error(msg="后台用户已存在")

    AdminUser.objects.create(
        username=username,
        nickname=nickname,
        password=make_password(password),
        role=role,
    )
    return Response.ok()


@router.get("dropdown/role", summary="角色选择下拉")
def dropdown_role(
    request: HttpRequest,
):
    data = list(Role.objects.values("id", "name"))
    return Response.list(data)


@router.get("dropdown/permission", summary="权限选择下拉")
def dropdown_permission(
    request: HttpRequest,
):
    data = list(AdminPermission.objects.values("id", "name", "key"))
    return Response.list(data)


@router.post("back/admin/edit", auth=auth_admin.get_auth(), summary="后台管理员角色修改")
def back_admin_edit(
    request: HttpRequest,
    admin_user_id: int = Form(..., description="后台用户id"),
    role_id: int = Form(..., description="角色id"),
):
    login_user = auth_admin.get_login_user(request)
    if not login_user.is_admin:
        return Response.error(msg="没有权限")

    role = Role.objects.filter(id=role_id).first()
    if not role:
        return Response.error(msg="角色不存在")

    change_user = AdminUser.objects.filter(id=admin_user_id).first()
    if not change_user:
        return Response.error(msg="用户不存在")

    change_user.role = role
    change_user.save()

    return Response.ok()
