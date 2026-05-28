"""
Gestão de usuários — acesso restrito a ADMIN.

  GET    /usuarios/         — lista todos
  POST   /usuarios/         — cria novo usuário
  GET    /usuarios/{id}     — detalhe
  PUT    /usuarios/{id}     — edita nome/perfil/ativo
  DELETE /usuarios/{id}     — desativa (nunca deleta)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.auth.deps import get_current_user, require_admin
from api.auth.security import hash_senha
from api.db import get_db
from api.models.usuario import PerfilUsuario, Usuario
from api.schemas.usuario import UsuarioCreate, UsuarioRead, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


def _get_or_404(usuario_id: int, db: Session) -> Usuario:
    u = db.get(Usuario, usuario_id)
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return u


@router.get("/", response_model=list[UsuarioRead])
def listar_usuarios(
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UsuarioRead]:
    return db.query(Usuario).order_by(Usuario.nome).all()


@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    payload: UsuarioCreate,
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioRead:
    if db.query(Usuario).filter(Usuario.email == payload.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )
    novo = Usuario(
        nome=payload.nome,
        email=payload.email.lower(),
        senha_hash=hash_senha(payload.senha),
        perfil=payload.perfil,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return UsuarioRead.model_validate(novo)


@router.get("/{usuario_id}", response_model=UsuarioRead)
def obter_usuario(
    usuario_id: int,
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioRead:
    return UsuarioRead.model_validate(_get_or_404(usuario_id, db))


@router.put("/{usuario_id}", response_model=UsuarioRead)
def atualizar_usuario(
    usuario_id: int,
    payload: UsuarioUpdate,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioRead:
    u = _get_or_404(usuario_id, db)

    # Impede que o admin remova seu próprio perfil ADMIN sem outro admin ativo
    if u.id == admin.id and payload.perfil and payload.perfil != PerfilUsuario.ADMIN:
        outros_admins = (
            db.query(Usuario)
            .filter(
                Usuario.perfil == PerfilUsuario.ADMIN,
                Usuario.ativo == True,
                Usuario.id != admin.id,
            )
            .count()
        )
        if outros_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não é possível remover o único Admin ativo do sistema",
            )

    if payload.nome is not None:
        u.nome = payload.nome
    if payload.perfil is not None:
        u.perfil = payload.perfil
    if payload.ativo is not None:
        # Impede auto-desativação sem outro admin
        if u.id == admin.id and payload.ativo is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Você não pode desativar sua própria conta",
            )
        u.ativo = payload.ativo

    db.commit()
    db.refresh(u)
    return UsuarioRead.model_validate(u)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_usuario(
    usuario_id: int,
    admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    u = _get_or_404(usuario_id, db)
    if u.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Você não pode desativar sua própria conta",
        )
    u.ativo = False
    db.commit()
