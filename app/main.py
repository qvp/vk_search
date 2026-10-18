from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db
from app.paths import STATIC_DIR
from app.routers import router
from app.data_export import router as dx_router
from app.version import VERSION


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    lifespan=lifespan,
    version=VERSION,
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(router)
app.include_router(dx_router)
