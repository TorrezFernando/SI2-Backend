from pydantic import BaseModel
from typing import Optional

class RolCreate(BaseModel):
    nombre: str

class RolResponse(BaseModel):
    id_rol: int
    nombre: str
    class Config:
        from_attributes = True

class UsuarioBase(BaseModel):
    ci: str
    nombre: str
    correo: str
    telefono: Optional[str] = None
    id_rol: int

class UsuarioCreate(UsuarioBase):
    password: str
    id_tenant: Optional[int] = None

class UsuarioResponse(UsuarioBase):
    id_tenant: Optional[int] = None
    
    class Config:
        from_attributes = True
