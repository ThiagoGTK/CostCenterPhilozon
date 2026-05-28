from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from api.models.usuario import PerfilUsuario


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    perfil: str = PerfilUsuario.COLABORADOR

    @field_validator("perfil")
    @classmethod
    def perfil_valido(cls, v: str) -> str:
        if v not in PerfilUsuario.TODOS:
            raise ValueError(f"Perfil inválido. Use: {PerfilUsuario.TODOS}")
        return v

    @field_validator("senha")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("A senha deve ter no mínimo 6 caracteres")
        return v


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    perfil: str | None = None
    ativo: bool | None = None

    @field_validator("perfil")
    @classmethod
    def perfil_valido(cls, v: str | None) -> str | None:
        if v is not None and v not in PerfilUsuario.TODOS:
            raise ValueError(f"Perfil inválido. Use: {PerfilUsuario.TODOS}")
        return v


class UsuarioRead(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime

    model_config = {"from_attributes": True}


class AlterarSenha(BaseModel):
    senha_atual: str
    senha_nova: str

    @field_validator("senha_nova")
    @classmethod
    def senha_minima(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("A senha deve ter no mínimo 6 caracteres")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioRead
