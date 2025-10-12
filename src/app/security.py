import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Optional

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ACCESS_TOKEN_TTL = int(os.getenv("ACCESS_TOKEN_TTL", "3600"))


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _b64urldecode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000, dklen=32)
    return _b64url(salt) + "." + _b64url(dk)


def verify_password(password: str, stored: str) -> bool:
    try:
        s_salt, s_hash = stored.split(".")
        salt = _b64urldecode(s_salt)
        good = _b64urldecode(s_hash)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000, dklen=32)
        return hmac.compare_digest(dk, good)
    except Exception:
        return False


def create_token(sub: int, role: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": sub, "role": role, "exp": int(time.time()) + ACCESS_TOKEN_TTL}
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    msg = f"{h}.{p}".encode()
    sig = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).digest()
    return f"{h}.{p}.{_b64url(sig)}"


def verify_token(token: str) -> Optional[Dict]:
    try:
        h, p, s = token.split(".")
        msg = f"{h}.{p}".encode()
        sig = _b64urldecode(s)
        good = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, good):
            return None
        payload = json.loads(_b64urldecode(p))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
