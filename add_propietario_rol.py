from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import Rol

db: Session = SessionLocal()
try:
    propietario_rol = db.query(Rol).filter(Rol.nombre == "Propietario").first()
    if not propietario_rol:
        nuevo_rol = Rol(nombre="Propietario")
        db.add(nuevo_rol)
        db.commit()
        print("Rol 'Propietario' añadido con éxito.")
    else:
        print("El rol 'Propietario' ya existe.")
finally:
    db.close()
