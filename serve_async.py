# serve_async.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "gimpromed.asgi:application",
        host="172.16.28.17",
        port=8000,
        workers=4,
        log_level="info",
        reload=False  # ⚠️ reload=False para producción
    )