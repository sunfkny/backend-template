from django.db.models import Q, Value
from django.db.models.functions import Concat

from backend.apps.back.models import AdminPermission, AdminUser, Role, RolePermission
from backend.utils.orm import ColF, ColQ, ColQuerySet, get_field_name


def test_get_field_name():
    assert get_field_name(AdminUser.create_time) == "create_time"
    assert get_field_name(AdminUser.update_time) == "update_time"
    assert get_field_name(AdminUser.nickname) == "nickname"
    assert get_field_name(AdminUser.username) == "username"
    assert get_field_name(AdminUser.password) == "password"
    assert get_field_name(AdminUser.avatar) == "avatar"
    assert get_field_name(AdminUser.summary) == "summary"
    assert get_field_name(AdminUser.is_superadmin) == "is_superadmin"
    assert get_field_name(AdminUser.role) == "role"
    assert get_field_name(AdminUser.role_id) == "role_id"
    assert get_field_name(AdminUser.pk) == "pk"
    assert get_field_name(AdminPermission.key) == "key"
    assert get_field_name(AdminPermission.name) == "name"
    assert get_field_name(AdminPermission.description) == "description"
    assert get_field_name(RolePermission.role) == "role"
    assert get_field_name(RolePermission.permission) == "permission"
    assert get_field_name(Role.name) == "name"
    assert get_field_name(Role.description) == "description"
    assert get_field_name(Role.permission) == "permission"
    assert get_field_name(Role) == "role"
    assert get_field_name((AdminUser.role, Role.name)) == "role__name"


def test_col():
    assert (ColQ(AdminUser.pk).filter(0)) == Q(pk=0)
    assert (ColQ(AdminUser.pk).filter(1)) == Q(pk=1)
    assert (ColQ(AdminUser.pk).filter(gte=0)) == Q(pk__gte=0)
    assert (ColQ(AdminUser.pk).filter(lte=0)) == Q(pk__lte=0)
    assert (ColQ(AdminUser.pk).filter(gt=0)) == Q(pk__gt=0)
    assert (ColQ(AdminUser.pk).filter(lt=0)) == Q(pk__lt=0)
    assert (ColQ(AdminUser.pk).filter(ne=0)) == ~Q(pk=0)
    assert (ColQ(AdminUser.pk).filter(range_=(20, 30))) == Q(pk__range=(20, 30))
    assert (ColQ(AdminUser.username).filter("admin")) == Q(username="admin")
    assert (ColQ(AdminUser.username).filter(ne="admin")) == ~Q(username="admin")
    assert (ColQ(AdminUser.username).filter(in_=["admin", "user"])) == Q(username__in=["admin", "user"])
    assert (ColQ(AdminUser.username).filter(like="admin")) == Q(username__like="admin")
    assert (ColQ(AdminUser.username).filter(startswith="admin")) == Q(username__startswith="admin")
    assert (ColQ(AdminUser.username).filter(istartswith="admin")) == Q(username__istartswith="admin")
    assert (ColQ(AdminUser.username).filter(endswith="admin")) == Q(username__endswith="admin")
    assert (ColQ(AdminUser.username).filter(iendswith="admin")) == Q(username__iendswith="admin")
    assert (ColQ(AdminUser.username).filter(contains="admin")) == Q(username__contains="admin")
    assert (ColQ(AdminUser.username).filter(icontains="admin")) == Q(username__icontains="admin")
    assert (ColQ(AdminUser.username).filter(isnull=True)) == Q(username__isnull=True)
    assert (ColQ(AdminUser.username).filter(isnull=False)) == Q(username__isnull=False)
    assert (ColQ((AdminUser.role, Role.name)).filter(isnull=True)) == Q(role__name__isnull=True)
    assert (ColQ((AdminUser.role, Role.name)).filter(isnull=False)) == Q(role__name__isnull=False)


def test_col_query(db, django_assert_num_queries):
    role = Role.objects.create(name="some role name")
    perm = AdminPermission.objects.create(key="admin", name="admin")
    role.permission.add(perm)
    AdminUser.objects.create(username="Admin", role=role)

    q1 = AdminUser.objects.filter(
        ColQ((AdminUser.role, Role.name)).filter("some role name"),
    )
    with django_assert_num_queries(1):
        q1.first()
    assert str(q1.query) == str(
        AdminUser.objects.filter(
            Q(role__name="some role name"),
        ).query
    )

    q2 = (
        AdminUser.objects.filter(
            ColQ(AdminUser.username).filter(icontains="John"),
            ColQ(AdminUser.pk).filter(range_=(20, 30)),
        )
        .order_by(ColF(AdminUser.create_time).order_by(descending=True))
        .select_related(
            ColF(AdminUser.role).name,
        )
    )
    assert str(q2.query) == str(
        AdminUser.objects.filter(
            Q(username__icontains="John"),
            Q(pk__range=(20, 30)),
        )
        .order_by("-create_time")
        .select_related("role")
        .query
    )
    with django_assert_num_queries(1):
        q2.first()

    q3 = AdminPermission.objects.prefetch_related(
        ColF.get_prefetch_related(AdminPermission, Role),
        ColF.get_prefetch_related(AdminPermission, RolePermission),
    )
    assert str(q3.query) == str(
        AdminPermission.objects.prefetch_related(
            "role",
            "rolepermission",
        ).query
    )
    with django_assert_num_queries(3):
        q3.first()

    q4 = AdminPermission.objects.prefetch_related(
        ColF.get_prefetch_related(AdminPermission, Role),
    )
    assert str(q4.query) == str(
        AdminPermission.objects.prefetch_related(
            "role",
        ).query
    )
    with django_assert_num_queries(2):
        q4.first()

    q5 = AdminPermission.objects.prefetch_related(
        ColF.get_prefetch_related(AdminPermission, RolePermission),
    )
    assert str(q5.query) == str(
        AdminPermission.objects.prefetch_related(
            "rolepermission",
        ).query
    )
    with django_assert_num_queries(2):
        q5.first()

    q6 = AdminUser.objects.filter(
        ColQ(AdminUser.username).filter("test@example.com"),
    )
    assert str(q6.query) == str(
        AdminUser.objects.filter(
            Q(username="test@example.com"),
        ).query
    )
    with django_assert_num_queries(1):
        q6.first()

    q7 = AdminUser.objects.filter(
        ColQ(AdminUser.pk).filter(in_=[25, 30, 35]),
    )
    assert str(q7.query) == str(
        AdminUser.objects.filter(
            Q(pk__in=[25, 30, 35]),
        ).query
    )
    with django_assert_num_queries(1):
        q7.count()

    q8 = AdminUser.objects.filter(
        ColQ(AdminUser.username).filter("Alice"),
    )
    assert str(q8.query) == str(
        AdminUser.objects.filter(
            Q(username="Alice"),
        ).query
    )
    with django_assert_num_queries(1):
        q8.first()

    q9 = AdminUser.objects.filter(
        ColQ(AdminUser.create_time).filter(gt="2022-01-01 00:00:00", lt="2022-01-01 00:00:00"),
        ColQ(AdminUser.role_id).filter(lte=1),
        ColQ(AdminUser.pk).filter(lte=1),
    )
    assert str(q9.query) == str(
        AdminUser.objects.filter(
            Q(create_time__gt="2022-01-01 00:00:00", create_time__lt="2022-01-01 00:00:00"),
            Q(role_id__lte=1),
            Q(pk__lte=1),
        ).query
    )
    with django_assert_num_queries(1):
        q9.first()

    q10 = AdminUser.objects.filter(
        ColQ(AdminUser.username).filter(""),
        ColQ(AdminUser.create_time).filter("2022-01-01 00:00:00"),
        ColQ(AdminUser.update_time).filter("2022-01-01 00:00:00"),
        ColQ(AdminUser.nickname).filter(""),
        ColQ(AdminUser.password).filter(""),
        ColQ(AdminUser.avatar).filter(""),
        ColQ(AdminUser.summary).filter(""),
        ColQ(AdminUser.is_superadmin).filter(True),
        ColQ(AdminUser.role).filter(1),
        ColQ(AdminUser.role_id).filter(1),
        ColQ(AdminUser.pk).filter(1),
    )
    assert str(q10.query) == str(
        AdminUser.objects.filter(
            Q(username=""),
            Q(create_time="2022-01-01 00:00:00"),
            Q(update_time="2022-01-01 00:00:00"),
            Q(nickname=""),
            Q(password=""),
            Q(avatar=""),
            Q(summary=""),
            Q(is_superadmin=True),
            Q(role=1),
            Q(role_id=1),
            Q(pk=1),
        ).query
    )
    with django_assert_num_queries(1):
        q10.first()

    q11 = AdminUser.objects.filter(
        ColQ(AdminUser.username).filter(""),
        ColQ(AdminUser.create_time).filter("2022-01-01 00:00:00"),
        ColQ(AdminUser.update_time).filter("2022-01-01 00:00:00"),
        ColQ(AdminUser.nickname).filter(""),
        ColQ(AdminUser.password).filter(""),
    ) | AdminUser.objects.filter(
        ColQ(AdminUser.avatar).filter(""),
        ColQ(AdminUser.summary).filter(""),
        ColQ(AdminUser.is_superadmin).filter(True),
        ColQ(AdminUser.role).filter(1),
        ColQ(AdminUser.role_id).filter(1),
        ColQ(AdminUser.pk).filter(1),
    )
    assert str(q11.query) == str(
        (
            AdminUser.objects.filter(
                Q(username=""),
                Q(create_time="2022-01-01 00:00:00"),
                Q(update_time="2022-01-01 00:00:00"),
                Q(nickname=""),
                Q(password=""),
            )
            | AdminUser.objects.filter(
                Q(avatar=""),
                Q(summary=""),
                Q(is_superadmin=True),
                Q(role=1),
                Q(role_id=1),
                Q(pk=1),
            )
        ).query
    )
    with django_assert_num_queries(1):
        q11.first()

    q12 = AdminPermission.objects.filter(
        ColQ(AdminPermission.key).filter("admin"),
        ColQ(AdminPermission.name).filter("admin"),
        ColQ(AdminPermission.description).filter("admin"),
    )
    assert str(q12.query) == str(
        AdminPermission.objects.filter(
            Q(key="admin"),
            Q(name="admin"),
            Q(description="admin"),
        ).query
    )
    with django_assert_num_queries(1):
        q12.first()

    q13 = RolePermission.objects.filter(
        ColQ(RolePermission.role).filter(1),
        ColQ(RolePermission.permission).filter(1),
    )
    assert str(q13.query) == str(
        RolePermission.objects.filter(
            Q(role=1),
            Q(permission=1),
        ).query
    )
    with django_assert_num_queries(1):
        q13.first()

    q14 = Role.objects.filter(
        ColQ(Role.name).filter("admin"),
        ColQ(Role.description).filter("admin"),
    )
    assert str(q14.query) == str(
        Role.objects.filter(
            Q(name="admin"),
            Q(description="admin"),
        ).query
    )
    with django_assert_num_queries(1):
        q14.first()

    q15 = (
        ColQuerySet(AdminUser)
        .filter_col(AdminUser.username, icontains="admin")
        .filter_col(AdminUser.pk, range_=(20, 30))
        .qs()
    )
    assert str(q15.query) == str(
        AdminUser.objects.filter(
            Q(username__icontains="admin"),
            Q(pk__range=(20, 30)),
        ).query
    )
    with django_assert_num_queries(1):
        q15.first()


def test_col_update(db, django_assert_num_queries):
    role = Role.objects.create(name="some role name")
    other_role = Role.objects.create(name="other role name")
    perm = AdminPermission.objects.create(key="admin", name="admin")
    role.permission.add(perm)
    user = AdminUser.objects.create(username="Admin", role=role)

    assert user.username == "Admin"
    assert user.role == role

    with django_assert_num_queries(1):
        rows = (
            ColQuerySet(AdminUser)
            .filter_col(
                AdminUser.username,
                user.username,
            )
            .update(
                {
                    ColF(AdminUser.username): Concat(
                        ColF(AdminUser.username).f,
                        Value(" update"),
                    ),
                    ColF(AdminUser.role): other_role,
                }
            )
        )
        assert rows == 1

    user.refresh_from_db()
    assert user.username == "Admin update"
    assert user.role == other_role
