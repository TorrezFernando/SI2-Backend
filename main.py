from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database.database import engine, Base
import database.models  # Esto importa todos los modelos modulares

# Importar routers modulares
from gestion_usuarios.routers import router as usuarios_router
from modulo_inmuebles.routers import router as inmuebles_router
from modulo_administracion_configuracion.backup_manager import router as backups_router
from modulo_administracion_configuracion.backup_manager import iniciar_scheduler
from ia_router import router as ia_router

app = FastAPI(title="Raíces - Inmobiliaria Multi-Tenant API", version="2.0.0")

# Iniciar planificador de tareas (backups automáticos, etc)
iniciar_scheduler()

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

from pydantic import BaseModel
class LoginAliasReq(BaseModel):
    correo: str
    password: str

from fastapi import Depends
from sqlalchemy.orm import Session
from database.database import get_db
from auth import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from database.models import Usuario
from datetime import timedelta
import logging

@app.post("/login")
def login_alias(req: LoginAliasReq, db: Session = Depends(get_db)):
    # Alias para compatibilidad con Angular
    correo_req = req.correo.strip()
    password_req = req.password.strip()
    print(f"DEBUG LOGIN: Intentando login con correo='{correo_req}', password='{password_req}'")
    
    user = db.query(Usuario).filter(Usuario.correo == correo_req).first()
    if not user:
        print("DEBUG LOGIN: Usuario no encontrado")
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
    print(f"DEBUG LOGIN: Usuario encontrado, hash={user.password_hash}")
    
    if not verify_password(password_req, str(user.password_hash)):
        print("DEBUG LOGIN: Contraseña incorrecta")
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    access_token = create_access_token(
        data={"sub": user.correo, "rol": user.id_rol, "tenant_id": user.id_tenant}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # Angular frontend necesita los permisos en el modelo (simulado aquí)
    permisos = ["admin_dashboard"] if user.id_rol == 1 else []
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/users/me")
@app.get("/auth/me")
def get_me_alias(current_user: Usuario = Depends(get_current_user)):
    # Alias para compatibilidad con Angular y Móvil
    permisos = []
    if current_user.id_rol == 1:
        # Permisos que Angular verifica en layout.html
        permisos = [
            "UI:MENU_EMPRESAS", "UI:MENU_USUARIOS", "UI:MENU_ROLES", 
            "UI:MENU_BITACORA", "UI:MENU_CATALOGO", "UI:MENU_CLIENTES", 
            "UI:MENU_PROPIETARIOS", "UI:MENU_AGENTES", "UI:MENU_PROPIEDADES",
            "UI:MENU_BACKUP"
        ]
        
    print(f"DEBUG USERS/ME: Devolviendo perfil para {current_user.correo} con rol {current_user.id_rol} y permisos {permisos}")
        
    return {
        "id": current_user.id,
        "email": current_user.correo,
        "full_name": current_user.nombre,
        "id_rol": current_user.id_rol,
        "id_tenant": current_user.id_tenant,
        "permisos": permisos
    }

from fastapi.responses import FileResponse
from modulo_administracion_configuracion.backup_manager import realizar_backup
from database.models import Tenant
from logger import leer_bitacora_segura
import os

@app.get("/admin/bitacora")
def get_bitacora_endpoint(dev_key: str, current_user: Usuario = Depends(get_current_user)):
    if current_user.id_rol != 1:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Sin permisos")
    try:
        registros = leer_bitacora_segura(dev_key)
        # Reverse to show newest first
        return registros[::-1]
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Llave inválida")

@app.get("/admin/empresas")
def get_empresas(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    if current_user.id_rol != 1:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Sin permisos")
    
    empresas = db.query(Tenant).all()
    return [{"id_tenant": t.id_tenant, "nombre": t.nombre} for t in empresas]

@app.get("/reportes/guardados")
def get_reportes_guardados():
    return []

from typing import Dict, Any
from database.models import Propiedad

@app.post("/reportes/generar")
def generar_reporte_preview(config: Dict[str, Any], db: Session = Depends(get_db)):
    entidad = config.get("entidad", "propiedades")
    if entidad == "usuarios":
        usuarios = db.query(Usuario).limit(15).all()
        data = []
        for u in usuarios:
            data.append({
                "ci": u.ci,
                "nombre": u.nombre,
                "correo": u.correo,
                "telefono": u.telefono,
                "id_tenant": u.id_tenant
            })
        return {"success": True, "data": data}
    else:
        propiedades = db.query(Propiedad).limit(15).all()
        data = []
        for p in propiedades:
            data.append({
                "id_tenant": p.id_tenant,
                "id_propiedad": p.id,
                "titulo": p.titulo,
                "direccion": p.direccion,
                "precio": p.precio,
                "tipo_operacion": p.tipo_operacion,
                "estado": p.estado
            })
        return {"success": True, "data": data}

@app.get("/admin/backup")
def descargar_backup_endpoint(current_user: Usuario = Depends(get_current_user)):
    if current_user.id_rol != 1:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Sin permisos")
    
    backup_path = realizar_backup()
    filename = os.path.basename(backup_path)
    return FileResponse(path=backup_path, filename=filename, media_type='application/octet-stream')

# Mount uploads directory
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include modular routers
app.include_router(usuarios_router)
app.include_router(inmuebles_router)
app.include_router(backups_router)
app.include_router(ia_router)

# Crear tablas si no existen (en prod usar Alembic)
Base.metadata.create_all(bind=engine)
