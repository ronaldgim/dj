# API MBA
from api_mba.mba import api_mba_sql

# BD Connection
from django.db import connections


# eliminar datos de tablas en wharehouse
def delete_data_warehouse(table_name):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"DELETE FROM {table_name}")


# obtener columnas de tabla por nombre de la tabla
def get_columns_table_warehouse(table_name):
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [row[0] for row in cursor.fetchall()]
        
    return columns


# insertar datos en tabla de warehouse
def insert_data_warehouse(table_name, data):   
    
    get_columns = get_columns_table_warehouse(table_name)
    
    columnas = ", ".join(get_columns)
    valores  = ", ".join(["%s"] * len(get_columns))
    sql_insert = f"INSERT INTO {table_name} ({columnas}) VALUES ({valores})"
    
    with connections['gimpromed_sql'].cursor() as cursor:
        cursor.executemany(sql_insert, data)



### ACTUALIZAR PRODUCTOS WAREHOUSE POR API DATA
def actualizar_productos_warehouse():
    
    productos_mba = api_mba_sql(
        "SELECT INVT_Ficha_Principal.PRODUCT_ID, INVT_Ficha_Principal.PRODUCT_NAME, "
        "INVT_Ficha_Principal.UM, INVT_Ficha_Principal.GROUP_CODE, INVT_Ficha_Principal.UNIDADES_EMPAQUE, INVT_Ficha_Principal.Custom_Field_1,INVT_Ficha_Principal.Custom_Field_2, INVT_Ficha_Principal.Custom_Field_4, "
        "INVT_Ficha_Principal.INACTIVE, INVT_Ficha_Principal.LARGO, INVT_Ficha_Principal.ANCHO, INVT_Ficha_Principal.ALTURA, INVT_Ficha_Principal.VOLUMEN, INVT_Ficha_Principal.WEIGHT, INVT_Ficha_Principal.AVAILABLE, INVT_Ficha_Principal.UnidadesPorPallet "
        "FROM INVT_Ficha_Principal INVT_Ficha_Principal"
    )    
    
    if productos_mba['status'] == 200:
        
        # data = [tuple(i.values()) for i in productos_mba['data']]
        
        # Trasformar data
        data = []
        
        for i in productos_mba["data"]:
            
            product_id = i['PRODUCT_ID']
            product_name = i['PRODUCT_NAME']
            group_code = i['GROUP_CODE']
            um = i['UM']
            unidades_empaque = i['UNIDADES_EMPAQUE']
            custom_field_1 = i['CUSTOM_FIELD_1']
            custom_field_2 = i['CUSTOM_FIELD_2']
            custom_field_4 = i['CUSTOM_FIELD_4']
            inactive = 0 if i['INACTIVE'] == 'false' else 1 # SOLO POR ESTE DATO SE CREA EL CICLO FOR 
            largo = i['LARGO']
            ancho = i['ANCHO'] 
            altura = i['ALTURA'] 
            volumen = i['VOLUMEN'] 
            weight = i['WEIGHT']
            available = i['AVAILABLE']
            unidadesporpallet = i['UNIDADESPORPALLET']
            
            t = (
                product_id,
                product_name,
                group_code,
                um,
                unidades_empaque,
                custom_field_1,
                custom_field_2,
                custom_field_4,
                inactive,
                largo,
                ancho,
                altura,
                volumen,
                weight,
                available,
                unidadesporpallet
            )
            
            data.append(t)
        
        # Borrar datos de tabla productos
        delete_data_warehouse('productos')
        
        # Insertar datos de tabla productos
        insert_data_warehouse('productos', data)


# ### ACTUALIZAR CLIENTES WAREHOUSE POR API DATA
# def actualizar_clientes_warehouse():
    
#     clientes_mba = api_mba_sql(
#         "SELECT CLNT_Ficha_Principal.CODIGO_CLIENTE, CLNT_Ficha_Principal.IDENTIFICACION_FISCAL, CLNT_Ficha_Principal.NOMBRE_CLIENTE, "
#         "CLNT_Ficha_Principal.CIUDAD_PRINCIPAL, CLNT_Ficha_Principal.CLIENT_TYPE, CLNT_Ficha_Principal.SALESMAN, CLNT_Ficha_Principal.LIMITE_CREDITO, "
#         "CLNT_Ficha_Principal.PriceList, CLNT_Ficha_Principal.E_MAIL, CLNT_Ficha_Principal.Email_Fiscal, CLNT_Ficha_Principal.DIRECCION_PRINCIPAL_1, CLNT_Ficha_Principal.FAX "
#         "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal"
#     )
    

#     for i in clientes_mba['data'][290:300]:
#         print(i)


#     # if clientes_mba["status"] == 200:
        
#     #     data = [tuple(i.values()) for i in clientes_mba['data']]
        
#     #     # Borrar datos de tabla clientes
#     #     delete_data_warehouse('clientes')
        
#     #     # Insertar datos de tabla clientes
#     #     insert_data_warehouse('clientes', data)
