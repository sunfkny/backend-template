import pathlib
import shlex

from django.core.management.utils import get_random_secret_key

from backend.settings import BASE_DIR, DOMAIN_NAME

if not DOMAIN_NAME:
    raise Exception("backend.settings.DOMAIN_NAME is not set")

secret_key = get_random_secret_key()
source = pathlib.Path("./backend/settings.py").read_text()
if 'SECRET_KEY = "django-insecure"' in source:
    source = source.replace('SECRET_KEY = "django-insecure"', f'SECRET_KEY = "{secret_key}"')
    source = source.replace("DEBUG = True", "DEBUG = False")
    pathlib.Path("./backend/settings.py").write_text(source)

UWSGI_INI_FILE_NAME = f"{DOMAIN_NAME}.ini"
UWSGI_INI_FILE_PATH = BASE_DIR / UWSGI_INI_FILE_NAME

if UWSGI_INI_FILE_PATH.exists():
    raise Exception(f"{UWSGI_INI_FILE_PATH} already exists")

run_file = BASE_DIR / "run.sh"
run_file.write_text(
    f"""source ./venv/bin/activate

if [ -f uwsgi.pid ]; then
    kill -9 `cat uwsgi.pid` || rm uwsgi.pid
fi

uwsgi --ini {shlex.quote(str(UWSGI_INI_FILE_PATH))}
"""
)
run_file.chmod(0o755)


reload_file = BASE_DIR / "reload.sh"
reload_file.write_text("touch uwsgi.reload\n")
reload_file.chmod(0o755)

UWSGI_INI_FILE_PATH.write_text(
    f"""# uwsgi使用配置文件启动
[uwsgi]
# 指定项目的根目录
chdir={BASE_DIR}
# 指定依赖的虚拟环境
venv=venv
# 指定项目的application
module=backend.wsgi:application
# uwsgi 协议
uwsgi-socket=uwsgi.sock
# http 协议
# http-socket=0.0.0.0:8011
# 进程个数
workers=2
pidfile=uwsgi.pid
# 启动uwsgi的用户名和用户组
uid=root
gid=root
# 启用主进程
master=true
# 退出时尝试删除所有生成的socket和pid文件
vacuum=true
# 加锁串行化接收, 避免多进程惊群问题
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
# touch触发重新打开日志
touch-logreopen=logs/run.log.logreopen
# touch触发重启
# touch-reload=uwsgi.reload
# touch触发优雅链式重启
lazy-apps=true
touch-chain-reload=uwsgi.reload
# 使用 x-forwarded-for 记录ip
# log-x-forwarded-for=true
# 禁用请求日志
# disable-logging = true
# 日志格式
log-format-strftime = true
log-date=%%Y-%%m-%%d %%H:%%M:%%S
logformat=%(ftime)     | INFO     | %(addr) (%(proto) %(status)) %(method) %(uri) => generated %(size) bytes in %(msecs) msecs
# uwsgi日志中不显示错误信息
ignore-sigpipe=true
ignore-write-errors=true
disable-write-exception=true
"""
)

print(
    f"""# ================== nginx config ==================
# /etc/nginx/conf.d/{DOMAIN_NAME}.conf

server {{
    listen 80;
    # listen 443 ssl http2;
    server_name {DOMAIN_NAME};

    access_log /var/log/nginx/{DOMAIN_NAME}_nginx.log combined;
    # ssl_certificate /etc/nginx/ssl/{DOMAIN_NAME}.pem;
    # ssl_certificate_key /etc/nginx/ssl/{DOMAIN_NAME}.key;

    set $base {BASE_DIR};

    # if ($ssl_protocol = "" ) {{
    #     return 301 https://$host$request_uri;
    # }}

    location /api {{
        include uwsgi_params;
        uwsgi_pass unix:$base/uwsgi.sock;
    }}
    location /media/ {{
        alias $base/media/;
    }}
    location / {{
        root $base/dist/;
        # try_files $uri $uri/ /index.html;
    }}
}}
"""
)

print(
    f"""
# ================== logrotate ==================
# /etc/logrotate.d/{DOMAIN_NAME}

{BASE_DIR / 'logs/*.log'} {{
    daily
    rotate 14
    createolddir
    olddir old
    missingok
    dateext
    compress
    notifempty
    sharedscripts
    postrotate
      touch {BASE_DIR / 'logs/run.log.logreopen'}
    endscript
}}
"""
)
