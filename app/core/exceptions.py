from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppException(Exception):
    """공통 에러 응답 형식 {detail, error_code}을 강제하는 애플리케이션 예외."""

    def __init__(self, status_code: int, detail: str, error_code: str) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class NotFoundError(AppException):
    def __init__(self, detail: str = "리소스를 찾을 수 없습니다.", error_code: str = "RESOURCE_NOT_FOUND") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, error_code)


class ConflictError(AppException):
    def __init__(self, detail: str, error_code: str = "CONFLICT") -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, error_code)


class ForbiddenError(AppException):
    def __init__(self, detail: str = "권한이 없습니다.", error_code: str = "FORBIDDEN") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, error_code)


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "인증이 필요합니다.", error_code: str = "UNAUTHORIZED") -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, error_code)


class BadRequestError(AppException):
    def __init__(self, detail: str, error_code: str = "BAD_REQUEST") -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, error_code)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error_code": exc.error_code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "error_code": "VALIDATION_ERROR"},
        )
