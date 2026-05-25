from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract
from api.db import get_db
from api.models.fatos import FatoLancamentoRealizado
from decimal import Decimal

router = APIRouter(prefix="/lancamentos", tags=["Lançamentos Realizados"])


@router.get("/{mes_referencia}")
def listar_lancamentos(
    mes_referencia: str,  # formato: YYYY-MM
    id_empresa: int | None = None,
    id_conta_gerencial: int | None = None,
    db: Session = Depends(get_db),
):
    try:
        ano, mes = map(int, mes_referencia.split("-"))
    except ValueError:
        return {"erro": "Formato inválido. Use YYYY-MM"}

    q = db.query(FatoLancamentoRealizado).filter(
        and_(
            extract("year", FatoLancamentoRealizado.data_referencia) == ano,
            extract("month", FatoLancamentoRealizado.data_referencia) == mes,
        )
    )
    if id_empresa:
        q = q.filter(FatoLancamentoRealizado.id_empresa == id_empresa)
    if id_conta_gerencial:
        q = q.filter(FatoLancamentoRealizado.id_conta_gerencial == id_conta_gerencial)

    return q.limit(500).all()
