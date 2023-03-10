#!venv/bin/python
import os
from backend.settings import MEDIA_URL, UWSGI_INI_FILE_NAME, BASE_DIR, DOMAIN_NAME, MEDIA_ROOT, DIST_ROOT

if not UWSGI_INI_FILE_NAME:
    raise Exception("backend.settings.UWSGI_INI_FILE_NAME is not set")

UWSGI_INI_FILE_PATH = BASE_DIR / f"{UWSGI_INI_FILE_NAME}.ini"

run_file = BASE_DIR / "run.sh"

run_file.write_text(
    f"""source ./venv/bin/activate

procedure_name="{UWSGI_INI_FILE_NAME}.ini"
PROCESS=`ps -ef | grep $procedure_name | grep -v grep | awk '{{print $2}}'`

for i in $PROCESS
do
    kill -9 $i
done
sleep 0.5
uwsgi --ini $procedure_name
"""
)
run_file.chmod(0o755)

UWSGI_INI_FILE_PATH.write_text(
    f"""# uwsgi使用配置文件启动
[uwsgi]
# 指定项目的根目录
root={BASE_DIR}
# 指定依赖的虚拟环境
virtualenv=venv
# 指定项目的application
module=backend.wsgi:application
# 指定sock的文件路径
socket=uwsgi.sock
# 进程个数
workers=2
pidfile=uwsgi.pid
# 指定IP端口
# http=0.0.0.0:8011
# 启动uwsgi的用户名和用户组
uid=root
gid=root
# 启用主进程
master=true
# 自动移除unix Socket和pid文件当服务停止的时候
vacuum=true
# 序列化接受的内容，如果可能的话
thunder-lock=true
# 启用线程
threads=1
enable-threads=true
# 设置自中断时间
harakiri=60
http-timeout=30
socket-timeout=30
# 设置缓冲
post-buffering=8192
# 设置日志目录
daemonize=logs/run.log
# 日志格式
log-format-strftime = true
log-date = %%Y-%%m-%%d %%H:%%M:%%S
logformat=%(ftime) - %(addr) (%(proto) %(status)) %(method) %(uri) => generated %(size) bytes in %(msecs) msecs
# => generated %(size) bytes in %(msecs) msecs process 1 worker %(wid) core %(core)
# uwsgi日志中不再显示错误信息
ignore-sigpipe=true
ignore-write-errors=true
disable-write-exception=true
"""
)
if not (DIST_ROOT / MEDIA_URL).exists():
    os.symlink(MEDIA_ROOT, DIST_ROOT / MEDIA_URL)

print(
    f"""# ================== nginx config ==================
server {{
    listen 80;
    # listen 443 ssl http2;
    server_name {DOMAIN_NAME};

    # access_log /data/wwwlogs/{DOMAIN_NAME}.log combined;
    # ssl_certificate /usr/local/nginx/cert/{DOMAIN_NAME}.pem;
    # ssl_certificate_key /usr/local/nginx/cert/{DOMAIN_NAME}.key;

    set $base {BASE_DIR};

    # if ($ssl_protocol = "" ) {{
    #     return 301 https://$host$request_uri;
    # }}

    location /api {{
        include uwsgi_params;
        uwsgi_pass unix:$base/uwsgi.sock;
    }}
    location / {{
        alias $base/dist/;
    }}
}}
"""
)
