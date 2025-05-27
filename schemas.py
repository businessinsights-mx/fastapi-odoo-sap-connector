from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class LineaPedido(BaseModel):
    producto: str
    cantidad: float
    monto: float

class PedidoOdoo(BaseModel):
    id_odoo: int
    nombre: str
    fecha: datetime
    cliente: str
    total: float
    lineas: Optional[
        List[LineaPedido]
    ] = None

    class Config:
        from_attributes = True