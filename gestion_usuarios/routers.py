from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
import re

from database.database import get_db
from database.models import Usuario, Rol
from gestion_usuarios import schemas
from auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user

router = APIRouter(prefix="/gestion_usuarios", tags=["Gestión de Usuarios"])

from pydantic import BaseModel
class UsuarioLogin(BaseModel):
    correo: str
    password: str

@router.post("/auth/register", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(Usuario).filter((Usuario.correo == user.correo) | (Usuario.ci == user.ci)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El correo o CI ya está registrado")
    
    hashed_password = get_password_hash(user.password)
    new_user = Usuario(
        ci=user.ci,
        nombre=user.nombre,
        correo=user.correo,
        telefono=user.telefono,
        id_rol=user.id_rol,
        id_tenant=user.id_tenant,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/auth/login")
def login(user_credentials: UsuarioLogin, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.correo == user_credentials.correo).first()
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.correo, "rol": user.id_rol, "tenant_id": user.id_tenant}, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "tenant_id": user.id_tenant,
        "tenant_nombre": user.tenant.nombre if user.tenant else None
    }

@router.get("/roles")
def get_roles(db: Session = Depends(get_db)):
    return db.query(Rol).all()

@router.post("/roles")
def create_rol(rol: schemas.RolCreate, db: Session = Depends(get_db)):
    new_rol = Rol(**rol.model_dump())
    db.add(new_rol)
    db.commit()
    db.refresh(new_rol)
    return new_rol

from pydantic import BaseModel
class PasswordUpdate(BaseModel):
    nueva_password: str

@router.put("/users/me/password")
def update_password(data: PasswordUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    current_user.password_hash = get_password_hash(data.nueva_password)
    db.commit()
    return {"message": "Contraseña actualizada exitosamente"}

from typing import List

@router.get("/usuarios", response_model=List[schemas.UsuarioResponse])
def get_usuarios(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return db.query(Usuario).filter(Usuario.id_tenant == current_user.id_tenant).all()

@router.post("/usuarios", response_model=schemas.UsuarioResponse)
def create_usuario(data: schemas.UsuarioCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    db_user = db.query(Usuario).filter(Usuario.ci == data.ci).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe.")
    
    new_user = Usuario(
        ci=data.ci,
        nombre=data.nombre,
        correo=data.correo,
        telefono=data.telefono,
        id_rol=data.id_rol,
        id_tenant=current_user.id_tenant,
        password_hash=get_password_hash(data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
