from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.event_app.router import router as router_event
from src.auth.router import router as router_auth

app = FastAPI(
    title="API Documentation",
    description="API documentation for the service",
    version="1.0.0",
    root_path="/api",
    docs_url="/docs"
)

# Настройка CORS
origins = [
    "http://localhost",
    "http://localhost:3000",  # Для React/Next.js frontend
    "http://localhost:8000",  # Для локальной разработки
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Set-Cookie", "Access-Control-Allow-Headers",
                  "Access-Control-Allow-Origin", "Authorization"],
)


# Подключение роутеров
app.include_router(router_event, prefix="/v1/event", tags=["event"])
app.include_router(router_auth, prefix="/v1/auth", tags=["auth"])

# Обработчик ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )
