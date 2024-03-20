__doc__ = """
使用方法
```python
@router.post("upload/params", summary="获取 PostObject 上传参数")
def post_upload_params(
    request: HttpRequest,
    ext: str = Form(..., description="文件后缀"),
):
    # [PostObject](https://help.aliyun.com/document_detail/31988.html)
    return Response.data(get_oss_upload_params(ext))

@router.post("post/object/callback", summary="上传回调", include_in_schema=False)
def post_object_callback(request: HttpRequest):
    body = request.body.decode()
    logger.info(body)
    return HttpResponse(body)
```
配置跨域
```python
import oss2

OSS_ACCESS_KEY_ID = "..."
OSS_ACCESS_KEY_SECRET = "..."
OSS_ENDPOINT = "..."
OSS_BUCKET_NAME = "..."
FORCE = False

auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

if FORCE:
    bucket.delete_bucket_cors()
try:
    cors: oss2.models.GetBucketCorsResult = bucket.get_bucket_cors()
except oss2.exceptions.NoSuchCors:
    print("create new cors rule")
    rule = oss2.models.CorsRule(
        allowed_origins=["*"],
        allowed_methods=["GET", "POST", "HEAD", "PUT", "DELETE"],
        allowed_headers=["*"],
    )
    resp = bucket.put_bucket_cors(oss2.models.BucketCors([rule]))
    print("put_bucket_cors", resp.status)
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
    raise Exception("cors rule already exists")
```
"""

import base64
import datetime
import hashlib
import hmac
import json
import uuid

from pydantic import BaseModel

OSS_ACCESS_KEY_ID = "..."
OSS_ACCESS_KEY_SECRET = "..."
OSS_ENDPOINT = "..."
OSS_BUCKET_NAME = "..."


class Oss(BaseModel):
    OSSAccessKeyId: str
    key: str
    policy: str
    signature: str
    # callback: str = ""
    # success_action_status: Literal["200", "201", "204"] = "204"


class OssUploadData(BaseModel):
    host: str
    url: str
    max_file_size: int = 20 * 1024 * 1024
    oss: Oss


def md5_encode(data: str):
    m = hashlib.md5()
    m.update(data.encode())
    return m.hexdigest()


def base64_encode(data: str):
    return base64.b64encode(data.encode()).decode()


def get_signature(policy_dict: dict):
    policy_bytes = base64.b64encode(json.dumps(policy_dict).encode())
    h = hmac.new(OSS_ACCESS_KEY_SECRET.encode(), policy_bytes, hashlib.sha1)
    sign_result = base64.encodebytes(h.digest()).strip()
    return sign_result.decode()


def get_expiration(expire: int):
    now = datetime.datetime.now()
    expire_time = now + datetime.timedelta(seconds=expire)
    return expire_time.strftime("%Y-%m-%dT%H:%M:%SZ")


def get_oss_upload_params(
    ext: str,
    expire: int = 600,
    max_file_size: int = 10 * 1024 * 1024,
):
    host = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}"
    yymmdd = datetime.datetime.now().strftime("%Y%m%d")
    file_name = uuid.uuid4().hex
    key = f"upload/{yymmdd}/{file_name}.{ext}"
    url = f"{host}/{key}"

    policy_dict = {
        "expiration": get_expiration(expire),
        "conditions": [
            {"bucket": OSS_BUCKET_NAME},
            ["eq", "$key", key],
            ["content-length-range", 1, max_file_size],
        ],
    }
    policy = base64_encode(json.dumps(policy_dict))
    signature = get_signature(policy_dict)

    # callback_dict = {
    #     "callbackUrl": f"{BASE_URL}/api/oss/callback",
    #     "callbackBody": '{"code":200,"msg":"success","data":{"url": "' + url + '"}}',
    #     "callbackBodyType": "application/json",
    # }
    # callback = base64_encode(json.dumps(callback_dict))

    oss = Oss(
        OSSAccessKeyId=OSS_ACCESS_KEY_ID,
        key=key,
        policy=policy,
        # callback=callback,
        # success_action_status="204",
        signature=signature,
    )
    data = OssUploadData(
        oss=oss,
        host=host,
        url=url,
        max_file_size=max_file_size,
    )
    return data
