from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/agentes",
    tags=["Agentes"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/", response_model=list[schemas.AgenteResponse])
def read_agentes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Agente).offset(skip).limit(limit).all()

@router.post("/", response_model=schemas.AgenteResponse, status_code=status.HTTP_201_CREATED)
def create_agente(agente: schemas.AgenteCreate, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.ci == agente.ci_usuario).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    db_agente = db.query(models.Agente).filter(models.Agente.ci_usuario == agente.ci_usuario).first()
    if db_agente:
        raise HTTPException(status_code=400, detail="El agente ya existe")
    
    new_agente = models.Agente(ci_usuario=agente.ci_usuario)
    db.add(new_agente)
    db.commit()
    db.refresh(new_agente)
    return new_agente

@router.delete("/{id_agente}")
def delete_agente(id_agente: int, db: Session = Depends(get_db)):
    db_agente = db.query(models.Agente).filter(models.Agente.id_agente == id_agente).first()
    if not db_agente:
        raise HTTPException(status_code=404, detail="Agente no encontrado")
    
    db.delete(db_agente)
    db.commit()
    return {"message": "Agente eliminado"}
