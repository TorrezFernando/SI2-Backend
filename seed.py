from database.database import SessionLocal
from database import models
from auth import get_password_hash

db = SessionLocal()

try:
    rol = db.query(models.Rol).filter(models.Rol.id_rol == 1).first()
    if not rol:
        rol = models.Rol(id_rol=1, nombre="Administrador")
        db.add(rol)
        db.commit()

    user = db.query(models.Usuario).filter(models.Usuario.correo == "admin@raices.com").first()
    if not user:
        user = models.Usuario(
            ci="1234567",
            nombre="Admin Raices",
            correo="admin@raices.com",
            telefono="77712345",
            id_rol=1,
            password_hash=get_password_hash("123")
        )
        db.add(user)
        db.commit()
        print("¡Usuario admin creado con exito!")
    else:
        print("El usuario ya existe.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
