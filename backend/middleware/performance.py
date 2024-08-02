import time
from typing import NamedTuple

from django.db.models.sql.compiler import SQLCompiler

original_execute_sql = SQLCompiler.execute_sql


class ServerTimingMetric(NamedTuple):
    name: str
    duration: float | None = None
    description: str | None = None

    def __str__(self) -> str:
        if self.duration is None and self.description is None:
            return self.name
        if self.duration is None:
            return f'{self.name};desc="{self.description}"'
        if self.description is None:
            dur = self.duration * 1000
            return f"{self.name};dur={dur:.4f}"
        dur = self.duration * 1000
        return f'{self.name};dur={dur:.4f};desc="{self.description}"'


class ServerTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        db_time = 0.0
        query_count = 0

        def execute_sql(self: SQLCompiler, *args, **kwargs):
            nonlocal db_time
            nonlocal query_count
            start_time = time.perf_counter()
            result = original_execute_sql(self, *args, **kwargs)
            end_time = time.perf_counter()
            db_time += end_time - start_time
            query_count += 1
            return result

        SQLCompiler.execute_sql = execute_sql
        try:
            start_time = time.perf_counter()
            response = self.get_response(request)
            end_time = time.perf_counter()
        finally:
            SQLCompiler.execute_sql = original_execute_sql

        elapsed_time = end_time - start_time
        server_timing_metrics = [
            ServerTimingMetric(name="db", duration=db_time, description=f"Database (count: {query_count})"),
            ServerTimingMetric(name="resp", duration=elapsed_time, description="Response"),
        ]
        response["Server-Timing"] = ", ".join(str(metric) for metric in server_timing_metrics)
        return response
