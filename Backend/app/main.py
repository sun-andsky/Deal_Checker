from fastapi import FastAPI
from app.database import Base, engine
from app.routers.files import router as files_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Deal Checker")
app.include_router(files_router, prefix="/api")
