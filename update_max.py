from database.database import SessionLocal
from database.models import *
from gestion_usuarios.models import Usuario

db = SessionLocal()
try:
    user = db.query(Usuario).filter(Usuario.ci == '12345678').first()
    if user:
        user.id_rol = 4
        db.commit()
        print("Role updated")
    else:
        print("User not found")
finally:
    db.close()
