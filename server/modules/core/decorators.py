import functools

from fastapi import HTTPException


def http_exception(status_code, detail):
    def http_exception_decorator(func):
        @functools.wraps(func)
        async def inner(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException as e:
                raise e
            except Exception:
                raise HTTPException(status_code=status_code, detail=detail)
        return inner
    return http_exception_decorator
