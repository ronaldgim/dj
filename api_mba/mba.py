# API MBA SQL
import requests

URL = "http://172.16.28.245:5000/lumen-4d/public/movements/ejecutarconsulta"

def api_mba_sql(sql):

    r = requests.post(
        url=URL,
        data = {"sql":sql},
    )
    
    return {
        "status": r.status_code,
        "data": r.json()
    }