from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.projects import router as project_router
from core.config import settings
from api.datasets import router as dataset_router

app = FastAPI(title="SECOND WORLD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(project_router)
app.include_router(dataset_router)