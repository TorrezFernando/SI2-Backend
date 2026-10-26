from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Usuario, Rol, Tenant, Cliente
from gestion_usuarios import schemas
from auth import (get_password_hash, verify_password, get_current_user, require_admin,
                  tenant_scope, user_token, profile, is_superadmin)

router = APIRouter(prefix="/gestion_usuarios", tags=["Gestión de Usuarios"])

class UsuarioLogin(BaseModel):
    correo: str
    password: str
    id_tenant: int | None = None

def existing_user(db, correo, ci, tenant_id):
    return db.query(Usuario).filter(Usuario.id_tenant == tenant_id,
        or_(func.lower(Usuario.correo) == correo.strip().lower(), Usuario.ci == ci)).first()

class RegistroPublico(schemas.UsuarioCreate):
    id_rol: int | None = None

@router.post("/auth/register", response_model=schemas.UsuarioResponse, status_code=201)
def register_user(user: RegistroPublico, db: Session = Depends(get_db)):
    tenant = db.get(Tenant, user.id_tenant) if user.id_tenant else None
    if not tenant or not tenant.estado:
        raise HTTPException(422, "Seleccione una inmobiliaria activa.")
    client_role = db.query(Rol).filter(func.lower(Rol.nombre) == "cliente").first()
    if not client_role:
        raise HTTPException(503, "El rol Cliente no está configurado.")
    if user.id_rol is not None and user.id_rol != client_role.id_rol:
        raise HTTPException(403, "El registro público solo permite cuentas de cliente.")
    if existing_user(db, user.correo, user.ci, tenant.id_tenant):
        raise HTTPException(409, "El correo o CI ya está registrado en esta inmobiliaria.")
    new = Usuario(**user.model_dump(exclude={"password", "correo", "id_rol"}),
                  correo=user.correo.strip().lower(), id_rol=client_role.id_rol,
                  password_hash=get_password_hash(user.password))
    db.add(new)
    db.flush()
    db.add(Cliente(id_usuario=new.id))
    db.commit()
    db.refresh(new)
    return new

@router.post("/auth/login")
def login(user_credentials: UsuarioLogin, db: Session = Depends(get_db)):
    query = db.query(Usuario).filter(func.lower(Usuario.correo) == user_credentials.correo.strip().lower())
    if user_credentials.id_tenant is not None:
        query = query.filter(Usuario.id_tenant == user_credentials.id_tenant)
    users = query.limit(2).all()
    if len(users) != 1 or not verify_password(user_credentials.password, users[0].password_hash):
        raise HTTPException(401, "Credenciales inválidas. Si pertenece a varias inmobiliarias, indique el ID de empresa.")
    user = users[0]
    if not user.tenant or not user.tenant.estado:
        raise HTTPException(403, "La inmobiliaria se encuentra inactiva.")
    return {"access_token": user_token(user), "token_type": "bearer", "tenant_id": user.id_tenant,
            "tenant_nombre": user.tenant.nombre, "user": profile(user)}

@router.get("/roles")
def get_roles(db: Session = Depends(get_db), current_user=Depends(require_admin)):
    return db.query(Rol).all()

@router.post("/roles")
def create_rol(rol: schemas.RolCreate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    if not is_superadmin(current_user):
        raise HTTPException(403, "Los roles globales requieren superadministrador.")
    if db.query(Rol).filter(func.lower(Rol.nombre) == rol.nombre.strip().lower()).first():
        raise HTTPException(409, "El rol ya existe.")
    new = Rol(nombre=rol.nombre.strip())
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

class PasswordUpdate(BaseModel):
    nueva_password: str
    actual_password: str

@router.put("/users/me/password")
def update_password(data: PasswordUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not verify_password(data.actual_password, current_user.password_hash):
        raise HTTPException(400, "La contraseña actual es incorrecta.")
    current_user.password_hash = get_password_hash(data.nueva_password)
    db.commit()
    return {"message": "Contraseña actualizada. Inicie sesión nuevamente."}

@router.get("/usuarios", response_model=list[schemas.UsuarioResponse])
def get_usuarios(id_tenant: int | None = None, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    return db.query(Usuario).filter(Usuario.id_tenant == tenant_scope(current_user, id_tenant)).all()

@router.post("/usuarios", response_model=schemas.UsuarioResponse, status_code=201)
def create_usuario(data: schemas.UsuarioCreate, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    tenant_id = tenant_scope(current_user, data.id_tenant)
    tenant = db.get(Tenant, tenant_id)
    if not tenant or not tenant.estado or not db.get(Rol, data.id_rol):
        raise HTTPException(422, "Empresa o rol no válido.")
    from planes import check_employee_limit
    db.query(Tenant).filter(Tenant.id_tenant == tenant_id).with_for_update().first()
    check_employee_limit(db,tenant,data.id_rol)
    if existing_user(db, data.correo, data.ci, tenant_id):
        raise HTTPException(409, "El correo o CI ya está registrado en esta inmobiliaria.")
    new = Usuario(**data.model_dump(exclude={"password","id_tenant","correo"}), id_tenant=tenant_id,
                  correo=data.correo.strip().lower(), password_hash=get_password_hash(data.password))
    db.add(new)
    db.commit()
    db.refresh(new)
    return new
