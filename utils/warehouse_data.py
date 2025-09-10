from django.db import connections, DatabaseError
from django.http import JsonResponse
import pandas as pd
import numpy as np
import math
from datos.models import Product
# from datos.views import productos_odbc_and_django


def clientes_list():
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT * FROM warehouse.clientes")
            columns = [col[0].lower() for col in cursor.description]
            clientes = [dict(zip(columns, row)) for row in cursor.fetchall()]            
            
            return JsonResponse(data={
                'success':True,
                'msg':'Lista de clientes MBA',
                'data':clientes
            }, status=200)
    except DatabaseError as e:
        return JsonResponse({
            'success': False,
            'msg': f'Error de base de datos: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'msg': f'Error inesperado: {str(e)}'
        }, status=500)
    # finally:
    #     connections['gimpromed_sql'].close()


def get_cliente(column_name: str, column_value: str):
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SELECT * FROM warehouse.clientes WHERE {column_name} = '{column_value}'")
            columns = [col[0].lower() for col in cursor.description]
            row = cursor.fetchone()
            cliente = dict(zip(columns, row)) if row else {}
            
            if row is not None:
                return cliente
            return None
    except Exception as e:
        return None
    # finally:
    #     connections['gimpromed_sql'].close()


def get_numero_factura_by_numero_pedido(contrato: str):
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SELECT CODIGO_FACTURA FROM warehouse.facturas WHERE NUMERO_PEDIDO_SISTEMA = '{contrato}';")
            columns = [col[0].lower() for col in cursor.description]
            row = cursor.fetchone()
            n_factura = dict(zip(columns, row)) if row else {}
            
            if row is not None:
                n_factura = extraer_numero_de_factura(n_factura.get('codigo_factura', None))
                return n_factura #.get('codigo_factura', None)
            return None
    except Exception as e:
        return None


def extraer_numero_de_factura(factura: str):
    
    try:
        n_factura = factura.split('-')[1][4:]
        n_factura = str(int(n_factura))
        return n_factura
    except:
        return factura


def email_cliente_by_codigo(codigo_cliente: str, tipo_email: str = None) -> list[str]:
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("""
            SELECT EMAIL, Email_Fiscal
            FROM warehouse.clientes
            WHERE CODIGO_CLIENTE = %s;
        """, [codigo_cliente])
        
        columns = [col[0].lower() for col in cursor.description]
        row = cursor.fetchone()
        emails = dict(zip(columns, row)) if row else {}

    email = emails.get('email')
    email_fiscal = emails.get('email_fiscal')

    def limpiar_lista(valor: str | None) -> list[str]:
        """Convierte string de emails separados por coma en lista limpia"""
        if not valor:
            return []
        return [e.strip() for e in valor.split(',') if e.strip()]

    email_list = limpiar_lista(email)
    email_fiscal_list = limpiar_lista(email_fiscal)

    if tipo_email is None:
        # Retorna solo el primer email disponible, pero en lista
        if email_list:
            return [email_list[0]]
        elif email_fiscal_list:
            return [email_fiscal_list[0]]
        return []

    elif tipo_email == 'email':
        return email_list

    elif tipo_email == 'email_fiscal':
        return email_fiscal_list

    elif tipo_email == 'todos':
        return email_list + email_fiscal_list

    return []


def get_vendedor_email_by_contrato(contrato_id: str) -> list[str]:
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT u.MAIL AS email
            FROM warehouse.pedidos p
            INNER JOIN warehouse.user_mba u 
                ON p.Entry_by = u.CODIGO_USUARIO 
            WHERE p.CONTRATO_ID = %s;
        """, [contrato_id])

        rows = cursor.fetchall()
        return [row[0] for row in rows] if rows else []


def productos_mba_django():
    with connections['gimpromed_sql'].cursor() as cursor:
        # cursor.execute("SELECT * FROM productos WHERE Inactivo = 0")
        cursor.execute("SELECT * FROM warehouse.productos")
        
        columns = [col[0].lower() for col in cursor.description]
        products = [ 
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        products = pd.DataFrame(products)
        products = products.rename(columns={'codigo':'product_id'})
        p = pd.DataFrame(Product.objects.filter(activo=True).values(
            'product_id', 't_etiq_1p', 't_etiq_2p', 't_etiq_3p', 
            'emp_primario', 'emp_secundario', 'emp_terciario',
            'unidad_empaque_box', 't_armado', 'n_personas'
        ))
        products = products.merge(p, on='product_id', how='left') 
        products['vol_m3'] = products['volumen'] / 1000000
        products['vol_m3'] = products['vol_m3'].replace(np.inf, 0)
        
        return products


def cartones_volumen_factura(contrato: str) -> dict[str, float | int]:
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute("""
            SELECT PRODUCT_ID, QUANTITY
            FROM warehouse.facturas
            WHERE NUMERO_PEDIDO_SISTEMA = %s;
        """, [contrato])

        columns = [col[0].lower() for col in cursor.description]
        factura = [dict(zip(columns, row)) for row in cursor.fetchall()]

    factura_df = pd.DataFrame(factura)
    productos = productos_mba_django()[['product_id', 'unidad_empaque', 'vol_m3']]

    if factura_df.empty:
        return {'volumen': 0.0, 'cartones': 0.0}

    # Unir con catálogo de productos
    df = factura_df.merge(productos, on='product_id', how='left')

    # Calcular volumen y cartones (manejar nulos con fillna)
    df['unidad_empaque'] = df['unidad_empaque'].fillna(1)
    df['vol_m3'] = df['vol_m3'].fillna(0)

    df['cartones'] = df['quantity'] / df['unidad_empaque']
    df['volumen'] = df['quantity'] * df['vol_m3']
    df = df.replace(np.inf, 0)
    df = df.replace(-np.inf, 0)
    
    vol = round(df['volumen'].sum(), 1)
    car = math.ceil(df['cartones'].sum())
    
    return {
        'volumen': vol,
        'cartones': car,
    }
