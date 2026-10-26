import hashlib
import os
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Usuario

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError("Configure JWT_SECRET_KEY con al menos 32 caracteres aleatorios.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="gestion_usuarios/auth/login")

def role_name(user):
    name = user.rol.nombre if user.rol else ""
    return "".join(c for c in unicodedata.normalize("NFD", name.lower()) if unicodedata.category(c) != "Mn")

def is_superadmin(user):
    allowed = {s.strip() for s in os.getenv("SUPERADMIN_USER_IDS", "").split(",") if s.strip()}
    return str(user.id) in allowed

def is_admin(user):
    return is_superadmin(user) or role_name(user) in {"administrador", "administrador de empresa"}

def validate_password(password):
    if (len(password) < 8 or len(password.encode()) > 72 or not re.search(r"[A-Z]", password)
        or not re.search(r"[a-z]", password) or not re.search(r"\d", password)
        or not re.search(r"[^\w\s]", password)):
        raise HTTPException(422, "Contraseña: mínimo 8 caracteres, mayúscula, minúscula, número y símbolo; máximo 72 bytes.")
    return password

def verify_password(plain_password: str, hashed_password: str | bytes) -> bool:
    try:
        hp = hashed_password.encode() if isinstance(hashed_password, str) else bytes(hashed_password)
        return bcrypt.checkpw(plain_password.encode(), hp)
    except (ValueError, TypeError, AttributeError):
        return False

def get_password_hash(password: str) -> str:
    validate_password(password)
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def password_version(user):
    return hashlib.sha256(user.password_hash.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    payload = dict(data)
    payload["exp"] = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def user_token(user):
    return create_access_token({"sub": str(user.id), "tenant_id": user.id_tenant, "pv": password_version(user)})

def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    invalid = HTTPException(401, "No se pudieron validar las credenciales", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid = int(payload["sub"])
    except (JWTError, KeyError, ValueError, TypeError):
        raise invalid
    user = db.get(Usuario, uid)
    if not user or payload.get("tenant_id") != user.id_tenant or payload.get("pv") != password_version(user):
        raise invalid
    if not user.tenant or not user.tenant.estado:
        raise HTTPException(403, "La inmobiliaria se encuentra inactiva.")
    from planes import assert_operational
    allowed = (request.url.path.startswith("/suscripciones") or
               request.url.path in {"/auth/me", "/users/me", "/auth/logout"} or
               (request.url.path == "/admin/empresas" and request.method == "GET"))
    if not allowed and not is_superadmin(user):
        assert_operational(db,user.tenant)
    return user

get_current_tenant_user = get_current_user

def require_admin(user: Usuario = Depends(get_current_user)):
    if not is_admin(user):
        raise HTTPException(403, "Se requiere permiso de administración.")
    return user

def require_staff(user: Usuario = Depends(get_current_user)):
    if not is_admin(user) and role_name(user) not in {"agente", "agente inmobiliario"}:
        raise HTTPException(403, "Se requiere permiso de gestión inmobiliaria.")
    return user

def tenant_scope(user, requested=None):
    if requested is not None and requested != user.id_tenant and not is_superadmin(user):
        raise HTTPException(403, "No puede acceder a otra inmobiliaria.")
    return requested if requested is not None else user.id_tenant

def profile(user):
    menus = ["CATALOGO"]
    if is_admin(user):
        menus += ["EMPRESAS", "USUARIOS", "ROLES", "CLIENTES", "PROPIETARIOS", "AGENTES", "PROPIEDADES"]
    elif role_name(user) in {"agente", "agente inmobiliario"}:
        menus += ["CLIENTES", "PROPIETARIOS", "AGENTES", "PROPIEDADES"]
    if is_superadmin(user):
        menus += ["BITACORA", "BACKUP"]
    permissions = ["UI:MENU_" + name for name in menus]
    return {"id": user.id, "email": user.correo, "full_name": user.nombre,
            "id_rol": user.id_rol, "id_tenant": user.id_tenant, "is_active": True,
            "is_superadmin": is_superadmin(user), "permisos": permissions,
            "roles": [{"id": user.id_rol, "name": user.rol.nombre if user.rol else "", "permissions": permissions}]}
