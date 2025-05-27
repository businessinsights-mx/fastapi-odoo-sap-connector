from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from setting import Settings
from utils.db import SessionLocal
from utils.odoo_client import get_odoo_connection
from models import PedidoOdoo
from schemas import PedidoOdoo as PedidoOdooSchema

router = APIRouter()
settings = Settings()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/ultimo-pedido-venta", response_model=PedidoOdooSchema)
def obtener_ultimo_pedido(db: Session = Depends(get_db)):
    uid, models = get_odoo_connection()
    pedidos = models.execute_kw(
        settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
        'sale.order', 'search_read',
        [[['state', '!=', 'cancel']]],
        {'fields': [
            'id',
            'name',
            'date_order', 
            'partner_id', 
            'amount_total', 
            'order_line'
            ], 
            'limit': 1, 
            'order': 'date_order desc'
        }
    )
    if not pedidos:
        raise HTTPException(
            status_code=404, 
            detail="No hay pedidos"
        )

    pedido = pedidos[0]

    lineas = models.execute_kw(
        settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
        'sale.order.line', 'read',
        [pedido['order_line']],
        {'fields':
            [
                'product_id', 
                'product_uom_qty', 
                'price_total'
            ]
        }
    )

    detalle_lineas = [
        {
            "producto": l['product_id'][1] if l.get('product_id') and isinstance(l['product_id'], list) and len(l['product_id']) > 1 else "",
            "cantidad": l.get('product_uom_qty', 0),
            "monto": l.get('price_total', 0)
        }
        for l in lineas
        if l.get('product_id') and isinstance(l['product_id'], list) and len(l['product_id']) > 1 and l['product_id'][1]
    ]

    detalle_lineas = [d for d in detalle_lineas if d["producto"]]

    existe = db.query(PedidoOdoo).filter_by(id_odoo=pedido['id']).first()
    if not existe:
        nuevo = PedidoOdoo(
            id_odoo=pedido['id'],
            nombre=pedido['name'],
            fecha=pedido['date_order'],
            cliente=pedido['partner_id'][1] if pedido['partner_id'] else "",
            total=pedido['amount_total']
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        pedido_schema = PedidoOdooSchema.from_orm(nuevo)
    else:
        pedido_schema = PedidoOdooSchema.from_orm(existe)

    return {
        **pedido_schema.model_dump(),
        "lineas": detalle_lineas
    }