import sqlite3
import csv
import pyodbc
import mysql.connector
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from sqlite3 import Error
        
currentTimeDate = datetime.now() - relativedelta(days=10)
#currentTimeDate = datetime.now() - datetime.timedelta(15)
OneMonthTime = currentTimeDate.strftime('%d-%m-%Y')
#print(OneMonthTime)
        
def odbc(mydb):
            # Using a DSN, but providing a password as well
            cnxn = pyodbc.connect('DSN=mba3;PWD=API')
            # Create a cursor from the connection
            cursorOdbc = cnxn.cursor()
            ####Cstock_lotes_ mba3O######
            print ("odbc_execute")
        
        
            #####Connect to MYSQL Database#####
            mycursorMysql = mydb.cursor() 
            ##Stock Lotes
            cursorOdbc.execute(
                "SELECT INVT_Ficha_Principal.PRODUCT_ID, INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, "
                "INVT_Ficha_Principal.UM, INVT_Producto_Lotes.OH, INVT_Producto_Lotes_Bodegas.OH, INVT_Producto_Lotes_Bodegas.COMMITED, "
                "INVT_Producto_Lotes_Bodegas.QUANTITY, INVT_Producto_Lotes.LOTE_ID, INVT_Producto_Lotes.Fecha_elaboracion_lote, INVT_Producto_Lotes.FECHA_CADUCIDAD, "
                "INVT_Producto_Lotes_Bodegas.WARE_CODE, INVT_Producto_Lotes_Bodegas.LOCATION "
                "FROM INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Producto_Lotes INVT_Producto_Lotes, INVT_Producto_Lotes_Bodegas INVT_Producto_Lotes_Bodegas "
                "WHERE INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Lotes.PRODUCT_ID_CORP AND "
                "INVT_Producto_Lotes_Bodegas.PRODUCT_ID_CORP = INVT_Ficha_Principal.PRODUCT_ID_CORP AND "
                "INVT_Producto_Lotes.LOTE_ID = INVT_Producto_Lotes_Bodegas.LOTE_ID AND INVT_Producto_Lotes.WARE_CODE_CORP = INVT_Producto_Lotes_Bodegas.WARE_CODE AND "
                "((INVT_Producto_Lotes.OH>0) AND (INVT_Producto_Lotes_Bodegas.OH>0))"
            )
        
            rows = cursorOdbc.fetchall()
        
            #Reservas
            cursorOdbc.execute(
                "SELECT CLNT_Pedidos_Principal.FECHA_PEDIDO, CLNT_Pedidos_Principal.CONTRATO_ID, CLNT_Ficha_Principal.NOMBRE_CLIENTE, "
                "CLNT_Pedidos_Detalle.PRODUCT_ID, CLNT_Pedidos_Detalle.PRODUCT_NAME, CLNT_Pedidos_Detalle.QUANTITY, CLNT_Pedidos_Detalle.Despachados, CLNT_Pedidos_Principal.WARE_CODE, CLNT_Pedidos_Principal.CONFIRMED "
                "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal, CLNT_Pedidos_Detalle CLNT_Pedidos_Detalle, CLNT_Pedidos_Principal CLNT_Pedidos_Principal "
                "WHERE CLNT_Pedidos_Principal.CONTRATO_ID_CORP = CLNT_Pedidos_Detalle.CONTRATO_ID_CORP AND CLNT_Ficha_Principal.CODIGO_CLIENTE = CLNT_Pedidos_Principal.CLIENT_ID "
                "AND ((CLNT_Pedidos_Principal.PEDIDO_CERRADO=false) AND (CLNT_Pedidos_Detalle.TIPO_DOCUMENTO='PE')) ORDER BY CLNT_Pedidos_Principal.CONTRATO_ID DESC"
                    )
        
            reservas = cursorOdbc.fetchall()
        
            #Clientes
            cursorOdbc.execute(
                    "SELECT CLNT_Ficha_Principal.CODIGO_CLIENTE, CLNT_Ficha_Principal.IDENTIFICACION_FISCAL, CLNT_Ficha_Principal.NOMBRE_CLIENTE, "
                    "CLNT_Ficha_Principal.CIUDAD_PRINCIPAL, CLNT_Ficha_Principal.CLIENT_TYPE, CLNT_Ficha_Principal.SALESMAN, CLNT_Ficha_Principal.LIMITE_CREDITO, CLNT_Ficha_Principal.PriceList "
                    "FROM CLNT_Ficha_Principal CLNT_Ficha_Principal limit 10"
                        )
            clientes=[]
            clientes = cursorOdbc.fetchall()
            print(clientes[1])
            #Productos
            cursorOdbc.execute(
                "SELECT INVT_Ficha_Principal.PRODUCT_ID, INVT_Ficha_Principal.PRODUCT_NAME, "
                "INVT_Ficha_Principal.UM, INVT_Ficha_Principal.GROUP_CODE, INVT_Ficha_Principal.UNIDADES_EMPAQUE  "
                "FROM INVT_Ficha_Principal INVT_Ficha_Principal"
            )
            productos = cursorOdbc.fetchall()
        
            #Facturas (ultimos 2 meses)
            cursorOdbc.execute(
                "SELECT CLNT_Factura_Principal.CODIGO_FACTURA, CLNT_Factura_Principal.FECHA_FACTURA, "
                "CLNT_Ficha_Principal.NOMBRE_CLIENTE, INVT_Ficha_Principal.PRODUCT_ID, "
                "INVT_Ficha_Principal.PRODUCT_NAME, INVT_Ficha_Principal.GROUP_CODE, INVT_Producto_Movimientos.QUANTITY "
                "FROM CLNT_Factura_Principal CLNT_Factura_Principal, CLNT_Ficha_Principal CLNT_Ficha_Principal, INVT_Ficha_Principal INVT_Ficha_Principal, INVT_Producto_Movimientos INVT_Producto_Movimientos "
                "WHERE INVT_Ficha_Principal.PRODUCT_ID_CORP = INVT_Producto_Movimientos.PRODUCT_ID_CORP AND "
                "CLNT_Factura_Principal.CODIGO_CLIENTE = CLNT_Ficha_Principal.CODIGO_CLIENTE AND CLNT_Factura_Principal.CODIGO_FACTURA = INVT_Producto_Movimientos.DOC_ID_CORP2 "
                "AND ((INVT_Producto_Movimientos.CONFIRM=TRUE And INVT_Producto_Movimientos.CONFIRM=TRUE) AND (INVT_Producto_Movimientos.I_E_SIGN='-') "
                "AND (INVT_Producto_Movimientos.ADJUSTMENT_TYPE='FT') AND (CLNT_Factura_Principal.ANULADA=FALSE)) AND  FECHA_FACTURA >='"+OneMonthTime+"'"
            )
            facturas = cursorOdbc.fetchall()
        
        
        
        
            sql_delete = "DELETE FROM clientes"
            mycursorMysql.execute(sql_delete)
            print("successfully deleted clientes")
        
            sql_insert_clientes = """INSERT INTO clientes (CODIGO_CLIENTE, IDENTIFICACION_FISCAL, NOMBRE_CLIENTE,
            CIUDAD_PRINCIPAL, CLIENT_TYPE, SALESMAN, LIMITE_CREDITO, PRICELIST) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"""
            result = mycursorMysql.executemany(sql_insert_clientes, clientes)
            print(type(result))
            mydb.commit()
            print("Record inserted successfully into database_mysql-CLIENTES")
        
        
        
        
        
            sql_delete="DELETE FROM stock_lote"
            mycursorMysql.execute(sql_delete)
            print("successfully deleted lotes")
        
            sql_insert_infimas = """INSERT INTO stock_lote (PRODUCT_ID, PRODUCT_NAME, GROUP_CODE, 
            UM, OH, OH2, COMMITED, QUANTITY, LOTE_ID, Fecha_elaboracion_lote, 
            FECHA_CADUCIDAD, WARE_CODE, LOCATION) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
            result = mycursorMysql.executemany(sql_insert_infimas, rows)
            mydb.commit()
            print("Record inserted successfully into database_mysql-LOTES")
        
        
            sql_delete="DELETE FROM reservas"
            mycursorMysql.execute(sql_delete)
            print("successfully deleted reservas")
        
            sql_insert_reservas = """INSERT INTO reservas (FECHA_PEDIDO, CONTRATO_ID, NOMBRE_CLIENTE, 
            PRODUCT_ID, PRODUCT_NAME, QUANTITY, Despachados, WARE_CODE, CONFIRMED) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);"""
            result = mycursorMysql.executemany(sql_insert_reservas, reservas)
            mydb.commit()
            print("Record inserted successfully into database_mysql - RESERVAS")
        
        
            delete_sql = "DELETE FROM productos"
            mycursorMysql.execute(delete_sql)
            mydb.commit()
            print("Sucessful Deleted productos")
        
            sql_insert = """INSERT INTO productos (Codigo,Nombre,Unidad,Marca,Unidad_Empaque) VALUES (%s, %s, %s, %s, %s)"""
            mycursorMysql.executemany(sql_insert, productos)
            print("Sucessful Updated Productos")
            mydb.commit()
        
        
        
            delete_sql = "DELETE FROM facturas"
            mycursorMysql.execute(delete_sql)
            mydb.commit()
            print("Sucessful Deleted facturas")
        
            sql_insert = """INSERT INTO facturas (CODIGO_FACTURA,FECHA_FACTURA,NOMBRE_CLIENTE,PRODUCT_ID,PRODUCT_NAME,GROUP_CODE,QUANTITY) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            mycursorMysql.executemany(sql_insert, facturas)
            print("Sucessful Updated Facturas")
            mydb.commit()
        
        
        
def main():
            
            mydb = mysql.connector.connect(
                    host="172.16.28.102",
                    user="standard",
                    passwd="gimpromed",
                    database="warehouse"
                )
            print(OneMonthTime)
            odbc(mydb)


if __name__ == '__main__':
    main()