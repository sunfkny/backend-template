import ast
import pathlib
import shlex
import sys

from django.core.management.utils import get_random_secret_key

import backend.settings
from backend.settings import BASE_DIR, DOMAIN_NAME


def check_domain_name(d: str):
    if not d:
        raise Exception("backend.settings.DOMAIN_NAME is not set")


check_domain_name(DOMAIN_NAME)

UWSGI_INI_FILE_NAME = DOMAIN_NAME + ".ini"
UWSGI_INI_FILE_PATH = BASE_DIR / UWSGI_INI_FILE_NAME
if UWSGI_INI_FILE_PATH.exists():
    raise Exception(f"{UWSGI_INI_FILE_PATH} already exists")

settings_path = pathlib.Path(backend.settings.__file__)
settings_source = settings_path.read_text()


class SettingsTransformer(ast.NodeTransformer):
    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0]
            if target.id == "SECRET_KEY":
                node.value = ast.Constant(value=get_random_secret_key())
            elif target.id == "DEBUG":
                node.value = ast.Constant(value=False)
        return node


settings_tree = ast.parse(settings_source)
settings_tree = SettingsTransformer().visit(settings_tree)
settings_tree = ast.fix_missing_locations(settings_tree)

settings_path.write_text(ast.unparse(settings_tree))

python = pathlib.Path(sys.executable)
scripts = python.parent.relative_to(BASE_DIR)
venv = scripts.parent
uwsgi = scripts / "uwsgi"

run_file = BASE_DIR / "run.sh"
run_file.write_text(
    f"""set -e

cd "{BASE_DIR}"

{python} manage.py check

if [ -e uwsgi.pid ]; then
    kill -9 `cat uwsgi.pid` || rm uwsgi.pid
fi

{uwsgi} --ini {shlex.quote(str(UWSGI_INI_FILE_PATH))}
"""
)
run_file.chmod(0o755)


reload_file = BASE_DIR / "reload.sh"
reload_file.write_text(f"""set -e

cd "{BASE_DIR}"

{python} manage.py check

touch uwsgi.reload

tail -F -n0 logs/run.log | while read line; do
    echo "$line"
    if [[ "$line" == *"chain reloading complete"* ]]; then
        break
    fi
done
""")
reload_file.chmod(0o755)


UWSGI_INI_FILE_PATH.write_text(
    f"""; uwsgi使用配置文件启动
[uwsgi]
; 指定项目的根目录
chdir={BASE_DIR}
; 指定依赖的虚拟环境
venv={venv}
; 指定项目的application
module=backend.wsgi:application
; uwsgi 协议
uwsgi-socket=uwsgi.sock
; http 协议
; http-socket=127.0.0.1:8000
; 进程个数
workers=2
pidfile=uwsgi.pid
; 启动uwsgi的用户名和用户组
uid=root
gid=root
; 启用主进程
master=true
; 退出时尝试删除所有生成的socket和pid文件
vacuum=true
; 加锁串行化接收, 避免多进程惊群问题
thunder-lock=true
; 启用线程
threads=1
enable-threads=true
; 设置自中断时间
harakiri=60
http-timeout=30
socket-timeout=30
; 设置缓冲
post-buffering=8192
; 设置日志目录
daemonize=logs/run.log
; touch触发重新打开日志
touch-logreopen=logs/run.log.logreopen
; touch触发重启
; touch-reload=uwsgi.reload
; touch触发优雅链式重启
lazy-apps=true
touch-chain-reload=uwsgi.reload
; 使用 x-forwarded-for 记录ip
; log-x-forwarded-for=true
; 禁用请求日志
; disable-logging = true
; 日志格式
log-format-strftime = true
log-date=%%Y-%%m-%%d %%H:%%M:%%S
logformat=%(ftime)     | INFO     | %(addr) (%(proto) %(status)) %(method) %(uri) => generated %(size) bytes in %(msecs) msecs
; uwsgi日志中不显示错误信息
ignore-sigpipe=true
ignore-write-errors=true
disable-write-exception=true
"""
)
