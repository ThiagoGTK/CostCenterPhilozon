from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.db import get_db
from api.models.dimensoes import DimContaGerencial
from api.schemas.conta_gerencial import ContaGerencialCreate, ContaGerencialRead

router = APIRouter(prefix="/contas-gerenciais", tags=["Plano de Contas Gerencial"])


@router.get("/", response_model=list[ContaGerencialRead])
def listar_contas(tipo: str | None = None, apenas_ativas: bool = True, db: Session = Depends(get_db)):
    q = db.query(DimContaGerencial)
    if apenas_ativas:
        q = q.filter(DimContaGerencial.ativa == True)
    if tipo:
        q = q.filter(DimContaGerencial.tipo == tipo.upper())
    return q.order_by(DimContaGerencial.codigo).all()


@router.get("/{id}", response_model=ContaGerencialRead)
def obter_conta(id: int, db: Session = Depends(get_db)):
    obj = db.get(DimContaGerencial, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta gerencial não encontrada")
    return obj


@router.post("/", response_model=ContaGerencialRead, status_code=status.HTTP_201_CREATED)
def criar_conta(payload: ContaGerencialCreate, db: Session = Depends(get_db)):
    existente = db.query(DimContaGerencial).filter(DimContaGerencial.codigo == payload.codigo).first()
    if existente:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Código '{payload.codigo}' já cadastrado")
    obj = DimContaGerencial(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{id}", response_model=ContaGerencialRead)
def atualizar_conta(id: int, payload: ContaGerencialCreate, db: Session = Depends(get_db)):
    obj = db.get(DimContaGerencial, id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conta gerencial não encontrada")
    for campo, valor in payload.model_dump().items():
        setattr(obj, campo, valor)
    db.commit()
    db.refresh(obj)
    return obj
