from pydantic import BaseModel, EmailStr
from typing import Optional

# Esquemas para Token
class Token(BaseModel):
    access_token: str
    token_type: str

from pydantic import BaseModel, EmailStr, Field, field_validator
import re

# Esquemas para Usuario
class UsuarioBase(BaseModel):
    ci: str
    id_empresa: Optional[int] = None
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
    permisos: list[str] = [] # Se llenará dinámicamente con los códigos de permiso
    
    class Config:
        from_attributes = True

# Esquemas para Rol
class RolBase(BaseModel):
    nombre: str
    id_empresa: Optional[int] = None

class RolCreate(RolBase):
    pass

class RolResponse(RolBase):
    id_rol: int
    permisos: list[int] = []

    class Config:
        from_attributes = True

# Esquemas para Permiso
class PermisoBase(BaseModel):
    codigo: str
    descripcion: Optional[str] = None
    tipo: str

class PermisoCreate(PermisoBase):
    pass

class PermisoResponse(PermisoBase):
    id_permiso: int

    class Config:
        from_attributes = True

# Esquemas para Empresa
class EmpresaBase(BaseModel):
    nombre: str
    dominio: Optional[str] = None
    estado: Optional[str] = "Activa"

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaResponse(EmpresaBase):
    id_empresa: int
    fecha_registro: str

    class Config:
        from_attributes = True

# Esquemas para Catálogo de Propiedades

class ImagenResponse(BaseModel):
    id_imagen: int
    url: str

    class Config:
        from_attributes = True

class CaracteristicaResponse(BaseModel):
    nombre: str
    valor: str

    class Config:
        from_attributes = True

class PropiedadCatalogoResponse(BaseModel):
    id_propiedad: int
    id_empresa: int
    titulo: str
    direccion: str
    precio: float
    tipo_operacion: str
    estado: str
    imagenes: list[ImagenResponse] = []
    caracteristicas: list[CaracteristicaResponse] = []
    
    class Config:
        from_attributes = True
