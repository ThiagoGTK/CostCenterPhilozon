from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import get_settings
from api.routers import centros_custo, contas_gerenciais, mapeamento, orcamento, comparativo, workflow, lancamentos, dre

settings = get_settings()

app = FastAPI(
    title="FP&A Financeiro — API",
    description="Plataforma de planejamento orçamentário e acompanhamento Realizado × Orçado",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_debug else ["https://seu-dominio.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────

PREFIX = "/api/v1"

app.include_router(centros_custo.router, prefix=PREFIX)
app.include_router(contas_gerenciais.router, prefix=PREFIX)
app.include_router(mapeamento.router, prefix=PREFIX)
app.include_router(orcamento.router_versoes, prefix=PREFIX)
app.include_router(orcamento.router, prefix=PREFIX)
app.include_router(comparativo.router, prefix=PREFIX)
app.include_router(workflow.router, prefix=PREFIX)
app.include_router(lancamentos.router, prefix=PREFIX)
app.include_router(dre.router, prefix=PREFIX)


# ── Health Check ────────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "env": settings.app_env}


@app.get("/", tags=["Sistema"])
def root():
    return {"message": "FP&A API", "docs": "/docs"}
