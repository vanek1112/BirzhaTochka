import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import storage, Storage
from app.routes import public, user, admin

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Admin API Key: {storage.admin_api_key}")
    print(f"Admin API Key via print: {storage.admin_api_key}")
    yield
    logger.info("Bye.")

app = FastAPI(lifespan=lifespan, title="Toy exchange", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(public.router)
app.include_router(user.router)
app.include_router(admin.router)

if __name__ == "__main__":
    import uvicorn
    print(f"Admin API Key: {storage.admin_api_key}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
