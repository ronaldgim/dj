
import mysql.connector
import pandas as pd

mydb = mysql.connector.connect(
    host="172.16.28.102",
    user="standard",
    passwd="gimpromed",
    database="warehouse"
)
mycursor = mydb.cursor()


mydb_web = mysql.connector.connect(
    host="172.16.28.102",
    user="standard",
    passwd="gimpromed",
    database="gim_web"
)
mycursor_web = mydb_web.cursor()


def ini(mycursor,mycursor_web, archivo) -> pd.DataFrame:
    list_t=[]
    list=[]
    marca_gim=""

    # read by default 1st sheet of an excel file
    # df = pd.read_excel('cot_metro.xlsx')
    df = pd.read_excel(archivo)
    
    #print(df)
    #print(df.iloc[3])


    for index, row in df.iterrows():
        codigo_metro = str(row['ARTICULO'])
        cantidad=row['CANTIDAD']
        precio_metro=row['PRECIO UNITARIO']

        if not codigo_metro or str(codigo_metro) == "None":
            nombre_gim = ""
            cantidad = ""
        else:
            sql_select_Query = "SELECT codigo_gim, precio_unitario, factor FROM gim_web.metro_product where codigo_hm like %s;"
            codigo_metro_new='%'+str(codigo_metro)
            mycursor_web.execute(sql_select_Query, (codigo_metro_new,))
            records = mycursor_web.fetchone()
            mycursor_web.fetchall()

            if (records == None):
                codigo_gim = "None"
                precio_contrato= ""
            else:
                codigo_gim = records[0]
                precio_contrato = records[1]
                cantidad = cantidad/records[2]


            sql_select_Query = "SELECT Nombre, MarcaDet, Disponible FROM productos WHERE Codigo= %s;"
            mycursor.execute(sql_select_Query, (codigo_gim,))
            records1 = mycursor.fetchone()
            #print(records1)
            mycursor.fetchall()


            if (records1 == None):
                nombre_gim = ""
                marca_gim = ""
                stock_disponible = ""
            else:
                nombre_gim = records1[0]
                marca_gim = records1[1]
                stock_disponible = records1[2]

        sql_select_Query = "SELECT SUM(AVAILABLE) FROM warehouse.stock_lote where PRODUCT_ID=%s AND WARE_CODE='BAN' group by WARE_CODE;"
        mycursor.execute(sql_select_Query, (codigo_gim,))
        records2 = mycursor.fetchone()
        mycursor.fetchall()
        if (records2 == None):
            disponible_ban=0
        else:
            disponible_ban=int(records2[0])


        sql_select_Query = "SELECT SUM(AVAILABLE) FROM warehouse.stock_lote where PRODUCT_ID=%s AND WARE_CODE='BCT' group by WARE_CODE;"
        mycursor.execute(sql_select_Query, (codigo_gim,))
        records3 = mycursor.fetchone()
        mycursor.fetchall()
        if (records3 == None):
            disponible_bct = 0
        else:
            disponible_bct = int(records3[0])

        sql_select_Query = "SELECT SUM(QUANTITY) FROM warehouse.reservas where CODIGO_CLIENTE='CLI03771' AND PRODUCT_ID=%s AND CONFIRMED =0;"
        mycursor.execute(sql_select_Query, (codigo_gim,))
        records4 = mycursor.fetchone()
        mycursor.fetchall()
        if records4 is None or records4[0] is None:
            reserva_metro = 0
        else:
            reserva_metro = int(records4[0])

        sql_select_Query = "SELECT SUM(QUANTITY) FROM warehouse.reservas where CODIGO_CLIENTE='CLI01002' AND PRODUCT_ID=%s;"
        mycursor.execute(sql_select_Query, (codigo_gim,))
        records5 = mycursor.fetchone()
        mycursor.fetchall()
        if records5 is None or records5[0] is None:
            reserva_gim= 0
        else:
            reserva_gim = int(records5[0])

        list.append(codigo_metro)
        list.append(codigo_gim)
        list.append(nombre_gim)
        list.append(marca_gim)
        list.append(cantidad)
        list.append(precio_contrato)
        list.append(precio_contrato*cantidad)
        list.append(disponible_ban)
        list.append(reserva_metro)
        list.append(reserva_gim)
        list.append(disponible_bct)
        list_t.append(list)
        #print(list)
        list = []

    # print(list_t)

    df = pd.DataFrame(list_t, columns=['codigo_metro', 'codigo_gim', 'nombre_gim', 'marca_gim','cantidad', 'precio_contrato',
        'Total','disponible_ban', 'reserva_metro','reserva_gim','disponible_bct'])

    # print(df)

    df = df.copy()
    df.loc["TOTAL", "Total"] = pd.to_numeric(df["Total"], errors="coerce").sum()

    # def check_dif(df):

    #     estilos = pd.DataFrame("", index=df.index, columns=df.columns)

    #     # Amarillo: 'tiene' != 0
    #     check = df["reserva_metro"].fillna(0) != 0
    #     estilos.loc[check, "reserva_metro"] = "background-color: #FFEB9C"  # amarillo claro

    #     # Amarillo: 'tiene' != 0
    #     check = df["reserva_gim"].fillna(0) != 0
    #     estilos.loc[check, "reserva_gim"] = "background-color: #FFEB9C"  # amarillo claro

    #     # Rojo: cantidad > disponible_and
    #     qty = pd.to_numeric(df["cantidad"], errors="coerce")
    #     disp = pd.to_numeric(df["disponible_ban"], errors="coerce")
    #     check = qty > disp
    #     estilos.loc[check, "disponible_ban"] = "background-color: #FFC7CE"

    #     return estilos


    # styled = df.style.apply(check_dif, axis=None)

    # file_name = 'Cuadro_Metro1.xlsx'
    # styled.to_excel(file_name, engine="openpyxl")

    return df