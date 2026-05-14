"""
Aplicação Principal - Residuum
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, descarte, endereco, residuo
from app.core.decorators import public
from app.core.security import require_auth_unless_public

# IMPORTAÇÕES DO BANCO
from app.database import Base, engine

# IMPORTAR TODOS OS MODELS
from app.models.usuario import Usuario
from app.models.endereco import Endereco
from app.models.descarte import Descarte
from app.models.residuo import Residuo

# CRIA AS TABELAS
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Residuum API",
    dependencies=[Depends(require_auth_unless_public)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro das rotas
app.include_router(auth.router, tags=["Autenticação"])
app.include_router(descarte.router, prefix="/descarte", tags=["Descarte"])
app.include_router(endereco.router, tags=["Endereço"])
app.include_router(residuo.router, prefix="/residuos", tags=["Resíduos"])


@app.get("/")
@public
def root():
    return {"msg": "Residuum API rodando com sucesso!"}