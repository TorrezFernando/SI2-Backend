from sqlalchemy import Column, Integer, String, Boolean, Date, TIMESTAMP
from database.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

class Tenant(Base):
    __tablename__ = "tenant"
    id_tenant = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    plan = Column(String(50), nullable=False, default="basico")
    max_propiedades = Column(Integer, nullable=False, default=10)
    estado = Column(Boolean, default=True)
    fecha_vencimiento_pago = Column(Date, nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.current_timestamp())
    
    usuarios = relationship("Usuario", back_populates="tenant")
    propiedades = relationship("Propiedad", back_populates="tenant")
    contratos = relationship("Contrato", back_populates="tenant")
    visitas = relationship("Visita", back_populates="tenant")
    bitacoras = relationship("Bitacora", back_populates="tenant")