from fastapi import FastAPI

from app.database import Base, engine
from app.routers.batches import router as batches_router

app = FastAPI(
    title="DigiPath Batch Tracker",
    version="1.0.0",
)

Base.metadata.create_all(bind=engine)

app.include_router(batches_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}