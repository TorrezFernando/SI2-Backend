from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database.database import Base

class Rol(Base):
    __tablename__ = "rol"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    
    usuarios = relationship("Usuario", back_populates="rol")

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, index=True)
    ci = Column(String(20), nullable=False)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(100), nullable=False, index=True)
    telefono = Column(String(20))
    id_rol = Column(Integer, ForeignKey("rol.id_rol"))
    password_hash = Column(String(255), nullable=False)
    
    # FK for Multi-Tenant
    id_tenant = Column(Integer, ForeignKey("tenant.id_tenant"), nullable=False)
    
    tenant = relationship("Tenant", back_populates="usuarios")
    rol = relationship("Rol", back_populates="usuarios")
    bitacoras = relationship("Bitacora", back_populates="usuario")
    propietario = relationship("Propietario", back_populates="usuario", uselist=False)
    agente = relationship("Agente", back_populates="usuario", uselist=False)
    cliente = relationship("Cliente", back_populates="usuario", uselist=False)

    __table_args__ = (
        UniqueConstraint("id_tenant", "correo", name="uq_usuario_tenant_correo"),
        UniqueConstraint("id_tenant", "ci", name="uq_usuario_tenant_ci"),
    )