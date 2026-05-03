"""
Aplicação Principal - Residium
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, descarte
from app.database import engine, Base
import app.models.descarte # Garante que o modelo de descarte seja carregado

# Cria as tabelas no banco de dados caso não existam
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Residium API")

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

@app.get("/")
def root():
    return {"msg": "Residium API rodando com sucesso!"}