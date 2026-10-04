from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os
from pathlib import Path

# Cargar variables de entorno desde .env si existe en la raíz del proyecto
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

# Leer DATABASE_URL, por defecto intentará usar SQLite si no hay .env para no romper tu entorno local
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./raices_db.db"
)

# Si es SQLite, necesitamos check_same_thread en False (para FastAPI).
# Si es PostgreSQL (en la nube), no lo necesitamos.
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
