import sys
import os
import logging
from contextlib import asynccontextmanager

# Ensure backend directory is in sys.path regardless of execution directory or runner
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import check_database_health
from app.api.v1 import (
    auth,
    users,
    categories,
    suppliers,
    products,
    inventory,
    sales,
    purchases,
    forecasts,
    recommendations,
    alerts,
    dashboard,
    analytics,
    settings as app_settings,
    notifications,
    ws,
)
from app.services.daily_scheduler_service import start_scheduler_loop
import asyncio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("stocksense")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup check
    logger.info("Initializing StockSense Backend...")
    is_healthy, msg = check_database_health()
    if is_healthy:
        logger.info(f"Database status: {msg}")
    else:
        logger.warning(
            f"Database connection warning on startup: {msg}\n"
            f"Ensure DATABASE_URL is configured with your Neon PostgreSQL connection string in .env"
        )
    # Launch background daily inventory check scheduler
    scheduler_task = asyncio.create_task(start_scheduler_loop())
    yield
    # Shutdown logic
    scheduler_task.cancel()
    logger.info("Shutting down StockSense Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler to sanitize unexpected internal errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the system administrator."}
    )


# Root and Health checks
@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": "StockSense API Backend is operational",
        "documentation": "/docs",
        "frontend_url": "http://localhost:5173",
        "status": "online"
    }


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    is_db_connected, db_msg = check_database_health()
    return {
        "status": "healthy" if is_db_connected else "degraded",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": {
            "provider": "Neon Serverless PostgreSQL",
            "connected": is_db_connected,
            "message": db_msg
        }
    }


# Include Versioned API Routers
api_v1 = settings.API_V1_STR
app.include_router(auth.router, prefix=f"{api_v1}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{api_v1}/users", tags=["Users"])
app.include_router(categories.router, prefix=f"{api_v1}/categories", tags=["Categories"])
app.include_router(suppliers.router, prefix=f"{api_v1}/suppliers", tags=["Suppliers"])
app.include_router(products.router, prefix=f"{api_v1}/products", tags=["Products"])
app.include_router(inventory.router, prefix=f"{api_v1}/inventory", tags=["Inventory"])
app.include_router(sales.router, prefix=f"{api_v1}/sales", tags=["Sales"])
app.include_router(purchases.router, prefix=f"{api_v1}/purchases", tags=["Purchases"])
app.include_router(forecasts.router, prefix=f"{api_v1}/forecasts", tags=["Demand Forecasting"])
app.include_router(recommendations.router, prefix=f"{api_v1}/recommendations", tags=["Replenishment Recommendations"])
app.include_router(alerts.router, prefix=f"{api_v1}/alerts", tags=["Alerts"])
app.include_router(dashboard.router, prefix=f"{api_v1}/dashboard", tags=["Dashboard"])
app.include_router(analytics.router, prefix=f"{api_v1}/analytics", tags=["Analytics"])
app.include_router(notifications.router, prefix=f"{api_v1}/notifications", tags=["Notifications & Email"])
app.include_router(app_settings.router, prefix=f"{api_v1}/settings", tags=["Settings"])
app.include_router(ws.router, prefix=api_v1, tags=["WebSockets"])


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
