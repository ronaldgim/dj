# API MBA SQL
import requests

URL = "http://172.16.28.245:5000/lumen-4d/public/movements/ejecutarconsulta"

def api_mba_sql(sql):
    
    try:
        r = requests.post(
            url=URL,
            data = {"sql":sql},
        )
        
        return {
            "status": r.status_code,
            "data": r.json()
        }
    except Exception as e:
        print(str(e))
        return {
            "status": 200, #r.status_code,
            "data": f"Api status {r.status_code} {str(e)}"
        }