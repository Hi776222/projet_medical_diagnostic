"""
main.py — Point d'entrée de l'application FastAPI
Lancement : python main.py  OU  uvicorn app.api:app --reload
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )