# fastapi-odoo-sap-connector

API en FastAPI para conectar Odoo SaaS y almacenar pedidos de venta en una base de datos PostgreSQL local.

## Requisitos

- Python 3.11+
- PostgreSQL
- Acceso a una instancia de Odoo SaaS

## Instalación

1. **Clona el repositorio:**

   ```sh
   git clone https://github.com/tu_usuario/fastapi-odoo-sap-connector.git
   cd fastapi-odoo-sap-connector
   ```

2. **Crea y activa un entorno virtual:**

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instala las dependencias:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Configura las variables de entorno:**

   Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido (ajusta los valores):

   ```
   ODOO_URL=https://tu-odoo-saas.com
   ODOO_DB=nombre_db
   ODOO_USERNAME=usuario
   ODOO_PASSWORD=contraseña
   POSTGRES_DSN=postgresql://usuario:contraseña@localhost:5432/tu_db
   ```

5. **Crea la base de datos en PostgreSQL si no existe:**

   ```sh
   psql -U tu_usuario
   CREATE DATABASE tu_db;
   \q
   ```

## Uso

1. **Inicia el servidor FastAPI:**

   ```sh
   uvicorn main:app --reload
   ```

2. **Accede a la documentación interactiva:**

   - [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

3. **Endpoints principales:**

   - `GET /ultimo-pedido-venta`: Obtiene el último pedido de venta de Odoo y lo guarda en la base de datos local.
   - `POST /crear-pedido-venta`: Crea un pedido de venta en Odoo (y lo guarda en la base de datos local) enviando un JSON con el cliente, fecha y productos. Ejemplo de payload:

     ```json
     {
       "cliente_id": 1387,
       "fecha_pedido": "2025-05-28",
       "productos": [
         {
           "producto_id": 877,
           "cantidad": 1,
           "precio_unitario": 9600
         },
         {
           "producto_id": 565,
           "cantidad": 25,
           "precio_unitario": 1200
         }
       ]
     }
     ```

## Estructura del proyecto

- `main.py`: Punto de entrada de la aplicación.
- `routes.py`: Definición de endpoints.
- `models.py`: Modelos de SQLAlchemy.
- `schemas.py`: Esquemas de Pydantic.
- `utils/`: Utilidades para conexión a Odoo y base de datos.
- `setting.py`: Configuración de variables de entorno.

## Licencia

MIT