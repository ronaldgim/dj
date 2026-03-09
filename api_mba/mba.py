# API MBA SQL
import requests
import hashlib
from django.core.cache import cache

URL = "http://172.16.28.245:5000/lumen-4d/public/movements/ejecutarconsulta"

def api_mba_sql(sql, use_cache=True, cache_timeout=300):
    """
    Ejecuta query SQL en API MBA con sistema de caché.

    Args:
        sql: Query SQL a ejecutar
        use_cache: Si debe usar caché (True por defecto)
        cache_timeout: Tiempo de caché en segundos (300 = 5 minutos por defecto)

    Returns:
        dict: {"status": int, "data": list/dict}
    """

    # Generar key única para el caché basada en el SQL
    cache_key = None
    if use_cache:
        sql_hash = hashlib.md5(sql.encode('utf-8')).hexdigest()
        cache_key = f"api_mba_sql:{sql_hash}"

        # Intentar obtener del caché
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            # print(f"✅ Caché HIT para query: {sql[:50]}...")
            return cached_result

    # Si no está en caché, hacer la llamada a la API
    try:
        r = requests.post(
            url=URL,
            data={"sql": sql},
            timeout=30  # Timeout de 30 segundos
        )

        result = {
            "status": r.status_code,
            "data": r.json()
        }

        # Guardar en caché solo si la respuesta es exitosa
        if use_cache and result["status"] == 200 and cache_key:
            cache.set(cache_key, result, cache_timeout)
            # print(f"💾 Guardado en caché: {sql[:50]}...")

        return result

    except requests.Timeout:
        print(f"⏱️ Timeout en API MBA: {sql[:50]}...")
        return {
            "status": 408,
            "data": {"error": "Request timeout"}
        }
    except Exception as e:
        print(f"❌ Error en API MBA: {str(e)}")
        return {
            "status": 500,
            "data": {"error": str(e)}
        }
        # return {
        #     "status": 200, #r.status_code,
        #     "data": f"Api status: {r.status_code} - Error: {str(e)}"
        # }