"""
Utilitários de segurança: hash de senha e tokens JWT.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from api.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    return _pwd_context.hash(senha)


def verificar_senha(senha: str, hash: str) -> bool:
    return _pwd_context.verify(senha, hash)


def criar_token(payload: dict) -> str:
    settings = get_settings()
    dados = payload.copy()
    expira = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    dados["exp"] = expira
    return jwt.encode(dados, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def decodificar_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.app_secret_key, algorithms=[settings.jwt_algorithm])
