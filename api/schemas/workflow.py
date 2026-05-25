from datetime import datetime
from pydantic import BaseModel


class WorkflowEnviar(BaseModel):
    id_versao: int
    id_empresa: int
    enviado_por: str


class WorkflowAprovar(BaseModel):
    id_workflow: int
    aprovado_por: str
    comentario: str | None = None


class WorkflowReprovar(BaseModel):
    id_workflow: int
    reprovado_por: str
    comentario: str


class WorkflowRead(BaseModel):
    id: int
    id_versao: int
    id_empresa: int
    status: str
    criado_por: str
    enviado_por: str | None
    aprovado_por: str | None
    reprovado_por: str | None
    data_envio: datetime | None
    data_decisao: datetime | None
    comentario: str | None

    model_config = {"from_attributes": True}
