import json
import logging
from typing import Dict
from backend.settings import get_logger
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = get_logger("request")


class ApiLoggingMiddleware(MiddlewareMixin):
    @staticmethod
    def _safe_loads_dict(body) -> Dict:
        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                data = {"__root__": data}
            return data
        except:
            return {}

    @staticmethod
    def _get_request_params(request: HttpRequest) -> Dict:
        data = {}
        if request.method == "GET":
            data.update(request.GET.dict())
        else:
            data.update(request.POST.dict())
            request_content_type = request.headers.get("Content-Type", "")
            if "application/json" in request_content_type:
                data.update(ApiLoggingMiddleware._safe_loads_dict(request.body))

        return data

    def process_response(self, request: HttpRequest, response: HttpResponse):
        data = ApiLoggingMiddleware._get_request_params(request)
        request_content_type = request.headers.get("Content-Type", "")
        logger.info(f"{request.method} {request.path} {response.status_code} {response.reason_phrase}")
        if data:
            logger.info(f"{request_content_type} {data}")

        response_content_type = response.headers.get("Content-Type", "")
        if "application/json" in response_content_type and not request.path.endswith("openapi.json"):
            logger.info("{} {}", response_content_type, response.content.decode("unicode_escape").replace("\n", " "))
        elif "text/html" in response_content_type or "text/javascript" in response_content_type:
            logger.info(response_content_type)
        elif "utf-8" in response_content_type:
            logger.info("{} {}", response_content_type, response.content.decode().replace("\n", " "))
        else:
            logger.info(response_content_type, response.content[:32])

        return response
