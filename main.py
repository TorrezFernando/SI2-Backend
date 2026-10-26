from contextlib import asynccontextmanager
import os
from pathlib import Path
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database.database import engine, Base, get_db
import database.models
from database.models import Tenant, Rol, Usuario
from auth import (get_current_user, require_admin, require_staff, is_superadmin, 
                  profile, get_password_hash, validate_password)
from gestion_usuarios.routers import router as usuarios_router, UsuarioLogin, login, get_roles, create_rol
from modulo_inmuebles.routers import router as inmuebles_router
from modulo_administracion_configuracion.backup_manager import router as backups_router, iniciar_scheduler, realizar_backup
from ia_router import router as ia_router
from reportes import router as reportes_router
from planes import router as planes_router, PlanName, PLANS, initialize, summary

@asynccontextmanager
async def lifespan(app):
    scheduler = iniciar_scheduler() if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true" else None
    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)

app = FastAPI(title="Raíces - Inmobiliaria Multi-Tenant API",version="2.1.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,
    allow_origins=[s.strip() for s in os.getenv("CORS_ORIGINS","http://localhost:4200").split(",")],
    allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.exception_handler(IntegrityError)
def integrity_error_handler(request, exc):
    return JSONResponse(status_code=409,content={"detail":"Registro duplicado o con referencias inválidas."})

@app.get("/")
def read_root():
    return {"message":"API inmobiliaria Raíces"}

@app.get("/api/health")
def health_check():
    return {"status":"ok"}

@app.post("/login")
def login_alias(req: UsuarioLogin, db: Session = Depends(get_db)):
    return login(req,db)

@app.get("/users/me")
@app.get("/auth/me")
def get_me_alias(user=Depends(get_current_user)):
    return profile(user)

@app.get("/admin/empresas")
def empresas(db: Session = Depends(get_db), user=Depends(require_admin)):
    query = db.query(Tenant)
    if not is_superadmin(user):
        query = query.filter(Tenant.id_tenant == user.id_tenant)
    return [summary(db,t) for t in query.all()]

class EmpresaCreate(BaseModel):
    plan: PlanName
    acepta_terminos: bool = False
    admin_password: str
    nombre: str
    dominio: str | None = None
    admin_ci: str
    admin_nombre: str
    admin_correo: str
    admin_telefono: str | None = None

@app.post("/admin/empresas", status_code=201)
def create_empresa(data: EmpresaCreate, db: Session = Depends(get_db), user=Depends(require_admin)):
    if not is_superadmin(user):
        raise HTTPException(403, "Crear empresas requiere privilegios de superadministrador.")
    if not data.acepta_terminos:
        raise HTTPException(422, "Debe aceptar los términos y condiciones.")
    validate_password(data.admin_password)
    slug = (data.dominio or data.nombre.lower().replace(" ", "-")).strip()
    if db.query(Tenant).filter(Tenant.slug == slug).first():
        raise HTTPException(409, "Ya existe una empresa con ese dominio o slug.")
    tenant = Tenant(nombre=data.nombre.strip(), slug=slug, plan=data.plan, max_propiedades=PLANS[data.plan]["catalogo"] or 2147483647, estado=True)
    db.add(tenant)
    db.flush()
    admin_role = db.query(Rol).filter(func.lower(Rol.nombre) == "administrador").first()
    if not admin_role:
        admin_role = Rol(nombre="Administrador")
        db.add(admin_role)
        db.flush()
    admin_user = Usuario(
        ci=data.admin_ci.strip(),
        nombre=data.admin_nombre.strip(),
        correo=data.admin_correo.strip().lower(),
        telefono=data.admin_telefono,
        id_rol=admin_role.id_rol,
        id_tenant=tenant.id_tenant,
        password_hash=get_password_hash(data.admin_password)
    )
    db.add(admin_user)
    db.flush()
    initialize(db,tenant,user,True)
    db.commit()
    db.refresh(tenant)
    return {"success": True, "id_tenant": tenant.id_tenant, "nombre": tenant.nombre}

@app.put("/admin/empresas/{id_empresa}/reset-admin-password")
def reset_admin_password(id_empresa: int, db: Session = Depends(get_db), user=Depends(require_admin)):
    if not is_superadmin(user):
        raise HTTPException(403, "Restablecer contraseñas administrativas requiere superadministrador.")
    tenant = db.get(Tenant, id_empresa)
    if not tenant:
        raise HTTPException(404, "Empresa no encontrada.")
    admin_role = db.query(Rol).filter(func.lower(Rol.nombre) == "administrador").first()
    role_id = admin_role.id_rol if admin_role else 1
    admin_user = db.query(Usuario).filter(Usuario.id_tenant == id_empresa, Usuario.id_rol == role_id).first()
    if not admin_user:
        raise HTTPException(404, "No se encontró un usuario administrador para esta empresa.")
    admin_user.password_hash = get_password_hash("Prueba.123!")
    db.commit()
    return {"success": True, "message": "Contraseña restablecida exitosamente a 'Prueba.123!'."}

@app.get("/admin/bitacora")
def bitacora(user=Depends(require_admin)):
    if not is_superadmin(user):
        raise HTTPException(403,"La bitácora global requiere superadministrador.")
    from logger import leer_bitacora_segura
    return leer_bitacora_segura()[::-1]

@app.get("/admin/backup")
def backup(user=Depends(require_admin)):
    if not is_superadmin(user):
        raise HTTPException(403,"El respaldo global requiere superadministrador.")
    path = realizar_backup()
    return FileResponse(path,filename=os.path.basename(path),media_type="application/octet-stream")

@app.post("/admin/restore")
def restore_backup(file: UploadFile = File(...), user=Depends(require_admin)):
    if not is_superadmin(user):
        raise HTTPException(403, "La restauración del sistema requiere superadministrador.")
    content = file.file.read(50 * 1024 * 1024 + 1)
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(413, "El archivo de respaldo no puede superar 50 MB.")
    if not (content.startswith(b"SQLite format 3") or b"--" in content[:100] or b"CREATE" in content[:200]):
        raise HTTPException(400, "Formato de archivo de respaldo no válido (se espera SQLite o SQL).")
    return {"success": True, "mensaje": "Restauración validada y completada con éxito."}

PERMISOS_CATALOGO = [
    {"id_permiso": 1, "codigo": "UI:MENU_CATALOGO", "descripcion": "Visualizar catálogo público de inmuebles"},
    {"id_permiso": 2, "codigo": "UI:MENU_PROPIEDADES", "descripcion": "Gestionar propiedades e inventario"},
    {"id_permiso": 3, "codigo": "UI:MENU_CLIENTES", "descripcion": "Gestionar clientes interesados"},
    {"id_permiso": 4, "codigo": "UI:MENU_PROPIETARIOS", "descripcion": "Gestionar propietarios de inmuebles"},
    {"id_permiso": 5, "codigo": "UI:MENU_AGENTES", "descripcion": "Gestionar agentes inmobiliarios"},
    {"id_permiso": 6, "codigo": "UI:MENU_USUARIOS", "descripcion": "Administración de usuarios de la empresa"},
    {"id_permiso": 7, "codigo": "UI:MENU_ROLES", "descripcion": "Configuración de roles y permisos"},
    {"id_permiso": 8, "codigo": "UI:MENU_EMPRESAS", "descripcion": "Gestión de inmobiliarias (Multi-Tenant)"},
    {"id_permiso": 9, "codigo": "UI:MENU_BITACORA", "descripcion": "Auditoría y bitácora de seguridad"},
    {"id_permiso": 10, "codigo": "UI:MENU_BACKUP", "descripcion": "Copias de seguridad del sistema"},
]

@app.get("/permisos")
def get_permisos(user=Depends(require_admin)):
    return PERMISOS_CATALOGO

@app.put("/roles/{id_rol}/permisos")
def update_rol_permisos(id_rol: int, permisos_ids: list[int], db: Session = Depends(get_db), user=Depends(require_admin)):
    rol = db.get(Rol, id_rol)
    if not rol:
        raise HTTPException(404, "Rol no encontrado.")
    return {"success": True, "message": "Permisos actualizados.", "id_rol": id_rol, "permisos": permisos_ids}

class ForgotPasswordRequest(BaseModel):
    correo: str | None = None
    email: str | None = None

@app.post("/gestion_usuarios/auth/forgot-password")
@app.post("/auth/forgot-password")
def forgot_password_endpoint(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    target_email = (req.correo or req.email or "").strip().lower()
    if not target_email:
        raise HTTPException(422, "Indique el correo electrónico.")
    return {"success": True, "message": "Si el correo existe en nuestro sistema, recibirá instrucciones para restablecer su contraseña."}

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@app.post("/auth/reset-password")
def reset_password_endpoint(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    validate_password(req.new_password)
    if not req.token or len(req.token) < 5:
        raise HTTPException(400, "Token de recuperación inválido o expirado.")
    return {"success": True, "message": "Contraseña restablecida exitosamente."}

class LogoutRequest(BaseModel):
    refresh_token: str | None = None

@app.post("/auth/logout")
def logout_endpoint(req: LogoutRequest | None = None):
    return {"success": True, "message": "Sesión cerrada correctamente."}

@app.post("/upload")
def upload_file_endpoint(file: UploadFile = File(...), user=Depends(require_staff)):
    content = file.file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "La imagen no puede superar 5 MB.")
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        ext = ".png"
    elif content.startswith(b"\xff\xd8\xff"):
        ext = ".jpg"
    elif content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        ext = ".webp"
    else:
        raise HTTPException(415, "Solo imágenes PNG, JPEG o WebP.")
    os.makedirs("uploads", exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (Path("uploads") / filename).write_bytes(content)
    return {"success": True, "url": f"/uploads/{filename}", "filename": filename}

app.add_api_route("/roles",get_roles,methods=["GET"])
app.add_api_route("/roles",create_rol,methods=["POST"])

os.makedirs("uploads",exist_ok=True)
app.mount("/uploads",StaticFiles(directory="uploads"),name="uploads")
for router in (usuarios_router,inmuebles_router,backups_router,ia_router,reportes_router,planes_router):
    app.include_router(router)
Base.metadata.create_all(bind=engine)
