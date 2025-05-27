from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PedidoOdoo(Base):
    __tablename__ = "pedidos_odoo"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_odoo = Column(Integer, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    fecha = Column(DateTime, nullable=False)
    cliente = Column(String, nullable=False)
    total = Column(Float, nullable=False)