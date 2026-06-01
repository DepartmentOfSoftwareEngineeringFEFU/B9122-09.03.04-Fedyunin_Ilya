from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routes import router
from database.database import engine, Base

# Создаём таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Научная библиотека ДВФУ",
    description="Подсистема аннотирования и реферирования документов",
    version="2.0.0"
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем API роуты
app.include_router(router, prefix="/api/v1", tags=["library"])

@app.get("/")
async def root():
    return {
        "message": "Научная библиотека ДВФУ",
        "subsystem": "Аннотирование и реферирование документов",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)