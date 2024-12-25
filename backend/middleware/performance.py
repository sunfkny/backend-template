import time
from typing import NamedTuple

from django.db.models.sql.compiler import SQLCompiler

from backend.utils.query_logger import QueryLogger

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
        with QueryLogger().execute_wrapper() as ql:
            start_time = time.perf_counter()
            response = self.get_response(request)
            end_time = time.perf_counter()

        response_duration = end_time - start_time
        db_duration = sum(i["duration"] for i in ql.queries)
        db_query_count = len(ql.queries)

        server_timing_metrics = [
            ServerTimingMetric(name="db", duration=db_duration, description=f"Database (count: {db_query_count})"),
            ServerTimingMetric(name="resp", duration=response_duration, description="Response"),
        ]
        response["Server-Timing"] = ", ".join(str(metric) for metric in server_timing_metrics)
        return response
