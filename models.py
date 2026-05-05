from sqlalchemy import Column, Integer, String
from database import Base

class Residuo(Base):
    __tablename__ = "residuos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    codigo_barras = Column(String, unique=True, nullable=False)
    quantidade = Column(Integer, default=1)