from pydantic import BaseModel, Field


class CentroCustoCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    nome: str = Field(..., min_length=1, max_length=200)
    descricao: str | None = None
    id_pai: int | None = None


class CentroCustoRead(CentroCustoCreate):
    id: int
    ativo: bool

    model_config = {"from_attributes": True}
