from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os, shutil, uuid

from database.database import get_db
from database.models import Propiedad, Cliente, Propietario, Agente, Imagen
from modulo_inmuebles import schemas
from auth import get_current_tenant_user, get_password_hash
from gestion_usuarios.models import Usuario

UPLOAD_DIR = "uploads"

router = APIRouter(prefix="/modulo_inmuebles", tags=["Módulo de Inmuebles"])

# --- Propiedades Multi-Tenant ---

@router.get("/propiedades/catalogo", response_model=List[schemas.PropiedadResponse])
def get_catalogo(estado: str = "Disponible", db: Session = Depends(get_db)):
    """Obtiene el catálogo público de todas las propiedades disponibles (Cross-Tenant)"""
    propiedades = db.query(Propiedad).filter(Propiedad.estado == estado).all()
    return propiedades

@router.get("/propiedades", response_model=List[schemas.PropiedadResponse])
def get_propiedades(
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_tenant_user)
):
    """Obtiene SOLO las propiedades del Tenant del usuario autenticado"""
    propiedades = db.query(Propiedad).filter(Propiedad.id_tenant == current_user.id_tenant).all()
    return propiedades

@router.post("/propiedades", response_model=schemas.PropiedadResponse, status_code=status.HTTP_201_CREATED)
def create_propiedad(
    prop: schemas.PropiedadCreate, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_tenant_user)
):
    """Crea una propiedad asociándola automáticamente al Tenant del usuario"""
    
    # Validación Multi-Tenant: Límite de Propiedades
    tenant = current_user.tenant
    current_count = db.query(Propiedad).filter(Propiedad.id_tenant == tenant.id_tenant).count()
    if current_count >= tenant.max_propiedades:
        raise HTTPException(
            status_code=403, 
            detail=f"Límite de propiedades alcanzado para tu plan ({tenant.max_propiedades})."
        )

    new_prop = Propiedad(**prop.model_dump(), id_tenant=current_user.id_tenant)
    db.add(new_prop)
    db.commit()
    db.refresh(new_prop)
    return new_prop

# --- Clientes, Propietarios, Agentes ---

@router.get("/clientes")
def get_clientes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    clientes = db.query(Cliente).join(Usuario).filter(Usuario.id_tenant == current_user.id_tenant).all()
    return [{"id_cliente": c.id_cliente, "ci_usuario": c.ci_usuario, "nombre": c.usuario.nombre, "correo": c.usuario.correo} for c in clientes]

@router.post("/clientes")
def create_cliente(data: schemas.ClienteCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    user = db.query(Usuario).filter(Usuario.ci == data.ci_usuario).first()
    if not user and data.nombre and data.correo and data.password:
        user = Usuario(
            ci=data.ci_usuario,
            nombre=data.nombre,
            correo=data.correo,
            telefono=data.telefono,
            id_rol=3, # Cliente
            id_tenant=current_user.id_tenant,
            password_hash=get_password_hash(data.password)
        )
        db.add(user)
        db.commit()
    elif not user:
        raise HTTPException(status_code=400, detail="El usuario con este CI no existe. Por favor regístrelo primero en la sección 'Gestión de Usuarios'.")
        
    nuevo = Cliente(ci_usuario=data.ci_usuario)
    db.add(nuevo)
    db.commit()
    return nuevo

@router.delete("/clientes/{id}")
def delete_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id_cliente == id).first()
    if cliente:
        db.delete(cliente)
        db.commit()
    return {"ok": True}

@router.get("/propietarios")
def get_propietarios(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    propietarios = db.query(Propietario).join(Usuario).filter(Usuario.id_tenant == current_user.id_tenant).all()
    return [{"id_propietario": p.id_propietario, "ci_usuario": p.ci_usuario, "nombre": p.usuario.nombre, "correo": p.usuario.correo} for p in propietarios]

@router.post("/propietarios")
def create_propietario(data: schemas.PropietarioCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    user = db.query(Usuario).filter(Usuario.ci == data.ci_usuario).first()
    if not user and data.nombre and data.correo and data.password:
        user = Usuario(
            ci=data.ci_usuario,
            nombre=data.nombre,
            correo=data.correo,
            telefono=data.telefono,
            id_rol=4, # Propietario
            id_tenant=current_user.id_tenant,
            password_hash=get_password_hash(data.password)
        )
        db.add(user)
        db.commit()
    elif not user:
        raise HTTPException(status_code=400, detail="El usuario con este CI no existe. Por favor regístrelo primero en la sección 'Gestión de Usuarios'.")
    else:
        # Si el usuario ya existe, actualizar su etiqueta visual de Rol a Propietario (4)
        user.id_rol = 4
        db.commit()
        
    nuevo = Propietario(ci_usuario=data.ci_usuario)
    db.add(nuevo)
    db.commit()
    return nuevo

@router.delete("/propietarios/{id}")
def delete_propietario(id: int, db: Session = Depends(get_db)):
    prop = db.query(Propietario).filter(Propietario.id_propietario == id).first()
    if prop:
        db.delete(prop)
        db.commit()
    return {"ok": True}

@router.get("/agentes")
def get_agentes(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    agentes = db.query(Agente).join(Usuario).filter(Usuario.id_tenant == current_user.id_tenant).all()
    return [{"id_agente": a.id_agente, "nombre": a.usuario.nombre, "ci": a.ci_usuario} for a in agentes]

@router.get("/propietarios_list")
def get_propietarios_list(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    propietarios = db.query(Propietario).join(Usuario).filter(Usuario.id_tenant == current_user.id_tenant).all()
    return [{"id_propietario": p.id_propietario, "nombre": p.usuario.nombre, "ci": p.ci_usuario} for p in propietarios]

@router.get("/clientes_list")
def get_clientes_list(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    clientes = db.query(Cliente).join(Usuario).filter(Usuario.id_tenant == current_user.id_tenant).all()
    return [{"id_cliente": c.id_cliente, "nombre": c.usuario.nombre, "ci": c.ci_usuario} for c in clientes]

@router.post("/agentes")
def create_agente(data: schemas.AgenteCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    user = db.query(Usuario).filter(Usuario.ci == data.ci_usuario).first()
    if not user and data.nombre and data.correo and data.password:
        user = Usuario(
            ci=data.ci_usuario,
            nombre=data.nombre,
            correo=data.correo,
            telefono=data.telefono,
            id_rol=2, # Agente
            id_tenant=current_user.id_tenant,
            password_hash=get_password_hash(data.password)
        )
        db.add(user)
        db.commit()
    elif not user:
        raise HTTPException(status_code=400, detail="El usuario no existe. Debe proporcionar nombre, correo y contraseña para crearlo.")
        
    nuevo = Agente(ci_usuario=data.ci_usuario)
    db.add(nuevo)
    db.commit()
    return nuevo

@router.delete("/agentes/{id}")
def delete_agente(id: int, db: Session = Depends(get_db)):
    ag = db.query(Agente).filter(Agente.id_agente == id).first()
    if ag:
        db.delete(ag)
        db.commit()
    return {"ok": True}

# --- Estado y Multimedia ---

from pydantic import BaseModel
class EstadoUpdate(BaseModel):
    estado: str

@router.put("/propiedades/{id_propiedad}/estado")
def update_estado(id_propiedad: int, data: EstadoUpdate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    propiedad = db.query(Propiedad).filter(Propiedad.id_propiedad == id_propiedad).first()
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    propiedad.estado = data.estado
    db.commit()
    db.refresh(propiedad)
    return propiedad

@router.post("/propiedades/{id_propiedad}/imagenes")
def upload_imagen(id_propiedad: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_tenant_user)):
    propiedad = db.query(Propiedad).filter(Propiedad.id_propiedad == id_propiedad).first()
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    url = f"/uploads/{filename}"
    nueva_imagen = Imagen(id_propiedad=id_propiedad, url=url)
    db.add(nueva_imagen)
    db.commit()
    db.refresh(nueva_imagen)
    return nueva_imagen

