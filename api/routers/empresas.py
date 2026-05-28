from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.auth.deps import get_current_user
from api.db import get_db
from api.models.dimensoes import DimEmpresa
from api.models.usuario import Usuario
from pydantic import BaseModel

router = APIRouter(prefix="/empresas", tags=["Empresas"])


class EmpresaRead(BaseModel):
    id: int
    codemp: int
    nome: str
    ativa: bool

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[EmpresaRead])
def listar_empresas(
    apenas_ativas: bool = True,
    _u: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(DimEmpresa)
    if apenas_ativas:
        q = q.filter(DimEmpresa.ativa == True)
    return q.order_by(DimEmpresa.codemp).all()
