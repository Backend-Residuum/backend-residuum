from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Descarte(Base):
    __tablename__ = "descarte"
    id_descarte = Column(Integer, primary_key=True, index=True)
    data_desc = Column(DateTime(timezone=True), server_default=func.now())
    quantidade = Column(Float, nullable=False)
    tipo_residuo = Column(String(50))
    observacao = Column(String(50))
    status = Column(String(20), default='pendente')
    quantidade_confirmada = Column(Float, nullable=True)
    usuario_id = Column(Integer, nullable=True)
    usuario_lat = Column(Float, nullable=True)
    usuario_long = Column(Float, nullable=True)
    ponto_lat = Column(Float, nullable=True)
    ponto_long = Column(Float, nullable=True)