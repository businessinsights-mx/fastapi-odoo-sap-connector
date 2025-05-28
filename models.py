from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
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
    lineas = relationship("LineaPedidoOdoo", back_populates="pedido", cascade="all, delete-orphan")

class LineaPedidoOdoo(Base):
    __tablename__ = "lineas_pedido_odoo"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos_odoo.id"), nullable=False)
    producto = Column(String, nullable=False)
    cantidad = Column(Float, nullable=False)
    monto = Column(Float, nullable=False)

    pedido = relationship("PedidoOdoo", back_populates="lineas")