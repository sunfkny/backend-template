import time
from contextlib import contextmanager
from typing import TypedDict

from django.db import connection


class QueryData(TypedDict):
    sql: str
    params: tuple
    many: bool
    status: str
    exception: str | None
    duration: float


class QueryLogger:
    def __init__(self):
        self.queries: list[QueryData] = []

    def __repr__(self) -> str:
        return f"QueryLogger(queries={repr(self.queries)})"

    def __call__(self, execute, sql, params, many, context):
        current_query: QueryData = {
            "sql": sql,
            "params": params,
            "many": many,
            "status": "unknown",
            "exception": None,
            "duration": 0,
        }
        start = time.perf_counter()
        try:
            result = execute(sql, params, many, context)
        except Exception as e:
            current_query["status"] = "error"
            current_query["exception"] = repr(e)
            raise
        else:
            current_query["status"] = "ok"
            return result
        finally:
            duration = time.perf_counter() - start
            current_query["duration"] = duration
            self.queries.append(current_query)

    @contextmanager
    def execute_wrapper(self):
        with connection.execute_wrapper(self):
            yield self
