from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/propietarios",
    tags=["Propietarios"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/", response_model=list[schemas.PropietarioResponse])
def read_propietarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Propietario).offset(skip).limit(limit).all()

@router.post("/", response_model=schemas.PropietarioResponse, status_code=status.HTTP_201_CREATED)
def create_propietario(propietario: schemas.PropietarioCreate, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.ci == propietario.ci_usuario).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    db_propietario = db.query(models.Propietario).filter(models.Propietario.ci_usuario == propietario.ci_usuario).first()
    if db_propietario:
        raise HTTPException(status_code=400, detail="El propietario ya existe")
    
    new_propietario = models.Propietario(ci_usuario=propietario.ci_usuario)
    db.add(new_propietario)
    db.commit()
    db.refresh(new_propietario)
    return new_propietario

@router.delete("/{id_propietario}")
def delete_propietario(id_propietario: int, db: Session = Depends(get_db)):
    db_propietario = db.query(models.Propietario).filter(models.Propietario.id_propietario == id_propietario).first()
    if not db_propietario:
        raise HTTPException(status_code=404, detail="Propietario no encontrado")
    
    db.delete(db_propietario)
    db.commit()
    return {"message": "Propietario eliminado"}
