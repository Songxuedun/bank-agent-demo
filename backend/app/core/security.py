"""密码哈希与登录令牌(仅用标准库，不引入新依赖)"""
import base64
import hashlib
import hmac
import secrets
import time
from typing import Optional

from app.core.config import settings

_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), _ITERATIONS)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def _sign(payload: str) -> str:
    return hmac.new(settings.token_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_token(user_id: str) -> str:
    exp = int(time.time()) + settings.token_ttl_seconds
    payload = base64.urlsafe_b64encode(f"{user_id}|{exp}".encode()).decode()
    return f"{payload}.{_sign(payload)}"


def parse_token(token: str) -> Optional[str]:
    """返回 user_id；令牌无效或过期返回 None"""
    try:
        payload, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, _sign(payload)):
            return None
        user_id, exp = base64.urlsafe_b64decode(payload.encode()).decode().rsplit("|", 1)
        return user_id if int(exp) >= time.time() else None
    except Exception:
        return None
