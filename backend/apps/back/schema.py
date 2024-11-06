from ninja import ModelSchema, Schema

from .models import AdminPermission, AdminUser, Role


class TokenSchema(Schema):
    token: str


class UrlSchema(Schema):
    url: str


class AdminUserModelSchema(ModelSchema):
    role_name: str
    role_id: int | None

    class Meta:
        model = AdminUser
        fields = [
            "id",
            "avatar",
            "nickname",
            "username",
            "summary",
        ]


class AdminPermissionModelSchema(ModelSchema):
    class Meta:
        model = AdminPermission
        fields = [
            "id",
            "key",
            "name",
            "description",
        ]


class RoleModelSchema(ModelSchema):
    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "description",
        ]


class RolePermissionSchema(Schema):
    role: RoleModelSchema
    permissions: list[AdminPermissionModelSchema]


class StorageListdirSchema(Schema):
    class DirectorySchema(Schema):
        name: str
        path: str

    class FileSchema(Schema):
        name: str
        url: str

    directories: list[DirectorySchema]
    files: list[FileSchema]
