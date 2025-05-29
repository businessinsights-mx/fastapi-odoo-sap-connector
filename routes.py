from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from setting import Settings
from utils.db import SessionLocal
from utils.odoo_client import get_odoo_connection
from models import PedidoOdoo, LineaPedidoOdoo
from schemas import PedidoVentaOdoo, PedidoVentaCreate

router = APIRouter()
settings = Settings()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/ultimo-pedido-venta", response_model=PedidoVentaOdoo)
def obtener_ultimo_pedido(db: Session = Depends(get_db)):
    uid, models = get_odoo_connection()
    pedidos = models.execute_kw(
        settings.ODOO_DB, 
        uid, 
        settings.ODOO_PASSWORD,
        'sale.order', 
        'search_read',
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
        settings.ODOO_DB, 
        uid, 
        settings.ODOO_PASSWORD,
        'sale.order.line', 
        'read',
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
            "producto_id": l['product_id'][0] if l.get('product_id') and isinstance(l['product_id'], list) and len(l['product_id']) > 0 else None,
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
        pedido_schema = PedidoVentaOdoo.from_orm(nuevo)
    else:
        pedido_schema = PedidoVentaOdoo.from_orm(existe)

    return {
        **pedido_schema.model_dump(),
        "lineas": detalle_lineas
    }

@router.post("/crear-pedido-venta")
def crear_pedido_venta(
    pedido: PedidoVentaCreate = Body(...),
    db: Session = Depends(get_db)
):
    uid, models = get_odoo_connection()
    
    order_lines = [
        (0, 0, {
            'product_id': p.producto_id,
            'product_uom_qty': p.cantidad,
            'price_unit': p.precio_unitario
        }) for p in pedido.productos
    ]
    
    order_id = models.execute_kw(
        settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
        'sale.order', 'create', [{
            'partner_id': pedido.cliente_id,
            'date_order': pedido.fecha_pedido,
            'order_line': order_lines
        }]
    )

    pedido_odoo = models.execute_kw(
        settings.ODOO_DB, 
        uid, 
        settings.ODOO_PASSWORD,
        'sale.order', 
        'read', 
        [[order_id]],
        {'fields': [
            'id', 
            'name', 
            'date_order', 
            'partner_id', 
            'amount_total'
            ]
        }
    )[0]

    nuevo = PedidoOdoo(
        id_odoo=pedido_odoo['id'],
        nombre=pedido_odoo['name'],
        fecha=pedido_odoo['date_order'],
        cliente=pedido_odoo['partner_id'][1] if pedido_odoo['partner_id'] else "",
        total=pedido_odoo['amount_total']
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    for producto in pedido.productos:
        producto_odoo = models.execute_kw(
            settings.ODOO_DB, 
            uid, 
            settings.ODOO_PASSWORD,
            'product.product', 
            'read', 
            [[producto.producto_id]],
            {'fields': [
                'name'
                ]
            }
        )
        nombre_producto = producto_odoo[0]['name'] if producto_odoo else str(producto.producto_id)

        nueva_linea = LineaPedidoOdoo(
            pedido_id=nuevo.id,
            producto_id=producto.producto_id, 
            producto=nombre_producto,
            cantidad=producto.cantidad,
            monto=producto.precio_unitario * producto.cantidad
        )
        db.add(nueva_linea)
    db.commit()

    return {
        "order_id": order_id,
        "nombre": pedido_odoo['name'],
        "total": pedido_odoo['amount_total'],
        "message": "Pedido creado en Odoo y guardado localmente"
    }