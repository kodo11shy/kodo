from typing import Any

from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, message: str, code: int = 40000, status_code: int = 400) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code


def ok(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"code": 0, "data": data if data is not None else {}, "message": message}


def fail(message: str, code: int = 40000, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "data": None, "message": message},
    )


def abort(message: str, code: int = 40000, status_code: int = 400) -> None:
    raise ApiError(message=message, code=code, status_code=status_code)
