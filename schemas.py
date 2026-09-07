from pydantic import BaseModel, EmailStr
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime

# Esquemas para Token
class Token(BaseModel):
    access_token: str
    token_type: str

from pydantic import BaseModel, EmailStr, Field, field_validator
import re

# Esquemas para Usuario
class UsuarioBase(BaseModel):
    ci: str
    nombre: str
    correo: EmailStr
    telefono: Optional[str] = None
    id_rol: int

class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=8)

    @field_validator('password')
    def validate_password(cls, v):
        if not re.match(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$", v):
            raise ValueError('La contraseña no cumple con los requisitos de seguridad')
        return v

class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str

class UsuarioResponse(UsuarioBase):
    class Config:
        from_attributes = True

# Esquemas para Rol
class RolBase(BaseModel):
    nombre: str

class RolCreate(RolBase):
    pass

class RolResponse(RolBase):
    id_rol: int

    class Config:
        from_attributes = True

# --- Nuevos Esquemas (Sprint 1) ---

# Esquemas para Cliente
class ClienteBase(BaseModel):
    ci_usuario: str

class ClienteCreate(ClienteBase):
    pass

class ClienteResponse(ClienteBase):
    id_cliente: int
    class Config:
        from_attributes = True

# Esquemas para Propietario
class PropietarioBase(BaseModel):
    ci_usuario: str

class PropietarioCreate(PropietarioBase):
    pass

class PropietarioResponse(PropietarioBase):
    id_propietario: int
    class Config:
        from_attributes = True

# Esquemas para Agente
class AgenteBase(BaseModel):
    ci_usuario: str

class AgenteCreate(AgenteBase):
    pass

class AgenteResponse(AgenteBase):
    id_agente: int
    class Config:
        from_attributes = True

# Esquemas para Imagen
class ImagenBase(BaseModel):
    url: str

class ImagenResponse(ImagenBase):
    id_imagen: int
    id_propiedad: int
    class Config:
        from_attributes = True

# Esquemas para Caracteristica
class CaracteristicaBase(BaseModel):
    nombre: str
    valor: str

class CaracteristicaResponse(CaracteristicaBase):
    id_caracteristica: int
    id_propiedad: int
    class Config:
        from_attributes = True

class CaracteristicaCreate(CaracteristicaBase):
    pass

# Esquemas para Propiedad
class PropiedadBase(BaseModel):
    id_propietario: int
    id_agente: int
    titulo: str
    direccion: str
    precio: Decimal
    tipo_operacion: str
    estado: Optional[str] = 'Disponible'

class PropiedadCreate(PropiedadBase):
    caracteristicas: Optional[List[CaracteristicaCreate]] = []

class PropiedadUpdate(BaseModel):
    estado: str

class PropiedadResponse(PropiedadBase):
    id_propiedad: int
    imagenes: List[ImagenResponse] = []
    caracteristicas: List[CaracteristicaResponse] = []
    
    class Config:
        from_attributes = True

