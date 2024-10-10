import os
import platform
import sys
from typing import Any

import psutil
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import HttpRequest
from ninja import Body, Form, Header, Query, Router

from backend.response import D, L, Response
from backend.settings import get_logger
from backend.utils.ip_utils import get_client_ip

router = Router(tags=["common"])

logger = get_logger()


@router.get("ping")
def get_ping(
    request: HttpRequest,
):
    return Response.success("pong")


@router.get("ip")
def get_ip(
    request: HttpRequest,
):
    data = {
        "ip": get_client_ip(request),
    }
    return Response.data(data)


@router.get("status")
def get_status(
    request: HttpRequest,
):
    redis_status = False
    try:
        from backend.settings import get_redis_connection

        redis_conn = get_redis_connection()
        redis_status = redis_conn.ping()
    except Exception as e:
        logger.error(e)
        redis_status = str(e)

    db_status = False
    try:
        from django.db import close_old_connections, connections

        close_old_connections()

        db_conn = connections["default"]
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            value = cursor.fetchone()
            db_status = value == (1,)
    except Exception as e:
        logger.error(e)
        db_status = str(e)

    migrations_status = False
    try:
        from django.db import connections
        from django.db.migrations.executor import MigrationExecutor

        executor = MigrationExecutor(connections["default"])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            logger.error(f"There are {len(plan)} migrations to apply")
        else:
            migrations_status = True

    except Exception as e:
        logger.error(e)
        migrations_status = str(e)

    return Response.data(
        {
            "db": db_status,
            "redis": redis_status,
            "migrations": migrations_status,
        }
    )


@router.get("system/info")
@staff_member_required
def get_system_info(request: HttpRequest):
    os_data = {
        "name": os.name,
        "getcwd": os.getcwd(),
        "getpid": os.getpid(),
        "cpu_count": os.cpu_count(),
        "getloadavg": os.getloadavg(),
    }

    sys_data = {
        "version_info": {
            "major": sys.version_info.major,
            "minor": sys.version_info.minor,
            "micro": sys.version_info.micro,
            "releaselevel": sys.version_info.releaselevel,
            "serial": sys.version_info.serial,
        },
        "platform": sys.platform,
        "version": sys.version,
    }

    platform_data: dict[str, Any] = {
        "machine": platform.machine(),
        "node": platform.node(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }
    if sys.platform == "win32":
        platform_data["win32_ver"] = " ".join(platform.win32_ver())
        platform_data["win32_edition"] = platform.win32_edition()
    if sys.platform == "linux":
        platform_data["libc_ver"] = " ".join(platform.libc_ver())
        try:
            platform_data["freedesktop_os_release"] = platform.freedesktop_os_release()
        except Exception:
            pass
    if sys.platform == "darwin":
        platform_data["mac_ver"] = " ".join(platform.mac_ver())

    psutil_data = {
        "cpu_percent": psutil.cpu_percent(),
        "cpu_count": psutil.cpu_count(),
        "cpu_freq": psutil.cpu_freq().current,
        "swap_memory": psutil.swap_memory()._asdict(),
        "virtual_memory": psutil.virtual_memory()._asdict(),
        "net_io_counters": psutil.net_io_counters()._asdict(),
        "boot_time": psutil.boot_time(),
        "disk_partitions": [
            {
                "disk_partition": disk_partition._asdict(),
                "disk_usage": psutil.disk_usage(disk_partition.mountpoint)._asdict(),
            }
            for disk_partition in psutil.disk_partitions()
        ],
    }

    data = {
        "os": os_data,
        "sys": sys_data,
        "platform": platform_data,
        "psutil": psutil_data,
    }

    try:
        import uwsgi  # type: ignore

        data["uwsgi"] = {
            "masterpid": uwsgi.masterpid(),
            "version": uwsgi.version.decode(),
            "hostname": uwsgi.hostname.decode(),
            "numproc": uwsgi.numproc,
            "started_on": uwsgi.started_on,
        }
    except Exception:
        pass

    return Response.data(data)
