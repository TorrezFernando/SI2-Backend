from database.database import SessionLocal
from database import models
from auth import get_password_hash

db = SessionLocal()

try:
    # 1. Crear Empresas SaaS
    empresa1 = db.query(models.Empresa).filter(models.Empresa.id_empresa == 1).first()
    if not empresa1:
        empresa1 = models.Empresa(id_empresa=1, nombre="Raíces Inmobiliaria", dominio="raices.com")
        db.add(empresa1)
        
    empresa2 = db.query(models.Empresa).filter(models.Empresa.id_empresa == 2).first()
    if not empresa2:
        empresa2 = models.Empresa(id_empresa=2, nombre="Horizonte Bienes Raíces", dominio="horizonte.com")
        db.add(empresa2)
    db.commit()

    # 2. Crear Roles
    roles_nombres = {1: 'Administrador', 2: 'Agente Inmobiliario', 3: 'Propietario', 4: 'Cliente'}
    for id_rol, nombre in roles_nombres.items():
        rol = db.query(models.Rol).filter(models.Rol.id_rol == id_rol).first()
        if not rol:
            rol = models.Rol(id_rol=id_rol, nombre=nombre)
            db.add(rol)
    db.commit()

    # 3. Crear Usuarios de la Empresa 1
    user = db.query(models.Usuario).filter(models.Usuario.correo == "admin@raices.com").first()
    if not user:
        user = models.Usuario(
            ci="1234567",
            id_empresa=1,
            nombre="Admin Raices",
            correo="admin@raices.com",
            telefono="77712345",
            id_rol=1,
            password_hash=get_password_hash("123")
        )
        db.add(user)
        db.commit()
        print("¡Datos semilla y usuario admin creados con exito!")
    else:
        print("Los datos semilla ya existen.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
