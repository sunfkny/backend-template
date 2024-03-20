__doc__ = """
使用方法
```python
@router.post("upload/params", summary="获取 POST Object 上传参数")
def post_upload_params(
    request: HttpRequest,
    ext: str = Form(..., description="文件后缀"),
):
    # [POST Object](https://cloud.tencent.com/document/product/436/14690)
    return Response.data(get_cos_upload_params(ext))
```
配置跨域
```python
from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError


COS_SECRET_ID = "..."
COS_SECRET_KEY = "..."
COS_BUCKET_APPID = "..."
COS_REGION = "..."
FORCE = False

config = CosConfig(Region=COS_REGION, SecretId=COS_SECRET_ID, SecretKey=COS_SECRET_KEY)
client = CosS3Client(config)

if FORCE:
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

COS_SECRET_ID = "..."
COS_SECRET_KEY = "..."
COS_BUCKET_APPID = "..."
COS_REGION = "..."
COS_ENDPOINT = "..."


class Cos(BaseModel):
    key: str
    policy: str
    sign_algorithm: str = "sha1"
    secret_id: str
    key_time: str
    signature: str

    def to_dict(self):
        return {
            "key": self.key,
            "policy": self.policy,
            "q-sign-algorithm": self.sign_algorithm,
            "q-ak": self.secret_id,
            "q-key-time": self.key_time,
            "q-signature": self.signature,
        }


class CosUploadData(BaseModel):
    host: str
    url: str
    max_file_size: int = 20 * 1024 * 1024
    cos: dict


def md5_encode(data: str):
    m = hashlib.md5()
    m.update(data.encode())
    return m.hexdigest()


def base64_encode(data: str):
    return base64.b64encode(data.encode()).decode()


def get_signature(key: str, msg: str):
    h = hmac.new(key.encode(), msg.encode(), hashlib.sha1)
    return h.hexdigest()


def sha1_encode(data: str):
    m = hashlib.sha1()
    m.update(data.encode())
    return m.hexdigest()


def get_expiration(expire: int):
    now = datetime.datetime.now()
    expire_time = now + datetime.timedelta(seconds=expire)
    return expire_time


def get_cos_upload_params(
    ext: str,
    expire: int = 600,
    max_file_size: int = 10 * 1024 * 1024,
):
    host = f"https://{COS_BUCKET_APPID}.{COS_ENDPOINT}"
    now = datetime.datetime.now()
    yymmdd = now.strftime("%Y%m%d")
    file_name = uuid.uuid4().hex
    key = f"upload/{yymmdd}/{file_name}.{ext}"
    url = f"{host}/{key}"

    expiration = get_expiration(expire)
    start_timestamp = int(now.timestamp())
    end_timestamp = int(expiration.timestamp())
    key_time = f"{start_timestamp};{end_timestamp}"

    policy_dict = {
        "expiration": expiration.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "conditions": [
            {"bucket": COS_BUCKET_APPID},
            ["eq", "$key", key],
            ["content-length-range", 1, max_file_size],
            {"q-sign-algorithm": "sha1"},
            {"q-ak": COS_SECRET_ID},
            {"q-sign-time": key_time},
        ],
    }
    policy = json.dumps(policy_dict)
    sign_key = get_signature(COS_SECRET_KEY, key_time)
    string_to_sign = sha1_encode(policy)
    signature = get_signature(sign_key, string_to_sign)

    cos = Cos(
        key=key,
        policy=base64_encode(policy),
        signature=signature,
        sign_algorithm="sha1",
        secret_id=COS_SECRET_ID,
        key_time=key_time,
    )
    data = CosUploadData(
        cos=cos.to_dict(),
        host=host,
        url=url,
        max_file_size=max_file_size,
    )
    return data
