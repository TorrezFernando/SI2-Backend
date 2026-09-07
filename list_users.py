from database.database import SessionLocal
from database.models import *
from gestion_usuarios.models import Usuario, Rol

db = SessionLocal()
try:
    usuarios = db.query(Usuario).all()
    roles = db.query(Rol).all()
    
    print("=== ROLES ===")
    for r in roles:
        print(f"  ID: {r.id_rol} | Nombre: {r.nombre}")
    
    print("\n=== USUARIOS ===")
    for u in usuarios:
        rol = db.query(Rol).filter(Rol.id_rol == u.id_rol).first()
        rol_nombre = rol.nombre if rol else "Sin rol"
        print(f"  Nombre: {u.nombre} | CI: {u.ci} | Correo: {u.correo} | Rol: {rol_nombre} | Tenant: {u.id_tenant}")
finally:
    db.close()
