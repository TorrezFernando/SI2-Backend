from database.database import engine, Base
import database.models
from sqlalchemy.orm import Session
from modulo_administracion_configuracion.models import Tenant
from gestion_usuarios.models import Rol, Usuario
from auth import get_password_hash

print("Recreando tablas...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

print("Sembrando datos iniciales...")
with Session(engine) as db:
    # Roles
    r1 = Rol(nombre="Administrador")
    r2 = Rol(nombre="Agente")
    r3 = Rol(nombre="Cliente")
    db.add_all([r1, r2, r3])
    
    # Tenant
    tenant = Tenant(nombre="Inmobiliaria Premium", plan="pro", max_propiedades=50)
    db.add(tenant)
    db.commit()
    
    # Usuario Admin del Tenant
    admin = Usuario(
        ci="123456",
        nombre="Admin Premium",
        correo="admin@premium.com",
        id_rol=r1.id_rol,
        id_tenant=tenant.id_tenant,
        password_hash=get_password_hash("Admin123!")
    )
    db.add(admin)
    db.commit()

print("Base de datos multi-tenant creada exitosamente.")
