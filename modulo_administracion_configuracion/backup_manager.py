import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.engine import make_url
from database.database import SQLALCHEMY_DATABASE_URL
from auth import require_admin, is_superadmin

router = APIRouter(prefix="/api/backup",tags=["Backups"])
BACKUP_DIR = Path("backups")

def realizar_backup():
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    url = make_url(SQLALCHEMY_DATABASE_URL)
    if url.get_backend_name() == "sqlite":
        source = Path(url.database or "")
        if not source.is_file():
            raise HTTPException(503,"No hay archivo SQLite para respaldar.")
        target = BACKUP_DIR / f"backup_{timestamp}.db"
        src = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            dst = sqlite3.connect(target)
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()
        return str(target)
    if url.get_backend_name() == "postgresql":
        target = BACKUP_DIR / f"backup_{timestamp}.sql"
        env = dict(os.environ)
        if url.password:
            env["PGPASSWORD"] = url.password
        try:
            subprocess.run(["pg_dump","--host",url.host or "localhost","--port",str(url.port or 5432),
                "--username",url.username or "postgres","--dbname",url.database,"--file",str(target)],
                env=env,check=True,capture_output=True,timeout=300)
        except (OSError,subprocess.SubprocessError):
            target.unlink(missing_ok=True)
            raise HTTPException(503,"No se pudo generar el respaldo PostgreSQL. Verifique pg_dump y la conexión.")
        return str(target)
    raise HTTPException(503,"Motor no soportado.")

@router.post("/manual")
def crear_backup_manual(user=Depends(require_admin)):
    if not is_superadmin(user):
        raise HTTPException(403,"El respaldo global requiere superadministrador.")
    path = realizar_backup()
    return {"success":True,"message":"Backup completado","archivo":Path(path).name}

def iniciar_scheduler():
    # Activar únicamente en un proceso dedicado; apagado por defecto.
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(timezone="America/La_Paz")
    scheduler.add_job(realizar_backup,"cron",hour=3,minute=0,id="backup",max_instances=1,coalesce=True)
    scheduler.start()
    return scheduler
