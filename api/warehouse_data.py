# django db
from django.db import connections, DatabaseError

# DRF
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny #, IsAuthenticated
from rest_framework.response import Response


# API QUERY EN DB WHAREHOUSE
@api_view(['GET'])
@permission_classes([AllowAny])
def api_warehouse_query(request):
    
    try:
        data = request.data
        query = data.get('query', None)
        if query:
            with connections['gimpromed_sql'].cursor() as cursor:
                cursor.execute(f"{query}")
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return Response(data={
                    'success':True,
                    'msg':'Data de wharehouse ok',
                    'data':data
                }, status=200)
        else:
            return Response({
                'success': False,
                'msg': 'Query parameter not provided'
            }, status=400)
    except DatabaseError as e:
        return Response({
            'success': False,
            'msg': f'Error de base de datos: {str(e)}'
        }, status=500)
    except Exception as e:
        return Response({
            'success': False,
            'msg': f'Error inesperado: {str(e)}'
        }, status=500)
    # finally:
    #     connections['gimpromed_sql'].close()


# APIS WHAREHOUSE CLIENT
@api_view(['GET'])
@permission_classes([AllowAny])
def api_clientes_list(_request):
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT * FROM warehouse.clientes")
            columns = [col[0] for col in cursor.description]
            clientes = [dict(zip(columns, row)) for row in cursor.fetchall()]            
            
            return Response(data={
                'success':True,
                'msg':'Lista de clientes MBA',
                'data':clientes
            }, status=200)
    except DatabaseError as e:
        return Response({
            'success': False,
            'msg': f'Error de base de datos: {str(e)}'
        }, status=500)
    except Exception as e:
        return Response({
            'success': False,
            'msg': f'Error inesperado: {str(e)}'
        }, status=500)
    # finally:
    #     connections['gimpromed_sql'].close()


@api_view(['GET'])
@permission_classes([AllowAny])
def api_get_cliente(_request, column_name: str, column_value: str):
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SELECT * FROM warehouse.clientes WHERE {column_name} = '{column_value}'")
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            cliente = dict(zip(columns, row)) if row else {}
            
            if row is not None:
                return Response(
                    data={
                        'success': True,
                        'msg': 'Datos del cliente ok',
                        'data': cliente
                    },
                    status=200
                )
            return Response(
                    data={
                        'success': False,
                        'msg': f'No existe un cliente con {column_name} igual a {column_value}',
                        'data': None
                    },
                    status=400
                )
    except Exception as e:
        return Response(
            data={
                'success': False,
                'msg': str(e)
            }
        )
    # finally:
    #     connections['gimpromed_sql'].close()


# APIS WHAREHOUSE PRODUCTS
@api_view(['GET'])
@permission_classes([AllowAny])
def api_productos_list(_request):
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute("SELECT * FROM warehouse.productos")
            columns = [col[0] for col in cursor.description]
            productos = [dict(zip(columns, row)) for row in cursor.fetchall()]            
            
            return Response(data={
                'success':True,
                'msg':'Lista de productos MBA',
                'data':productos
            }, status=200)
    except DatabaseError as e:
        return Response({
            'success': False,
            'msg': f'Error de base de datos: {str(e)}'
        }, status=500)
    except Exception as e:
        return Response({
            'success': False,
            'msg': f'Error inesperado: {str(e)}'
        }, status=500)
    # finally:
    #     connections['gimpromed_sql'].close()


@api_view(['GET'])
@permission_classes([AllowAny])
def api_get_producto(_request, codigo: str):
    try:
        with connections['gimpromed_sql'].cursor() as cursor:
            cursor.execute(f"SELECT * FROM warehouse.productos WHERE Codigo = '{codigo}'")
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
            producto = dict(zip(columns, row)) if row else {}
            
            if row is not None:
                return Response(
                    data={
                        'success': True,
                        'msg': 'Datos del producto ok',
                        'data': producto
                    },
                    status=200
                )
            return Response(
                    data={
                        'success': False,
                        'msg': f'No existe un producto con código {codigo}',
                        'data': None
                    },
                    status=400
                )
    except Exception as e:
        return Response(
            data={
                'success': False,
                'msg': str(e)
            },
            status=500
        )
    # finally:
    #     connections['gimpromed_sql'].close()
