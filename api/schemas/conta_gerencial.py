from pydantic import BaseModel, Field
from typing import Literal


class ContaGerencialCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    nome: str = Field(..., min_length=1, max_length=200)
    tipo: Literal["RECEITA", "DESPESA", "ATIVO", "PASSIVO", "RESULTADO"]
    natureza: Literal["DEVEDORA", "CREDORA"]
    id_pai: int | None = None
    nivel: int = Field(default=1, ge=1, le=10)
    aceita_lancamento: bool = True


class ContaGerencialRead(ContaGerencialCreate):
    id: int
    ativa: bool

    model_config = {"from_attributes": True}
