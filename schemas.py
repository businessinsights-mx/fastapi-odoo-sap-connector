from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class LineaPedido(BaseModel):
    producto: str
    cantidad: float
    monto: float

class PedidoVentaOdoo(BaseModel):
    id_odoo: int
    nombre: str
    fecha: datetime
    cliente: str
    total: float
    lineas: Optional[List[LineaPedido]] = None

    class Config:
        from_attributes = True

class ProductoPedido(BaseModel):
    producto_id: int
    cantidad: float
    precio_unitario: float

class PedidoVentaCreate(BaseModel):
    cliente_id: int
    fecha_pedido: str
    productos: List[ProductoPedido]