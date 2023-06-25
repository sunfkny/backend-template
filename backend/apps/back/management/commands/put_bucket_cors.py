from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Put bucket cors"
    platform_choices = ["oss", "cos"]

    def add_arguments(self, parser):
        parser.add_argument(
            "platform",
            type=str,
            help=" | ".join(self.platform_choices),
        )
        parser.add_argument(
            "--force",
            "-f",
            action="store_true",
            default=False,
            help="delete and readd cors rule",
        )

    def handle(self, *args, **options):
        platform: str = options["platform"]
        force = options["force"]

        if platform.lower() == "oss":
            self.handle_oss(force)
        elif platform.lower() == "cos":
            self.handle_cos(force)
        else:
            raise CommandError(f"Unknown platform {platform!r}")

    def handle_oss(self, force: bool):
        try:
            import oss2
        except ImportError:
            raise CommandError("oss2 is not installed")

        OSS_ACCESS_KEY_ID = str(getattr(settings, "OSS_ACCESS_KEY_ID", ""))
        OSS_ACCESS_KEY_SECRET = str(getattr(settings, "OSS_ACCESS_KEY_SECRET", ""))
        OSS_ENDPOINT = str(getattr(settings, "OSS_ENDPOINT", ""))
        OSS_BUCKET_NAME = str(getattr(settings, "OSS_BUCKET_NAME", ""))
        assert OSS_ACCESS_KEY_ID
        assert OSS_ACCESS_KEY_SECRET
        assert OSS_ENDPOINT
        assert OSS_BUCKET_NAME

        auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
        bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

        if force:
            bucket.delete_bucket_cors()

        try:
            cors = bucket.get_bucket_cors()
        except oss2.exceptions.NoSuchCors:
            print("create new cors rule")
            rule = oss2.models.CorsRule(
                allowed_origins=["*"],
                allowed_methods=["GET", "POST", "HEAD", "PUT", "DELETE"],
                allowed_headers=["*"],
            )
            resp = bucket.put_bucket_cors(oss2.models.BucketCors([rule]))
            print(f"put_bucket_cors {resp.status}")
        else:
            rules: list[oss2.models.CorsRule] = cors.rules
            print(
                [
                    {
                        "AllowedOrigins": rule.allowed_origins,
                        "AllowedMethods": rule.allowed_methods,
                        "AllowedHeaders": rule.allowed_headers,
                    }
                    for rule in rules
                ]
            )
            raise CommandError("cors rule already exists")

    def handle_cos(self, force: bool):
        try:
            from qcloud_cos import CosConfig
            from qcloud_cos import CosS3Client
            from qcloud_cos.cos_exception import CosException, CosServiceError
        except ImportError:
            raise CommandError("qcloud_cos is not installed")

        COS_SECRET_ID = str(getattr(settings, "COS_SECRET_ID", ""))
        COS_SECRET_KEY = str(getattr(settings, "COS_SECRET_KEY", ""))
        COS_BUCKET_APPID = str(getattr(settings, "COS_BUCKET_APPID", ""))
        COS_REGION = str(getattr(settings, "COS_REGION", ""))
        assert COS_SECRET_ID
        assert COS_SECRET_KEY
        assert COS_BUCKET_APPID
        assert COS_REGION

        config = CosConfig(Region=COS_REGION, SecretId=COS_SECRET_ID, SecretKey=COS_SECRET_KEY)
        client = CosS3Client(config)

        if force:
            client.delete_bucket_cors(Bucket=COS_BUCKET_APPID)

        try:
            cors = client.get_bucket_cors(Bucket=COS_BUCKET_APPID)
        except CosServiceError as e:
            if not e.get_error_code() == "NoSuchCORSConfiguration":
                raise
            print("create new cors rule")
            client.put_bucket_cors(
                Bucket=COS_BUCKET_APPID,
                CORSConfiguration={
                    "CORSRule": [
                        {
                            "AllowedOrigin": ["*"],
                            "AllowedMethod": ["GET", "POST", "HEAD", "PUT", "DELETE"],
                            "AllowedHeader": ["*"],
                            "ExposeHeader": ["Content-Length", "ETag", "x-cos-meta-author"],
                        }
                    ]
                },
            )
            print("put_bucket_cors success")
        else:
            print(cors["CORSRule"])
            raise CommandError("cors rule already exists")
