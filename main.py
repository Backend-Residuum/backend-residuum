from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import models, schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/residuos", response_model=schemas.ResiduoResponse)
def criar_residuo(residuo: schemas.ResiduoCreate, db: Session = Depends(get_db)):

    existente = db.query(models.Residuo).filter(
        models.Residuo.codigo_barras == residuo.codigo_barras
    ).first()

    if existente:
        existente.quantidade += residuo.quantidade
        db.commit()
        db.refresh(existente)
        return existente

    novo = models.Residuo(
        nome=residuo.nome,
        codigo_barras=residuo.codigo_barras,
        quantidade=residuo.quantidade
    )

    db.add(novo)
    db.commit()
    db.refresh(novo)

    return novo