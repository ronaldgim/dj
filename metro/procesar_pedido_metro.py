
# import mysql.connector
# import pandas as pd

# mydb = mysql.connector.connect(
#     host="172.16.28.102",
#     user="standard",
#     passwd="gimpromed",
#     database="warehouse"
# )
# mycursor = mydb.cursor()


# mydb_web = mysql.connector.connect(
#     host="172.16.28.102",
#     user="standard",
#     passwd="gimpromed",
#     database="gim_web"
# )
# mycursor_web = mydb_web.cursor()


# def ini(mycursor,mycursor_web, archivo) -> pd.DataFrame:
#     list_t=[]
#     list=[]
#     marca_gim=""

#     # read by default 1st sheet of an excel file
#     # df = pd.read_excel('cot_metro.xlsx')
#     df = pd.read_excel(archivo)
    
#     #print(df)
#     #print(df.iloc[3])


#     for index, row in df.iterrows():
#         codigo_metro = str(row['ARTICULO'])
#         cantidad=row['CANTIDAD']
#         precio_metro=row['PRECIO UNITARIO']

#         if not codigo_metro or str(codigo_metro) == "None":
#             nombre_gim = ""
#             cantidad = ""
#         else:
#             sql_select_Query = "SELECT codigo_gim, precio_unitario, factor FROM gim_web.metro_product where codigo_hm like %s;"
#             codigo_metro_new='%'+str(codigo_metro)
#             mycursor_web.execute(sql_select_Query, (codigo_metro_new,))
#             records = mycursor_web.fetchone()
#             mycursor_web.fetchall()

#             if (records == None):
#                 codigo_gim = "None"
#                 precio_contrato= ""
#             else:
#                 codigo_gim = records[0]
#                 precio_contrato = records[1]
#                 cantidad = cantidad/records[2]


#             sql_select_Query = "SELECT Nombre, MarcaDet, Disponible FROM productos WHERE Codigo= %s;"
#             mycursor.execute(sql_select_Query, (codigo_gim,))
#             records1 = mycursor.fetchone()
#             #print(records1)
#             mycursor.fetchall()


#             if (records1 == None):
#                 nombre_gim = ""
#                 marca_gim = ""
#                 stock_disponible = ""
#             else:
#                 nombre_gim = records1[0]
#                 marca_gim = records1[1]
#                 stock_disponible = records1[2]

#         sql_select_Query = "SELECT SUM(AVAILABLE) FROM warehouse.stock_lote where PRODUCT_ID=%s AND WARE_CODE='BAN' group by WARE_CODE;"
#         mycursor.execute(sql_select_Query, (codigo_gim,))
#         records2 = mycursor.fetchone()
#         mycursor.fetchall()
#         if (records2 == None):
#             disponible_ban=0
#         else:
#             disponible_ban=int(records2[0])


#         sql_select_Query = "SELECT SUM(AVAILABLE) FROM warehouse.stock_lote where PRODUCT_ID=%s AND WARE_CODE='BCT' group by WARE_CODE;"
#         mycursor.execute(sql_select_Query, (codigo_gim,))
#         records3 = mycursor.fetchone()
#         mycursor.fetchall()
#         if (records3 == None):
#             disponible_bct = 0
#         else:
#             disponible_bct = int(records3[0])

#         sql_select_Query = "SELECT SUM(QUANTITY) FROM warehouse.reservas where CODIGO_CLIENTE='CLI03771' AND PRODUCT_ID=%s AND CONFIRMED =0;"
#         mycursor.execute(sql_select_Query, (codigo_gim,))
#         records4 = mycursor.fetchone()
#         mycursor.fetchall()
#         if records4 is None or records4[0] is None:
#             reserva_metro = 0
#         else:
#             reserva_metro = int(records4[0])

#         sql_select_Query = "SELECT SUM(QUANTITY) FROM warehouse.reservas where CODIGO_CLIENTE='CLI01002' AND PRODUCT_ID=%s;"
#         mycursor.execute(sql_select_Query, (codigo_gim,))
#         records5 = mycursor.fetchone()
#         mycursor.fetchall()
#         if records5 is None or records5[0] is None:
#             reserva_gim= 0
#         else:
#             reserva_gim = int(records5[0])

#         list.append(codigo_metro)
#         list.append(codigo_gim)
#         list.append(nombre_gim)
#         list.append(marca_gim)
#         list.append(cantidad)
#         list.append(precio_contrato)
#         list.append(precio_contrato*cantidad)
#         list.append(disponible_ban)
#         list.append(reserva_metro)
#         list.append(reserva_gim)
#         list.append(disponible_bct)
#         list_t.append(list)
#         #print(list)
#         list = []

#     # print(list_t)

#     df = pd.DataFrame(list_t, columns=['codigo_metro', 'codigo_gim', 'nombre_gim', 'marca_gim','cantidad', 'precio_contrato',
#         'Total','disponible_ban', 'reserva_metro','reserva_gim','disponible_bct'])

#     # print(df)

#     df = df.copy()
#     df.loc["TOTAL", "Total"] = pd.to_numeric(df["Total"], errors="coerce").sum()

#     # def check_dif(df):

#     #     estilos = pd.DataFrame("", index=df.index, columns=df.columns)

#     #     # Amarillo: 'tiene' != 0
#     #     check = df["reserva_metro"].fillna(0) != 0
#     #     estilos.loc[check, "reserva_metro"] = "background-color: #FFEB9C"  # amarillo claro

#     #     # Amarillo: 'tiene' != 0
#     #     check = df["reserva_gim"].fillna(0) != 0
#     #     estilos.loc[check, "reserva_gim"] = "background-color: #FFEB9C"  # amarillo claro

#     #     # Rojo: cantidad > disponible_and
#     #     qty = pd.to_numeric(df["cantidad"], errors="coerce")
#     #     disp = pd.to_numeric(df["disponible_ban"], errors="coerce")
#     #     check = qty > disp
#     #     estilos.loc[check, "disponible_ban"] = "background-color: #FFC7CE"

#     #     return estilos


#     # styled = df.style.apply(check_dif, axis=None)

#     # file_name = 'Cuadro_Metro1.xlsx'
#     # styled.to_excel(file_name, engine="openpyxl")

#     return df




import pandas as pd
from django.db import connections


def ini(archivo) -> pd.DataFrame:
    rows_out = []

    df = pd.read_excel(archivo)

    with connections['default'].cursor() as cursor_web, \
        connections['gimpromed_sql'].cursor() as cursor_wh:

        for _, row in df.iterrows():
            codigo_metro = str(row.get('ARTICULO'))
            cantidad = row.get('CANTIDAD', 0) or 0
            precio_metro = row.get('PRECIO UNITARIO', 0) or 0

            codigo_gim = None
            nombre_gim = ""
            marca_gim = ""
            precio_contrato = 0

            # =============================
            # RELACIÓN METRO → GIM
            # =============================
            if codigo_metro and codigo_metro != "None":

                cursor_web.execute("""
                    SELECT codigo_gim, precio_unitario, factor
                    FROM metro_product
                    WHERE codigo_hm LIKE %s
                    LIMIT 1
                """, (f"%{codigo_metro}",))

                record = cursor_web.fetchone()

                if record:
                    codigo_gim, precio_contrato, factor = record
                    cantidad = cantidad / factor if factor else cantidad

                    # =============================
                    # PRODUCTO
                    # =============================
                    cursor_wh.execute("""
                        SELECT Nombre, MarcaDet, Disponible
                        FROM productos
                        WHERE Codigo = %s
                        LIMIT 1
                    """, (codigo_gim,))
                    prod = cursor_wh.fetchone()

                    if prod:
                        nombre_gim, marca_gim, _ = prod

            # =============================
            # STOCK BAN
            # =============================
            cursor_wh.execute("""
                SELECT COALESCE(SUM(AVAILABLE), 0)
                FROM stock_lote
                WHERE PRODUCT_ID = %s
                AND WARE_CODE = 'BAN'
            """, (codigo_gim,))
            disponible_ban = cursor_wh.fetchone()[0] or 0

            # =============================
            # STOCK BCT
            # =============================
            cursor_wh.execute("""
                SELECT COALESCE(SUM(AVAILABLE), 0)
                FROM stock_lote
                WHERE PRODUCT_ID = %s
                AND WARE_CODE = 'BCT'
            """, (codigo_gim,))
            disponible_bct = cursor_wh.fetchone()[0] or 0

            # =============================
            # RESERVA METRO
            # =============================
            cursor_wh.execute("""
                SELECT COALESCE(SUM(QUANTITY), 0)
                FROM reservas
                WHERE CODIGO_CLIENTE = 'CLI03771'
                AND PRODUCT_ID = %s
                AND CONFIRMED = 0
            """, (codigo_gim,))
            reserva_metro = cursor_wh.fetchone()[0] or 0

            # =============================
            # RESERVA GIM
            # =============================
            cursor_wh.execute("""
                SELECT COALESCE(SUM(QUANTITY), 0)
                FROM reservas
                WHERE CODIGO_CLIENTE = 'CLI01002'
                AND PRODUCT_ID = %s
            """, (codigo_gim,))
            reserva_gim = cursor_wh.fetchone()[0] or 0

            total = precio_contrato * cantidad

            rows_out.append([
                codigo_metro,
                codigo_gim,
                nombre_gim,
                marca_gim,
                cantidad,
                precio_contrato,
                total,
                disponible_ban,
                reserva_metro,
                reserva_gim,
                disponible_bct,
            ])

    result_df = pd.DataFrame(
        rows_out,
        columns=[
            'codigo_metro',
            'codigo_gim',
            'nombre_gim',
            'marca_gim',
            'cantidad',
            'precio_contrato',
            'Total',
            'disponible_ban',
            'reserva_metro',
            'reserva_gim',
            'disponible_bct',
        ]
    )

    result_df.loc['TOTAL', 'Total'] = pd.to_numeric(
        result_df['Total'], errors='coerce'
    ).sum()

    return result_df
