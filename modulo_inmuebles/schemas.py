from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

# --- Cliente ---
class ClienteBase(BaseModel):
    ci_usuario: str

class ClienteCreate(ClienteBase):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    password: Optional[str] = None

class ClienteResponse(ClienteBase):
    id_cliente: int
    class Config:
        from_attributes = True

# --- Propietario ---
class PropietarioBase(BaseModel):
    ci_usuario: str

class PropietarioCreate(PropietarioBase):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    password: Optional[str] = None

class PropietarioResponse(PropietarioBase):
    id_propietario: int
    class Config:
        from_attributes = True

# --- Agente ---
class AgenteBase(BaseModel):
    ci_usuario: str

class AgenteCreate(AgenteBase):
    nombre: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None
    password: Optional[str] = None

class AgenteResponse(AgenteBase):
    id_agente: int
    class Config:
        from_attributes = True

# --- Imagen ---
class ImagenResponse(BaseModel):
    id_imagen: int
    url: str
    class Config:
        from_attributes = True

# --- Propiedad ---
class PropiedadBase(BaseModel):
    titulo: str
    direccion: str
    precio: Decimal
    tipo_operacion: str
    estado: str = "Disponible"
    id_propietario: int
    id_agente: int

class PropiedadCreate(PropiedadBase):
    pass

class PropiedadResponse(PropiedadBase):
    id_propiedad: int
    id_tenant: int
    imagenes: List[ImagenResponse] = []
    
    class Config:
        from_attributes = True
