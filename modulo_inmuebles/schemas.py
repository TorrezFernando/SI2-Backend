from pydantic import BaseModel, Field
from typing import Literal
from decimal import Decimal

Operacion = Literal["Venta", "Alquiler", "Anticretico"]
Estado = Literal["Disponible", "Reservada", "Vendida", "Alquilada", "Anticretico"]

class PersonaCreate(BaseModel):
    ci_usuario: str = Field(min_length=1, max_length=20)
    nombre: str | None = None
    correo: str | None = None
    telefono: str | None = None
    password: str | None = None
    id_tenant: int | None = None

ClienteCreate = PersonaCreate
PropietarioCreate = PersonaCreate
AgenteCreate = PersonaCreate

class ImagenResponse(BaseModel):
    id_imagen: int
    url: str
    class Config:
        from_attributes = True

class PropiedadBase(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    direccion: str = Field(min_length=1, max_length=255)
    precio: Decimal = Field(gt=0, le=9999999999.99)
    tipo_operacion: Operacion
    estado: Estado = "Disponible"
    id_propietario: int = Field(gt=0)
    id_agente: int = Field(gt=0)
    id_tipo_inmueble: int = Field(gt=0)
    id_zona: int = Field(gt=0)
    habitaciones: int | None = Field(default=None, ge=0)
    banos: int | None = Field(default=None, ge=0)
    superficie_m2: Decimal | None = Field(default=None, gt=0, le=99999999.99)
    garaje: bool = False
    antiguedad_anios: int | None = Field(default=None, ge=0)
    descripcion: str = Field(default="", max_length=10000)

class PropiedadCreate(PropiedadBase):
    id_tenant: int | None = None

class PropiedadResponse(PropiedadBase):
    id_propiedad: int
    id_tenant: int
    imagenes: list[ImagenResponse] = Field(default_factory=list)
    class Config:
        from_attributes = True
