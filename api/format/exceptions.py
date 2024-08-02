from typing import Any, Optional, Dict

from fastapi import status
from fastapi import HTTPException
from starlette.responses import JSONResponse

from api.format.error_schema import ErrorSchema


async def http_exception_handler(request, exc):
    content = ErrorSchema(status=exc.status_code, message=exc.detail).model_dump(mode='json')
    return JSONResponse(content, status_code=exc.status_code)


class AuthError(HTTPException):
    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, headers)


class BadRequestError(HTTPException):
    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status. HTTP_400_BAD_REQUEST, detail, headers)


class NotFoundError(HTTPException):
    def __init__(
        self, detail: Any = None, headers: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, headers)
