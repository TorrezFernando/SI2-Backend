from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

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
    password: str = Field(..., min_length=4)

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

class EmpresaConAdminCreate(EmpresaBase):
    admin_ci: str
    admin_nombre: str
    admin_correo: EmailStr
    admin_telefono: Optional[str] = None

class EmpresaResponse(EmpresaBase):
    id_empresa: int
    fecha_registro: Optional[datetime] = None

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

# ============================================================
# SCHEMAS MÓDULO INMUEBLES (ADMIN)
# ============================================================

class PropiedadCreate(BaseModel):
    id_propietario: int
    id_agente: int
    titulo: str
    direccion: str
    precio: float
    tipo_operacion: str  # 'Venta', 'Alquiler', 'Anticretico'

class PropiedadEstadoUpdate(BaseModel):
    estado: str  # 'Disponible', 'Reservada', 'Vendida', 'Alquilada'

class PropiedadAdminResponse(BaseModel):
    id_propiedad: int
    id_empresa: int
    id_propietario: int
    id_agente: int
    titulo: str
    direccion: str
    precio: float
    tipo_operacion: str
    estado: str
    imagenes: list[ImagenResponse] = []
    caracteristicas: list[CaracteristicaResponse] = []

    class Config:
        from_attributes = True

class PropietarioCreate(BaseModel):
    ci_usuario: str

class PropietarioResponse(BaseModel):
    id_propietario: int
    ci_usuario: str
    id_empresa: int
    nombre: Optional[str] = None
    correo: Optional[str] = None
    telefono: Optional[str] = None

    class Config:
        from_attributes = True

class AgenteResponse(BaseModel):
    id_agente: int
    ci_usuario: str
    id_empresa: int
    nombre: Optional[str] = None
    correo: Optional[str] = None

    class Config:
        from_attributes = True

# ============================================================
# SCHEMAS MÓDULO REPORTES DINÁMICOS
# ============================================================
from typing import Any

class ReporteFiltro(BaseModel):
    columna: str
    operador: str # 'eq', 'gt', 'lt', 'gte', 'lte', 'like'
    valor: Any

class ReporteOrden(BaseModel):
    columna: str
    direccion: str # 'asc' o 'desc'

class ReporteRequest(BaseModel):
    entidad: str # 'usuarios', 'propiedades'
    columnas: list[str]
    filtros: list[ReporteFiltro] = []
    orden: Optional[ReporteOrden] = None

class ReporteGuardadoCreate(BaseModel):
    nombre: str
    configuracion: str # JSON string of ReporteRequest

class ReporteGuardadoResponse(BaseModel):
    id_reporte: int
    nombre: str
    configuracion: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True
