from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class Rol(Base):
    __tablename__ = "rol"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    
    usuarios = relationship("Usuario", back_populates="rol")

class Usuario(Base):
    __tablename__ = "usuario"
    ci = Column(String(20), primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), unique=True, index=True, nullable=False)
    telefono = Column(String(20))
    id_rol = Column(Integer, ForeignKey("rol.id_rol"))
    password_hash = Column(String(255), nullable=False)
    
    # FK for Multi-Tenant
    id_tenant = Column(Integer, ForeignKey("tenant.id_tenant"), nullable=True)
    
    tenant = relationship("Tenant", back_populates="usuarios")
    rol = relationship("Rol", back_populates="usuarios")
    bitacoras = relationship("Bitacora", back_populates="usuario")
    propietario = relationship("Propietario", back_populates="usuario", uselist=False)
    agente = relationship("Agente", back_populates="usuario", uselist=False)
    cliente = relationship("Cliente", back_populates="usuario", uselist=False)
