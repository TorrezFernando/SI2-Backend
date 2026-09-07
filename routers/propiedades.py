import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Optional
from sqlalchemy.orm import Session
from database.database import get_db
from database import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/propiedades",
    tags=["Propiedades"]
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# CU-11: Catálogo y filtrado (Público)
@router.get("/catalogo", response_model=list[schemas.PropiedadResponse])
def get_catalogo(
    tipo_operacion: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    estado: Optional[str] = 'Disponible',
    db: Session = Depends(get_db)
):
    query = db.query(models.Propiedad)
    
    if estado:
        query = query.filter(models.Propiedad.estado == estado)
    if tipo_operacion:
        query = query.filter(models.Propiedad.tipo_operacion == tipo_operacion)
    if precio_min is not None:
        query = query.filter(models.Propiedad.precio >= precio_min)
    if precio_max is not None:
        query = query.filter(models.Propiedad.precio <= precio_max)
        
    return query.all()

@router.get("/", response_model=list[schemas.PropiedadResponse])
def get_todas_propiedades(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Propiedad).offset(skip).limit(limit).all()

# CU-09: CRUD (Protegido)
@router.post("/", response_model=schemas.PropiedadResponse, status_code=status.HTTP_201_CREATED)
def create_propiedad(propiedad: schemas.PropiedadCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    new_propiedad = models.Propiedad(
        id_propietario=propiedad.id_propietario,
        id_agente=propiedad.id_agente,
        titulo=propiedad.titulo,
        direccion=propiedad.direccion,
        precio=propiedad.precio,
        tipo_operacion=propiedad.tipo_operacion,
        estado=propiedad.estado
    )
    db.add(new_propiedad)
    db.flush() # get id_propiedad
    
    for carac in propiedad.caracteristicas:
        new_carac = models.Caracteristica(
            id_propiedad=new_propiedad.id_propiedad,
            nombre=carac.nombre,
            valor=carac.valor
        )
        db.add(new_carac)
        
    db.commit()
    db.refresh(new_propiedad)
    return new_propiedad

# CU-13: Actualizar Estado (Protegido)
@router.put("/{id_propiedad}/estado", response_model=schemas.PropiedadResponse)
def update_estado(id_propiedad: int, update_data: schemas.PropiedadUpdate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    propiedad = db.query(models.Propiedad).filter(models.Propiedad.id_propiedad == id_propiedad).first()
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        
    propiedad.estado = update_data.estado
    db.commit()
    db.refresh(propiedad)
    return propiedad

# CU-10: Cargar Recursos Multimedia (Protegido)
@router.post("/{id_propiedad}/imagenes", response_model=schemas.ImagenResponse)
def upload_imagen(id_propiedad: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    propiedad = db.query(models.Propiedad).filter(models.Propiedad.id_propiedad == id_propiedad).first()
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    url = f"/uploads/{filename}"
    nueva_imagen = models.Imagen(id_propiedad=id_propiedad, url=url)
    db.add(nueva_imagen)
    db.commit()
    db.refresh(nueva_imagen)
    
    return nueva_imagen
