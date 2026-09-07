from pydantic import BaseModel
from typing import Optional
from datetime import date

class TenantBase(BaseModel):
    nombre: str
    plan: str = "basico"
    max_propiedades: int = 10
    estado: bool = True
    fecha_vencimiento_pago: Optional[date] = None

class TenantCreate(TenantBase):
    pass

class TenantResponse(TenantBase):
    id_tenant: int

    class Config:
        from_attributes = True
