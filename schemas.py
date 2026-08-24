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
