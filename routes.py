from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from setting import Settings
from utils.db import SessionLocal
from utils.odoo_client import get_odoo_connection
from models import PedidoOdoo, LineaPedidoOdoo
from schemas import PedidoVentaOdoo, PedidoVentaCreate
import xmlrpc.client

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
    try:
        pedidos = models.execute_kw(
            settings.ODOO_DB, 
            uid, 
            settings.ODOO_PASSWORD,
            'sale.order', 
            'search_read',
            [[['state', '!=', 'cancel']]],
            {'fields': [
                'id', 'name', 'date_order', 'partner_id', 'amount_total', 'order_line'
            ], 'limit': 1, 'order': 'date_order desc'}
        )
    except xmlrpc.client.Fault:
        # Error de comunicación o ejecución en Odoo al obtener los pedidos
        raise HTTPException(
            status_code=500,
            detail="No se pudo obtener el último pedido debido a un error de conexión con Odoo."
        )

    if not pedidos:
        # No hay pedidos disponibles
        raise HTTPException(
            status_code=404,
            detail="No se encontró ningún pedido en Odoo que no esté cancelado."
        )

    pedido = pedidos[0]

    try:
        lineas = models.execute_kw(
            settings.ODOO_DB, 
            uid, 
            settings.ODOO_PASSWORD,
            'sale.order.line', 
            'read',
            [pedido['order_line']],
            {'fields': ['product_id', 'product_uom_qty', 'price_total']}
        )
    except xmlrpc.client.Fault:
        # Error al obtener las líneas del pedido
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un problema al obtener las líneas del pedido desde Odoo."
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

        for linea in detalle_lineas:
            nueva_linea = LineaPedidoOdoo(
                pedido_id=nuevo.id,
                producto_id=linea["producto_id"],
                producto=linea["producto"],
                cantidad=linea["cantidad"],
                monto=linea["monto"]
            )
            db.add(nueva_linea)
        db.commit()

        return {
            "id_odoo": nuevo.id_odoo,
            "nombre": nuevo.nombre,
            "fecha": nuevo.fecha,
            "cliente": nuevo.cliente,
            "total": nuevo.total,
            "lineas": detalle_lineas
        }
    else:
        return {
            "id_odoo": existe.id_odoo,
            "nombre": existe.nombre,
            "fecha": existe.fecha,
            "cliente": existe.cliente,
            "total": existe.total,
            "lineas": [
                {
                    "producto_id": l.producto_id,
                    "producto": l.producto,
                    "cantidad": l.cantidad,
                    "monto": l.monto
                }
                for l in existe.lineas
            ]
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

    try:
        order_id = models.execute_kw(
            settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
            'sale.order', 'create', [{
                'partner_id': pedido.cliente_id,
                'date_order': pedido.fecha_pedido,
                'order_line': order_lines
            }]
        )
    except xmlrpc.client.Fault as e:
        # Error común: partner_id inválido o no existe
        if "partner_id" in e.faultString or "Customer" in e.faultString:
            raise HTTPException(
                status_code=422,
                detail="No se pudo crear el pedido: el cliente proporcionado no existe o no fue especificado correctamente."
            )
        raise HTTPException(status_code=500, detail="Ocurrió un error interno al crear el pedido. Intenta más tarde.")

    try:
        pedido_odoo = models.execute_kw(
            settings.ODOO_DB, 
            uid, 
            settings.ODOO_PASSWORD,
            'sale.order', 
            'read', 
            [[order_id]],
            {'fields': ['id', 'name', 'date_order', 'partner_id', 'amount_total']}
        )[0]
    except IndexError:
        # El pedido fue creado, pero no se pudo recuperar con .read()
        raise HTTPException(
            status_code=404,
            detail="El pedido fue creado, pero no se pudo recuperar su información. Intenta consultar más tarde."
        )
    except xmlrpc.client.Fault:
        # Error interno inesperado al leer
        raise HTTPException(
            status_code=500,
            detail="No se pudo acceder al pedido recién creado debido a un problema interno."
        )

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
        try:
            producto_odoo = models.execute_kw(
                settings.ODOO_DB, 
                uid, 
                settings.ODOO_PASSWORD,
                'product.product', 
                'read', 
                [[producto.producto_id]],
                {'fields': ['name']}
            )
            nombre_producto = producto_odoo[0]['name'] if producto_odoo else str(producto.producto_id)
        except IndexError:
            # El producto no existe o fue eliminado
            raise HTTPException(
                status_code=422,
                detail=f"No se encontró el producto con ID {producto.producto_id}. Verifica que sea válido."
            )
        except xmlrpc.client.Fault:
            # Error de comunicación o conexión inesperado
            raise HTTPException(
                status_code=500,
                detail=f"Ocurrió un error al buscar el producto con ID {producto.producto_id}. Intenta nuevamente."
            )

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
