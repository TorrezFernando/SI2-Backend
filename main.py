from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta

# Importaciones locales
from database.database import engine, get_db
from database import models
from auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
import schemas
from logger import log_accion_segura, leer_bitacora_segura
from fastapi import Request

app = FastAPI(title="Raíces - Inmobiliaria API", version="1.0.0")

# CORS setup for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Ignorar rutas estáticas o de salud
    if request.url.path in ["/api/health", "/docs", "/openapi.json"]:
        return await call_next(request)
        
    # Extraer IP
    ip = request.client.host if request.client else "Desconocida"
    
    # Extraer Usuario (Intentar leer del header Authorization sin requerir DB)
    usuario = "Anónimo"
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            usuario = payload.get("sub", "Anónimo")
        except JWTError:
            pass
            
    # Extraer Acción
    accion = f"{request.method} {request.url.path}"
    
    # Registrar de forma asíncrona pero sin bloquear si falla
    try:
        log_accion_segura(ip, usuario, accion)
    except Exception as e:
        print(f"Error guardando bitacora: {e}")
        
    response = await call_next(request)
    return response

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
        id_empresa=user.id_empresa,
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
        data={"sub": user.correo, "rol": user.id_rol, "id_empresa": user.id_empresa}, expires_delta=access_token_expires
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

@app.get("/users/me", response_model=schemas.UsuarioResponse)
def get_user_profile(current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtiene el perfil del usuario autenticado, incluyendo sus permisos dinámicos."""
    permisos = []
    if current_user.rol:
        for p in current_user.rol.permisos:
            permisos.append(p.codigo)
            
    # Hacemos una copia para inyectar los permisos sin fallar el modelo de sqlalchemy
    user_dict = {
        "ci": current_user.ci,
        "id_empresa": current_user.id_empresa,
        "nombre": current_user.nombre,
        "correo": current_user.correo,
        "telefono": current_user.telefono,
        "id_rol": current_user.id_rol,
        "permisos": permisos
    }
    return user_dict

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
    """CU-05: Obtener roles. Filtrados por empresa (SaaS) o todos si es SuperAdmin"""
    if current_user.id_rol == 1:
        roles_db = db.query(models.Rol).all()
    else:
        # Solo roles de su empresa o roles globales (id_empresa is null)
        roles_db = db.query(models.Rol).filter((models.Rol.id_empresa == current_user.id_empresa) | (models.Rol.id_empresa == None)).all()
        
    resultado = []
    for r in roles_db:
        resultado.append({
            "id_rol": r.id_rol,
            "nombre": r.nombre,
            "id_empresa": r.id_empresa,
            "permisos": [p.id_permiso for p in r.permisos]
        })
    return resultado

@app.post("/roles", response_model=schemas.RolResponse)
def create_rol(rol: schemas.RolCreate, current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """CU-05: Crear un nuevo rol para su propia empresa (o global si es SuperAdmin)"""
    if current_user.id_rol not in [1, 2]: # Solo SuperAdmin o Admin Empresa
        raise HTTPException(status_code=403, detail="Permiso denegado. Solo administradores.")
        
    db_rol = db.query(models.Rol).filter(models.Rol.nombre == rol.nombre).first()
    if db_rol:
        raise HTTPException(status_code=400, detail="Este rol ya existe")
    
    # Si es SuperAdmin puede crear rol global, de lo contrario se asigna a su empresa
    empresa_id = None if current_user.id_rol == 1 else current_user.id_empresa
    
    new_rol = models.Rol(nombre=rol.nombre, id_empresa=empresa_id)
    db.add(new_rol)
    db.commit()
    db.refresh(new_rol)
    return new_rol

# ==========================================
# ENDPOINTS DE BITACORA SEGURA (CU-06)
# ==========================================

@app.get("/admin/bitacora")
def get_bitacora_segura(dev_key: str, current_user: models.Usuario = Depends(get_current_user)):
    """Punto 3: Obtener la bitácora segura desencriptada. Solo SuperAdmin con la llave correcta."""
    if current_user.id_rol != 1:
        raise HTTPException(status_code=403, detail="Permiso denegado. Solo el Super Administrador puede ver la bitácora.")
        
    try:
        registros = leer_bitacora_segura(dev_key)
        return registros
    except ValueError:
        raise HTTPException(status_code=403, detail="Llave de desarrollador inválida")

# ==========================================
# ENDPOINTS DE PERMISOS (RBAC/CBAC)
# ==========================================

@app.get("/permisos", response_model=list[schemas.PermisoResponse])
def get_permisos(current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Obtener todos los componentes/permisos registrables del sistema"""
    return db.query(models.Permiso).all()

@app.post("/permisos", response_model=schemas.PermisoResponse)
def create_permiso(permiso: schemas.PermisoCreate, current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Registrar un nuevo componente protegible en el sistema (Solo Super Admin)"""
    if current_user.id_rol != 1:
        raise HTTPException(status_code=403, detail="Solo Super Admin puede crear permisos globales")
    
    db_permiso = db.query(models.Permiso).filter(models.Permiso.codigo == permiso.codigo).first()
    if db_permiso:
        raise HTTPException(status_code=400, detail="Código de permiso ya existe")
        
    new_permiso = models.Permiso(**permiso.model_dump())
    db.add(new_permiso)
    db.commit()
    db.refresh(new_permiso)
    return new_permiso

from typing import List

@app.put("/roles/{id_rol}/permisos")
def update_rol_permisos(id_rol: int, permisos_ids: List[int], current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """Asigna/Revoca permisos a un rol específico"""
    if current_user.id_rol not in [1, 2]:
        raise HTTPException(status_code=403, detail="Solo administradores")
        
    rol = db.query(models.Rol).filter(models.Rol.id_rol == id_rol).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
        
    # Validar que no está modificando un rol de otra empresa
    if current_user.id_rol != 1 and rol.id_empresa != current_user.id_empresa:
        raise HTTPException(status_code=403, detail="No puede modificar roles de otra empresa")
        
    # Limpiar y asignar nuevos permisos
    rol.permisos.clear()
    if permisos_ids:
        nuevos_permisos = db.query(models.Permiso).filter(models.Permiso.id_permiso.in_(permisos_ids)).all()
        rol.permisos.extend(nuevos_permisos)
        
    db.commit()
    return {"message": "Permisos actualizados exitosamente", "rol_id": id_rol}

# ==========================================
# ENDPOINTS DE PROPIEDADES (BÚSQUEDA / CATÁLOGO)
# ==========================================

from typing import Optional
from sqlalchemy import cast, Integer, Float, and_
from fastapi import Header

@app.get("/modulo_inmuebles/propiedades/catalogo", response_model=list[schemas.PropiedadCatalogoResponse])
def get_catalogo_propiedades(
    tipo_operacion: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    cuartos: Optional[int] = None,
    banos: Optional[int] = None,
    salas: Optional[int] = None,
    metros_min: Optional[float] = None,
    metros_max: Optional[float] = None,
    zona: Optional[str] = None,
    amueblado: Optional[bool] = None,
    servicios_basicos: Optional[bool] = None,
    x_tenant_id: Optional[int] = Header(None, alias="X-Tenant-ID", description="ID de la Empresa/Agencia SaaS"),
    db: Session = Depends(get_db)
):
    """
    Obtiene el catálogo de propiedades con filtros avanzados.
    Soporta filtrado por atributos extendidos (EAV) y aislamiento Multi-tenant.
    """
    query = db.query(models.Propiedad).filter(models.Propiedad.estado == 'Disponible')
    
    if x_tenant_id is not None:
        query = query.filter(models.Propiedad.id_empresa == x_tenant_id)
    
    if tipo_operacion:
        query = query.filter(models.Propiedad.tipo_operacion == tipo_operacion)
    
    if precio_min is not None:
        query = query.filter(models.Propiedad.precio >= precio_min)
        
    if precio_max is not None:
        query = query.filter(models.Propiedad.precio <= precio_max)
        
    if cuartos is not None:
        query = query.filter(models.Propiedad.caracteristicas.any(
            and_(models.Caracteristica.nombre == 'Cuartos', cast(models.Caracteristica.valor, Integer) >= cuartos)
        ))
        
    if banos is not None:
        query = query.filter(models.Propiedad.caracteristicas.any(
            and_(models.Caracteristica.nombre == 'Baños', cast(models.Caracteristica.valor, Integer) >= banos)
        ))
        
    if salas is not None:
        query = query.filter(models.Propiedad.caracteristicas.any(
            and_(models.Caracteristica.nombre == 'Salas', cast(models.Caracteristica.valor, Integer) >= salas)
        ))
        
    if metros_min is not None:
        query = query.filter(models.Propiedad.caracteristicas.any(
            and_(models.Caracteristica.nombre == 'Metros Cuadrados', cast(models.Caracteristica.valor, Float) >= metros_min)
        ))
        
    if metros_max is not None:
        query = query.filter(models.Propiedad.caracteristicas.any(
            and_(models.Caracteristica.nombre == 'Metros Cuadrados', cast(models.Caracteristica.valor, Float) <= metros_max)
        ))
        
    if zona:
        query = query.filter(models.Propiedad.caracteristicas.any(
            and_(models.Caracteristica.nombre == 'Zona', models.Caracteristica.valor == zona)
        ))
        
    if amueblado is not None:
        valor_amueblado = 'Sí' if amueblado else 'No'
        query = query.filter(models.Propiedad.caracteristicas.any(
            and_(models.Caracteristica.nombre == 'Amueblado', models.Caracteristica.valor == valor_amueblado)
        ))
        
    if servicios_basicos is not None:
        valor_servicios = 'Sí' if servicios_basicos else 'No'
        query = query.filter(models.Propiedad.caracteristicas.any(
            and_(models.Caracteristica.nombre == 'Servicios Básicos', models.Caracteristica.valor == valor_servicios)
        ))

    propiedades = query.all()
    return propiedades
