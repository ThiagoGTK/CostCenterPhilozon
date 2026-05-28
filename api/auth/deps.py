"""
Dependências FastAPI para autenticação e autorização.

Uso nos routers:
  # Qualquer usuário autenticado
  usuario = Depends(get_current_user)

  # Somente ADMIN ou GESTOR (escrita operacional)
  usuario = Depends(require_admin_ou_gestor)

  # Somente ADMIN (gestão de usuários)
  usuario = Depends(require_admin)
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from api.auth.security import decodificar_token
from api.db import get_db
from api.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credencial_invalida = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodificar_token(token)
        usuario_id: int | None = payload.get("sub")
        if usuario_id is None:
            raise credencial_invalida
    except JWTError:
        raise credencial_invalida

    usuario = db.get(Usuario, int(usuario_id))
    if not usuario or not usuario.ativo:
        raise credencial_invalida
    return usuario


def require_admin(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.perfil != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return usuario


def require_admin_ou_gestor(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.perfil not in ("ADMIN", "GESTOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a Gestores e Administradores",
        )
    return usuario
