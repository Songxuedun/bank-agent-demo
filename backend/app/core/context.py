"""请求级用户上下文: 工具函数通过 uid() 取当前登录用户，避免写死 current_user"""
from contextvars import ContextVar

_current_uid: ContextVar[str] = ContextVar("current_uid", default="")


def set_uid(user_id: str):
    return _current_uid.set(user_id)


def uid() -> str:
    value = _current_uid.get()
    if not value:
        raise RuntimeError("未登录: 没有设置当前用户")
    return value
