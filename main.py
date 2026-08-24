from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta

# Importaciones locales
from database.database import engine, get_db
from database import models
from auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
import schemas

app = FastAPI(title="Raíces - Inmobiliaria API", version="1.0.0")

# CORS setup for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de Inmobiliaria Raíces"}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# ==========================================
# ENDPOINTS DE AUTENTICACIÓN (SPRINT 0)
# ==========================================

@app.post("/register", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    # Verificar si el usuario ya existe
    db_user = db.query(models.Usuario).filter((models.Usuario.correo == user.correo) | (models.Usuario.ci == user.ci)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El correo o CI ya está registrado")
    
    # Hashear contraseña y crear usuario
    hashed_password = get_password_hash(user.password)
    new_user = models.Usuario(
        ci=user.ci,
        nombre=user.nombre,
        correo=user.correo,
        telefono=user.telefono,
        id_rol=user.id_rol,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    # Buscar usuario por correo
    user = db.query(models.Usuario).filter(models.Usuario.correo == user_credentials.correo).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    
    # Verificar contraseña
    if not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
    
    # Generar Token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.correo, "rol": user.id_rol}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

from pydantic import BaseModel, Field, EmailStr, field_validator
import re

class PasswordUpdate(BaseModel):
    nueva_password: str = Field(..., min_length=8)

    @field_validator('nueva_password')
    def validate_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$", v):
            raise ValueError('La contraseña no cumple con los requisitos de seguridad')
        return v

@app.put("/users/me/password")
def change_password(data: PasswordUpdate, current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """CU-04: Cambiar contraseña (Perfil)"""
    hashed_password = get_password_hash(data.nueva_password)
    current_user.password_hash = hashed_password
    db.commit()
    return {"message": "Contraseña actualizada exitosamente"}

class ForgotPasswordRequest(BaseModel):
    correo: EmailStr

@app.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """CU-03: Recuperar contraseña"""
    user = db.query(models.Usuario).filter(models.Usuario.correo == data.correo).first()
    if not user:
        # Por seguridad no revelamos si existe o no el correo
        return {"message": "Si el correo existe, se han enviado las instrucciones de recuperación."}
    
    # Aquí iría la lógica para enviar un email con SendGrid/SMTP
    return {"message": "Si el correo existe, se han enviado las instrucciones de recuperación."}

# ==========================================
# ENDPOINTS DE ROLES (CU-05)
# ==========================================

@app.get("/roles", response_model=list[schemas.RolResponse])
def get_roles(current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """CU-05: Obtener todos los roles"""
    if current_user.id_rol != 1:
        raise HTTPException(status_code=403, detail="Permiso denegado. Solo administradores.")
    return db.query(models.Rol).all()

@app.post("/roles", response_model=schemas.RolResponse)
def create_rol(rol: schemas.RolCreate, current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """CU-05: Crear un nuevo rol"""
    if current_user.id_rol != 1:
        raise HTTPException(status_code=403, detail="Permiso denegado. Solo administradores.")
        
    db_rol = db.query(models.Rol).filter(models.Rol.nombre == rol.nombre).first()
    if db_rol:
        raise HTTPException(status_code=400, detail="Este rol ya existe")
    
    new_rol = models.Rol(nombre=rol.nombre)
    db.add(new_rol)
    db.commit()
    db.refresh(new_rol)
    return new_rol
