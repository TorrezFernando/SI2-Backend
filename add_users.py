from database.database import engine, Base
import database.models
from sqlalchemy.orm import Session
from modulo_administracion_configuracion.models import Tenant
from gestion_usuarios.models import Rol, Usuario
from auth import get_password_hash

print("Añadiendo Agente y Cliente de prueba...")
with Session(engine) as db:
    # Buscar roles y tenant
    r2 = db.query(Rol).filter(Rol.nombre == "Agente").first()
    r3 = db.query(Rol).filter(Rol.nombre == "Cliente").first()
    tenant = db.query(Tenant).filter(Tenant.nombre == "Inmobiliaria Premium").first()
    
    if not db.query(Usuario).filter(Usuario.correo == "agente@premium.com").first():
        agente = Usuario(
            ci="888888",
            nombre="Agente Estrella",
            correo="agente@premium.com",
            id_rol=r2.id_rol,
            id_tenant=tenant.id_tenant,
            password_hash=get_password_hash("Agente123!")
        )
        db.add(agente)
        
    if not db.query(Usuario).filter(Usuario.correo == "cliente@premium.com").first():
        cliente = Usuario(
            ci="999999",
            nombre="Cliente VIP",
            correo="cliente@premium.com",
            id_rol=r3.id_rol,
            id_tenant=tenant.id_tenant,
            password_hash=get_password_hash("Cliente123!")
        )
        db.add(cliente)
        
    db.commit()

print("Usuarios añadidos exitosamente.")
