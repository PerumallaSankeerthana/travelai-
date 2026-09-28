from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import init_db
from routes.auth_routes import router as auth_router
from routes.trip_routes import router as trip_router


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(auth_router)
app.include_router(trip_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "TravelAI",
        "environment": settings.environment,
    }