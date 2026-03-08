import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
PBKDF2_PREFIX = 'pbkdf2_sha256'


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode('utf-8').rstrip('=')


def _b64_decode(raw: str) -> bytes:
    padding = '=' * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + padding)


def _pbkdf2_hash(password: str, iterations: int = 390000) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f'{PBKDF2_PREFIX}${iterations}${_b64_encode(salt)}${_b64_encode(digest)}'


def _pbkdf2_verify(password: str, encoded: str) -> bool:
    try:
        prefix, iterations_raw, salt_raw, digest_raw = encoded.split('$', 3)
        if prefix != PBKDF2_PREFIX:
            return False
        iterations = int(iterations_raw)
        salt = _b64_decode(salt_raw)
        expected = _b64_decode(digest_raw)
    except Exception:
        return False

    actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return hmac.compare_digest(actual, expected)


def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception:
        # Fallback if bcrypt backend is unavailable in deployment.
        return _pbkdf2_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith(f'{PBKDF2_PREFIX}$'):
        return _pbkdf2_verify(plain_password, hashed_password)

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expires_minutes)
    payload = {'sub': subject, 'exp': expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return str(payload.get('sub'))
    except JWTError:
        return None