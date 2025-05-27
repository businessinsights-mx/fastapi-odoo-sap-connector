from fastapi import FastAPI
from models import Base
from sqlalchemy import create_engine
from setting import Settings
from routes import router

app = FastAPI()
settings = Settings()

engine = create_engine(settings.POSTGRES_DSN)
Base.metadata.create_all(bind=engine)

app.include_router(router)