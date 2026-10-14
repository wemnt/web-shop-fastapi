from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.errors import register_exception_handlers
from api.v1.router import api_router
from core.config import settings
from db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
register_exception_handlers(app)
app.include_router(api_router)
