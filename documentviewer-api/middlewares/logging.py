import time
from typing import Any

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.config import config


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        request_data = await self._extract_request_data(request)

        logger.info(
            "Incoming request: {method} {path}",
            method=request.method,
            path=request.url.path,
            **request_data,
        )

        try:
            response = await call_next(request)

            process_time = time.time() - start_time

            logger.info(
                "Response: {status_code} for {method} {path} in {process_time:.3f}s",
                status_code=response.status_code,
                method=request.method,
                path=request.url.path,
                process_time=process_time,
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed: {method} {path} - {error}",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=process_time,
                exc_info=True,
            )
            raise

    async def _extract_request_data(self, request: Request) -> dict[str, Any]:
        data = {
            "user_agent": request.headers.get("referer"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
        }
        if config.MODE == "DEV":
            data.update(
                {
                    "query_params": dict(request.query_params),
                    "path_params": dict(request.path_params),
                }
            )

        return data
