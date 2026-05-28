"""
Endpoints de autenticação.

  POST /auth/login   — recebe email+senha, retorna JWT
  GET  /auth/me      — retorna o usuário logado
  POST /auth/alterar-senha — troca a senha do próprio usuário
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.auth.deps import get_current_user
from api.auth.security import criar_token, hash_senha, verificar_senha
from api.db import get_db
from api.models.usuario import Usuario
from api.schemas.usuario import AlterarSenha, LoginRequest, TokenResponse, UsuarioRead

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == payload.email.lower())
        .first()
    )
    if not usuario or not verificar_senha(payload.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
        )
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado. Contate o administrador.",
        )
    token = criar_token({"sub": str(usuario.id), "perfil": usuario.perfil})
    return TokenResponse(
        access_token=token,
        usuario=UsuarioRead.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioRead)
def me(usuario: Usuario = Depends(get_current_user)) -> UsuarioRead:
    return UsuarioRead.model_validate(usuario)


@router.post("/alterar-senha", status_code=status.HTTP_204_NO_CONTENT)
def alterar_senha(
    payload: AlterarSenha,
    usuario: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not verificar_senha(payload.senha_atual, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta",
        )
    usuario.senha_hash = hash_senha(payload.senha_nova)
    db.commit()
