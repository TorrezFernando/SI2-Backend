import json
from decimal import Decimal, InvalidOperation
from typing import Literal, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import Session
from database.database import Base, get_db
from database.models import Usuario, Propiedad
from auth import require_staff, is_admin, is_superadmin

router = APIRouter(prefix="/reportes", tags=["Reportes"])

class ReporteGuardado(Base):
    __tablename__ = "reporte_guardado"
    id = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    id_tenant = Column(Integer, ForeignKey("tenant.id_tenant"), nullable=False)
    nombre = Column(String(150), nullable=False)
    configuracion = Column(Text, nullable=False)

COLUMNS = {
    "propiedades": ["id_tenant","id_propiedad","titulo","direccion","precio","tipo_operacion","estado"],
    "usuarios": ["id_tenant","ci","nombre","correo","telefono"],
}

class Filtro(BaseModel):
    columna: str
    operador: Literal["eq","like","gt","lt","gte","lte"]
    valor: str | int | float

class Orden(BaseModel):
    columna: str
    direccion: Literal["asc","desc"] = "asc"

class ReporteConfig(BaseModel):
    entidad: Literal["propiedades","usuarios"] = "propiedades"
    columnas: list[str] | None = None
    filtros: list[Filtro] = Field(default_factory=list, max_length=30)
    orden: Orden | None = None
    limite: int = Field(default=1000, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

def validate_config(config):
    allowed = COLUMNS[config.entidad]
    requested = (config.columnas or allowed) + [f.columna for f in config.filtros]
    if config.orden:
        requested.append(config.orden.columna)
    if not set(requested).issubset(allowed):
        raise HTTPException(422,"Columna no permitida.")
    return config

@router.post("/generar")
def generar_reporte(config: ReporteConfig, db: Session = Depends(get_db), user=Depends(require_staff)):
    validate_config(config)
    if config.entidad == "usuarios" and not is_admin(user):
        raise HTTPException(403,"El reporte de usuarios requiere administración.")
    model = Usuario if config.entidad == "usuarios" else Propiedad
    query = db.query(model)
    if not is_superadmin(user):
        query = query.filter(model.id_tenant == user.id_tenant)
    for f in config.filtros:
        column = getattr(model,f.columna)
        value = f.valor
        try:
            python_type = column.type.python_type
            if python_type is Decimal:
                value = Decimal(str(value))
                if not value.is_finite():
                    raise ValueError()
            elif python_type is int:
                value = int(str(value))
            else:
                value = str(value)
        except (ValueError, InvalidOperation, TypeError):
            raise HTTPException(422,"Valor de filtro incompatible con la columna.")
        if f.operador == "like":
            if python_type is not str:
                raise HTTPException(422,"like requiere una columna de texto.")
            query = query.filter(column.contains(value, autoescape=True))
        else:
            operators = {"eq":column.__eq__,"gt":column.__gt__,"lt":column.__lt__,"gte":column.__ge__,"lte":column.__le__}
            query = query.filter(operators[f.operador](value))
    primary = model.id if model is Usuario else model.id_propiedad
    if config.orden:
        column = getattr(model,config.orden.columna)
        query = query.order_by(column.desc() if config.orden.direccion == "desc" else column.asc(), primary)
    else:
        query = query.order_by(primary)
    total = query.count()
    columns = config.columnas or COLUMNS[config.entidad]
    data = [{key:getattr(row,key) for key in columns} for row in query.offset(config.offset).limit(config.limite).all()]
    return {"success":True,"data":data,"total":total,"limite":config.limite,"offset":config.offset}

class GuardarReporte(BaseModel):
    nombre: str = Field(min_length=1,max_length=150)
    configuracion: str = Field(max_length=20000)

@router.get("/guardados")
def guardados(db: Session = Depends(get_db), user=Depends(require_staff)):
    return db.query(ReporteGuardado).filter(ReporteGuardado.id_usuario == user.id,ReporteGuardado.id_tenant == user.id_tenant).all()

@router.post("/guardados", status_code=201)
def guardar(data: GuardarReporte, db: Session = Depends(get_db), user=Depends(require_staff)):
    try:
        cfg = json.loads(data.configuracion)
        config = ReporteConfig.model_validate(cfg)
    except (ValueError, TypeError):
        raise HTTPException(422,"Configuración inválida.")
    validate_config(config)
    if config.entidad == "usuarios" and not is_admin(user):
        raise HTTPException(403,"Sin permiso para reportes de usuarios.")
    row = ReporteGuardado(nombre=data.nombre,configuracion=data.configuracion,id_usuario=user.id,id_tenant=user.id_tenant)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
