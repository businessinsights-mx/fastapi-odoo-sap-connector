from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from setting import Settings

settings = Settings()

engine = create_engine(settings.POSTGRES_DSN)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)