from contextlib import contextmanager
from functools import wraps

from django.db.models.sql.compiler import SQLCompiler

from backend.settings import get_logger
from backend.utils.timer import Timer

original_execute_sql = SQLCompiler.execute_sql


@contextmanager
def slow_query(long_query_time: float):
    @wraps(original_execute_sql)
    def execute_sql(self: SQLCompiler, *args, **kwargs):
        with Timer() as timer:
            ret = original_execute_sql(self, *args, **kwargs)
        if timer >= long_query_time:
            alias = self.connection.alias
            sql, args = self.as_sql()
            statement = sql % args
            get_logger("slow_query").info(f"{alias} ({timer}) {statement}")

        return ret

    # monkey patching the SQLCompiler
    SQLCompiler.execute_sql = execute_sql

    yield  # execute code in the `with` statement

    # restore original execute_sql
    SQLCompiler.execute_sql = original_execute_sql


def slow_query_decorator(long_query_time: float):
    def wrapper(func):
        @wraps(func)
        def wrapped(*fargs, **fkwargs):
            with slow_query(long_query_time=long_query_time):
                return func(*fargs, **fkwargs)

        return wrapped

    return wrapper
