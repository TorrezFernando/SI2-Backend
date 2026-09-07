from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database.database import engine, Base
import database.models  # Esto importa todos los modelos modulares

# Importar routers modulares
from gestion_usuarios.routers import router as usuarios_router
from modulo_inmuebles.routers import router as inmuebles_router

app = FastAPI(title="Raíces - Inmobiliaria Multi-Tenant API", version="2.0.0")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

@app.exception_handler(IntegrityError)
def integrity_error_handler(request, exc: IntegrityError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Error de integridad en la base de datos (posible duplicado o referencia no encontrada)."},
    )

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API Multi-Tenant de Inmobiliaria Raíces"}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# Mount uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include modular routers
app.include_router(usuarios_router)
app.include_router(inmuebles_router)

# Crear tablas si no existen (en prod usar Alembic)
Base.metadata.create_all(bind=engine)
