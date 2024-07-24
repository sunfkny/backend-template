from django.core.paginator import Paginator
from django.http import HttpRequest
from ninja import Body, Form, Header, Query, Router

from backend.settings import get_logger
from backend.utils.ip_utils import get_client_ip
from backend.utils.response_types import Response

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

    return Response.data(
        {
            "db": db_status,
            "redis": redis_status,
            "migrations": migrations_status,
        }
    )
