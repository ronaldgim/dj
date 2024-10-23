# API MBA
from api_mba.mba import api_mba_sql


# query clientes mba
def api_query_clientes_mba():
    
    clientes_mba = api_mba_sql(
            """
            SELECT 
                CLNT_Ficha_Principal.CODIGO_CLIENTE, 
                CLNT_Ficha_Principal.IDENTIFICACION_FISCAL, 
                CLNT_Ficha_Principal.NOMBRE_CLIENTE, 
                CLNT_Ficha_Principal.CIUDAD_PRINCIPAL, 
                CLNT_Ficha_Principal.CLIENT_TYPE, 
                CLNT_Ficha_Principal.SALESMAN, 
                CLNT_Ficha_Principal.LIMITE_CREDITO, 
                CLNT_Ficha_Principal.PriceList, 
                CLNT_Ficha_Principal.E_MAIL, 
                CLNT_Ficha_Principal.Email_Fiscal, 
                CLNT_Ficha_Principal.DIRECCION_PRINCIPAL_1, 
                CLNT_Ficha_Principal.FAX 
            FROM 
                CLNT_Ficha_Principal CLNT_Ficha_Principal
            """
        )
    
    return clientes_mba