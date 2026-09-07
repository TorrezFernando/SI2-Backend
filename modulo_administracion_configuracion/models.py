from sqlalchemy import Column, Integer, String, Boolean, Date
from database.database import Base
from sqlalchemy.orm import relationship

class Tenant(Base):
    __tablename__ = "tenant"
    id_tenant = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    plan = Column(String(50), nullable=False, default="basico")
    max_propiedades = Column(Integer, nullable=False, default=10)
    estado = Column(Boolean, default=True)
    fecha_vencimiento_pago = Column(Date, nullable=True)
    
    usuarios = relationship("Usuario", back_populates="tenant")
