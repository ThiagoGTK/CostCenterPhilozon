from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.auth.deps import get_current_user, require_admin_ou_gestor
from api.db import get_db
from api.models.dimensoes import DimCentroCusto
from api.models.usuario import Usuario
from api.schemas.centro_custo import CentroCustoCreate, CentroCustoRead

router = APIRouter(prefix="/centros-custo", tags=["Centros de Custo"])


@router.get("/", response_model=list[CentroCustoRead])
def listar_centros_custo(
    apenas_ativos: bool = True,
    _u: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(DimCentroCusto)
    if apenas_ativos:
        q = q.filter(DimCentroCusto.ativo == True)
    return q.order_by(DimCentroCusto.codigo).all()


@router.get("/{id}", response_model=CentroCustoRead)
def obter_centro_custo(
    id: int,
    _u: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    obj = db.get(DimCentroCusto, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centro de custo não encontrado")
    return obj


@router.post("/", response_model=CentroCustoRead, status_code=status.HTTP_201_CREATED)
def criar_centro_custo(
    payload: CentroCustoCreate,
    _u: Usuario = Depends(require_admin_ou_gestor),
    db: Session = Depends(get_db),
):
    existente = db.query(DimCentroCusto).filter(DimCentroCusto.codigo == payload.codigo).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Código '{payload.codigo}' já cadastrado")
    obj = DimCentroCusto(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=CentroCustoRead)
def atualizar_centro_custo(
    id: int,
    payload: CentroCustoCreate,
    _u: Usuario = Depends(require_admin_ou_gestor),
    db: Session = Depends(get_db),
):
    obj = db.get(DimCentroCusto, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centro de custo não encontrado")
    for campo, valor in payload.model_dump().items():
        setattr(obj, campo, valor)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_centro_custo(
    id: int,
    _u: Usuario = Depends(require_admin_ou_gestor),
    db: Session = Depends(get_db),
):
    obj = db.get(DimCentroCusto, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centro de custo não encontrado")
    obj.ativo = False
    db.commit()
