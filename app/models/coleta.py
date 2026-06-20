from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base

class Coleta(Base):
    __tablename__ = "coleta"

    id = Column(Integer, primary_key=True, index=True)

    descarte_id = Column(
        Integer,
        ForeignKey("descarte.id_descarte"),
        nullable=False
    )

    peso_real = Column(Float, nullable=False)

    observacao = Column(String(255), nullable=True)

    responsavel = Column(String(100), nullable=False)

    data_coleta = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    descarte = relationship("Descarte")