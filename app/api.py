from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.database import init_db
from database.config import get_settings
import uvicorn
import logging

from routers.user import user_route
from routers.wallet import wallet_route
from routers.prediction import predict_route
from routers.theme import theme_route
from routers.task_log import tasklog_route
from routers.task import task_route

logger = logging.getLogger(__name__)
settings = get_settings()

def create_application() -> FastAPI:
    """
    Создание и конфигурация приложения FastAPI.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )

    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Регистрация маршрутов
    app.include_router(user_route,    prefix="/api")
    app.include_router(wallet_route,  prefix="/api")
    app.include_router(predict_route, prefix="/api")
    app.include_router(theme_route,   prefix="/api")
    app.include_router(tasklog_route, prefix="/api")
    app.include_router(task_route,    prefix="/api")

    # healthcheck для docker-compose
    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return app

app = create_application()

@app.on_event("startup") 
def on_startup():
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка ресурсов при завершении работы приложения."""
    logger.info("Application shutting down...")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(
        'api:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
        log_level="info"
    )
