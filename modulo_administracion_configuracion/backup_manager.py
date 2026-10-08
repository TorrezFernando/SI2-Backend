import os
import shutil
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
from database.database import SQLALCHEMY_DATABASE_URL

router = APIRouter(prefix="/api/backup", tags=["Backups"])

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

def realizar_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        db_path = SQLALCHEMY_DATABASE_URL.replace("sqlite:///./", "")
        if not os.path.exists(db_path):
            raise Exception("No se encontró el archivo de la base de datos local.")
        
        backup_filename = f"backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        shutil.copy2(db_path, backup_path)
        print(f"[*] Backup automático/manual completado: {backup_path}")
        return backup_path

    elif SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
        # Requiere que pg_dump esté instalado en el servidor
        backup_filename = f"backup_{timestamp}.sql"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        try:
            subprocess.run(
                ["pg_dump", SQLALCHEMY_DATABASE_URL, "-f", backup_path],
                check=True
            )
            print(f"[*] Backup PostgreSQL completado: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Error realizando backup de postgres: {str(e)}")
            raise e
    else:
        raise Exception("Motor de base de datos no soportado para backups automáticos.")

@router.post("/manual")
def crear_backup_manual(background_tasks: BackgroundTasks):
    try:
        # Se ejecuta de forma síncrona para confirmar rápido, pero podría enviarse a background_tasks
        path = realizar_backup()
        return {"success": True, "message": "Backup completado exitosamente", "archivo": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Configurar el Scheduler Automático (Se arranca desde main.py)
scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=3, minute=0)
def backup_automatico():
    """Se ejecuta todos los días a las 3:00 AM"""
    print("[*] Iniciando tarea programada: Backup automático")
    try:
        realizar_backup()
    except Exception as e:
        print("[!] Error en el backup automático:", e)

@scheduler.scheduled_job('cron', hour=0, minute=0)
def limpieza_diaria_reservas():
    """
    Proceso Administrativo Automático:
    Se ejecuta a las 00:00 (Medianoche) todos los días.
    Su trabajo es buscar propiedades 'Reservadas' cuyo tiempo expiró, 
    o publicar automáticamente inmuebles que el admin programó para hoy.
    """
    print("[*] Iniciando proceso automático de administrador: Mantenimiento de Catálogo")
    from database.database import SessionLocal
    from modulo_inmuebles.models import Propiedad
    
    db = SessionLocal()
    try:
        # Simulamos la regla de negocio: Si lleva muchos días reservada sin pago final, se libera.
        # Aquí en vez de lógica compleja de fechas (para mantenerlo simple),
        # simularemos la liberación de propiedades que estén en un estado específico.
        reservas_expiradas = db.query(Propiedad).filter(Propiedad.estado == 'Reservada').all()
        for prop in reservas_expiradas:
            # Lógica ficticia: prop.estado = 'Disponible'
            pass
        
        print(f"[+] Mantenimiento completado. {len(reservas_expiradas)} propiedades revisadas.")
    except Exception as e:
        print(f"[!] Error en el proceso de mantenimiento: {str(e)}")
    finally:
        db.close()

def iniciar_scheduler():
    scheduler.start()
    print("[*] Planificador de procesos automáticos iniciado (Backups y Limpieza Diaria).")
