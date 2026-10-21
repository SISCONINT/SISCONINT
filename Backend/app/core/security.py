import hashlib
import secrets
import time
import redis
from functools import lru_cache

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from flask import current_app

_hasher = PasswordHasher()  # argon2id con parámetros recomendados


# ---------------------------------------------------------------- lista de jti revocados (HU_04)
class _MemoryBlocklist:
    """Reserva para pruebas y entornos sin Redis. TTL igual que en Redis."""

    def __init__(self):
        self._store: dict[str, float] = {}
        self._user_gen: dict[str, tuple[int, float]] = {}  # user_id -> (generación, vence)

    def add(self, jti: str, ttl: int) -> None:
        self._store[jti] = time.time() + max(1, ttl)

    def contains(self, jti: str) -> bool:
        expires_at = self._store.get(jti)
        if expires_at is None:
            return False
        if expires_at < time.time():
            del self._store[jti]
            return False
        return True

    def bump_user(self, user_id: int, ttl: int) -> int:
        key = str(user_id)
        current, expires_at = self._user_gen.get(key, (0, 0.0))
        if expires_at < time.time():
            current = 0
        nxt = current + 1
        self._user_gen[key] = (nxt, time.time() + max(1, ttl))
        return nxt

    def user_generation(self, user_id: int) -> int:
        entry = self._user_gen.get(str(user_id))
        if entry is None:
            return 0
        gen, expires_at = entry
        if expires_at < time.time():
            del self._user_gen[str(user_id)]
            return 0
        return gen


class _RedisBlocklist:
    """Arquitectura 3.4: jti revocados en Redis (logout, cambio de rol, etc.)."""

    def __init__(self, url: str):

        self._redis = redis.Redis.from_url(url, decode_responses=True)

    def add(self, jti: str, ttl: int) -> None:
        self._redis.set(f"jwt:revoked:{jti}", "1", ex=max(1, ttl))

    def contains(self, jti: str) -> bool:
        return self._redis.get(f"jwt:revoked:{jti}") is not None

    def bump_user(self, user_id: int, ttl: int) -> int:
        key = f"jwt:ugen:{user_id}"
        val = int(self._redis.incr(key))
        self._redis.expire(key, max(1, ttl))
        return val

    def user_generation(self, user_id: int) -> int:
        val = self._redis.get(f"jwt:ugen:{user_id}")
        return int(val) if val else 0


def init_token_blocklist(app) -> None:
    url = (app.config.get("REDIS_URL") or "").strip()
    if app.config.get("TESTING") or not url:
        app.extensions["token_blocklist"] = _MemoryBlocklist()
    else:
        app.extensions["token_blocklist"] = _RedisBlocklist(url)


def revoke_jti(jti: str, ttl_seconds: int) -> None:
    if not jti:
        return
    current_app.extensions["token_blocklist"].add(jti, ttl_seconds)


def jti_is_revoked(jti: str) -> bool:
    if not jti:
        return False
    store = current_app.extensions.get("token_blocklist")
    return bool(store and store.contains(jti))


def bump_user_generation(user_id: int, ttl_seconds: int) -> int:
    """Invalida todas las sesiones vigentes del colaborador (cambio de rol, HU_08)."""
    return current_app.extensions["token_blocklist"].bump_user(user_id, ttl_seconds)


def user_generation(user_id: int) -> int:
    store = current_app.extensions.get("token_blocklist")
    if not store:
        return 0
    return store.user_generation(user_id)


def user_tokens_revoked(user_id: int, token_generation: int) -> bool:
    return token_generation < user_generation(user_id)


# ---------------------------------------------------------------- tokens de un solo uso
def generate_token(nbytes: int = 32) -> tuple[str, str]:
    """Devuelve (token_en_claro, hash_sha256). Solo el hash se guarda en la base."""
    raw = secrets.token_urlsafe(nbytes)
    return raw, hash_token(raw)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- contraseñas
def hash_password(password: str) -> str:
    return _hasher.hash(password)


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return _hasher.hash("hash-ficticio-para-igualar-tiempos")


def verify_password(stored_hash: str | None, password: str) -> bool:
    """True si la contraseña coincide. Nunca lanza.

    Si no hay hash (correo inexistente o cuenta sin contraseña) verifica contra uno ficticio:
    así el tiempo de respuesta no revela qué correos existen.
    """
    if not stored_hash:
        try:
            _hasher.verify(_dummy_hash(), password)
        except (VerificationError, InvalidHashError):
            pass
        return False
    try:
        return _hasher.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_policy_errors(password: str, correo: str | None = None) -> list[str]:
    """RG-05: mínimo 10 caracteres, mayúscula, minúscula, número y símbolo; distinta del correo."""
    errors: list[str] = []
    if len(password) < 10:
        errors.append("Mínimo 10 caracteres")
    if not any(c.isupper() for c in password):
        errors.append("Debe incluir una mayúscula")
    if not any(c.islower() for c in password):
        errors.append("Debe incluir una minúscula")
    if not any(c.isdigit() for c in password):
        errors.append("Debe incluir un número")
    if not any(not c.isalnum() and not c.isspace() for c in password):
        errors.append("Debe incluir un símbolo")
    if correo and password.strip().lower() == correo.strip().lower():
        errors.append("No puede ser igual al correo")
    return errors