from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database import models
import schemas
from auth import get_current_user

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/", response_model=list[schemas.ClienteResponse])
def read_clientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Cliente).offset(skip).limit(limit).all()

@router.post("/", response_model=schemas.ClienteResponse, status_code=status.HTTP_201_CREATED)
def create_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    user = db.query(models.Usuario).filter(models.Usuario.ci == cliente.ci_usuario).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    db_cliente = db.query(models.Cliente).filter(models.Cliente.ci_usuario == cliente.ci_usuario).first()
    if db_cliente:
        raise HTTPException(status_code=400, detail="El cliente ya existe")
    
    new_cliente = models.Cliente(ci_usuario=cliente.ci_usuario)
    db.add(new_cliente)
    db.commit()
    db.refresh(new_cliente)
    return new_cliente

@router.delete("/{id_cliente}")
def delete_cliente(id_cliente: int, db: Session = Depends(get_db)):
    db_cliente = db.query(models.Cliente).filter(models.Cliente.id_cliente == id_cliente).first()
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db.delete(db_cliente)
    db.commit()
    return {"message": "Cliente eliminado"}
