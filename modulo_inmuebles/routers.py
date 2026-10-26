from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from pathlib import Path
import uuid
from database.database import get_db
from database.models import Propiedad, Cliente, Propietario, Agente, Imagen, Usuario, Tenant, Rol, TipoInmueble, Zona
from modulo_inmuebles import schemas
from auth import require_staff, require_admin, get_password_hash, tenant_scope, is_superadmin
from gestion_usuarios.routers import existing_user

UPLOAD_DIR = Path("uploads")
router = APIRouter(prefix="/modulo_inmuebles", tags=["Módulo de Inmuebles"])

def scoped_property(db, user, id_propiedad):
    query = db.query(Propiedad).filter(Propiedad.id_propiedad == id_propiedad)
    if not is_superadmin(user):
        query = query.filter(Propiedad.id_tenant == user.id_tenant)
    prop = query.first()
    if not prop:
        raise HTTPException(404, "Propiedad no encontrada.")
    return prop

@router.get("/tipos")
def tipos(db: Session = Depends(get_db), user=Depends(require_staff)):
    return db.query(TipoInmueble).order_by(TipoInmueble.nombre).all()

@router.get("/zonas")
def zonas(db: Session = Depends(get_db), user=Depends(require_staff)):
    return db.query(Zona).order_by(Zona.nombre).all()

@router.get("/propiedades/catalogo", response_model=list[schemas.PropiedadResponse])
def get_catalogo(estado: schemas.Estado = "Disponible", tipo_operacion: schemas.Operacion | None = None,
                 precio_min: float | None = Query(None, ge=0), precio_max: float | None = Query(None, ge=0),
                 cuartos: int | None = Query(None, ge=0), banos: int | None = Query(None, ge=0),
                 metros_min: float | None = Query(None, ge=0), metros_max: float | None = Query(None, ge=0),
                 zona: str | None = None, id_tenant: int | None = None,
                 salas: int | None = None, amueblado: bool = False, servicios_basicos: bool = False,
                 db: Session = Depends(get_db)):
    from modulo_inmuebles.models import Caracteristica
    query = db.query(Propiedad).join(Tenant).filter(Tenant.estado.is_(True), Propiedad.estado == estado)
    for field, value, operator in [(Propiedad.tipo_operacion,tipo_operacion,"eq"), (Propiedad.precio,precio_min,"ge"),
            (Propiedad.precio,precio_max,"le"), (Propiedad.habitaciones,cuartos,"ge"), (Propiedad.banos,banos,"ge"),
            (Propiedad.superficie_m2,metros_min,"ge"), (Propiedad.superficie_m2,metros_max,"le"),
            (Propiedad.id_tenant,id_tenant,"eq")]:
        if value is not None:
            query = query.filter({"eq":field.__eq__, "ge":field.__ge__, "le":field.__le__}[operator](value))
    if precio_min is not None and precio_max is not None and precio_min > precio_max:
        raise HTTPException(422, "Rango de precios inválido.")
    if zona:
        query = query.join(Zona).filter(Zona.nombre.ilike("%" + zona + "%"))
    for name, value in [("salas",salas),("amueblado",True if amueblado else None),("servicios_basicos",True if servicios_basicos else None)]:
        if value is not None:
            query = query.filter(Propiedad.caracteristicas.any((Caracteristica.nombre == name) & (Caracteristica.valor == str(value).lower())))
    from planes import state
    return [p for p in query.order_by(Propiedad.id_propiedad).all() if state(db,p.tenant) not in {"suspendida","cancelada","inactiva"}]

@router.get("/propiedades", response_model=list[schemas.PropiedadResponse])
def get_propiedades(id_tenant: int | None = None, db: Session = Depends(get_db), user=Depends(require_staff)):
    return db.query(Propiedad).filter(Propiedad.id_tenant == tenant_scope(user,id_tenant)).all()

def validate_relations(db, data, tenant_id):
    for model, field in [(Propietario,"id_propietario"),(Agente,"id_agente")]:
        relation = db.query(model).join(Usuario).filter(getattr(model,field) == getattr(data,field),Usuario.id_tenant == tenant_id).first()
        if not relation:
            raise HTTPException(422, "Propietario y agente deben pertenecer a la inmobiliaria.")
    if not db.get(TipoInmueble,data.id_tipo_inmueble) or not db.get(Zona,data.id_zona):
        raise HTTPException(422, "Tipo de inmueble o zona inexistente.")

@router.post("/propiedades", response_model=schemas.PropiedadResponse, status_code=201)
def create_propiedad(prop: schemas.PropiedadCreate, db: Session = Depends(get_db), user=Depends(require_staff)):
    tenant_id = tenant_scope(user,prop.id_tenant)
    tenant = db.query(Tenant).filter(Tenant.id_tenant == tenant_id).with_for_update().first()
    if not tenant or not tenant.estado:
        raise HTTPException(422,"Empresa inactiva o inexistente.")
    validate_relations(db,prop,tenant_id)
    from planes import check_property_limit
    check_property_limit(db,tenant)
    new = Propiedad(**prop.model_dump(exclude={"id_tenant","descripcion"}),id_tenant=tenant_id)
    new.descripcion = prop.descripcion
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

@router.put("/propiedades/{id_propiedad}", response_model=schemas.PropiedadResponse)
def edit_propiedad(id_propiedad: int, data: schemas.PropiedadCreate, db: Session = Depends(get_db), user=Depends(require_staff)):
    prop = scoped_property(db,user,id_propiedad)
    if data.id_tenant is not None and data.id_tenant != prop.id_tenant:
        raise HTTPException(422,"No puede transferir el inmueble a otra empresa.")
    validate_relations(db,data,prop.id_tenant)
    for key,value in data.model_dump(exclude={"id_tenant","estado"}).items():
        setattr(prop,key,value)
    db.commit()
    db.refresh(prop)
    return prop

@router.delete("/propiedades/{id_propiedad}")
def delete_propiedad(id_propiedad: int, db: Session = Depends(get_db), user=Depends(require_staff)):
    prop = scoped_property(db,user,id_propiedad)
    if prop.contratos or prop.visitas:
        raise HTTPException(409,"El inmueble tiene contratos o visitas; no se puede eliminar.")
    for item in list(prop.imagenes) + list(prop.caracteristicas):
        db.delete(item)
    db.delete(prop)
    db.commit()
    return {"ok":True}

def list_people(model, field, db, user, tenant_id):
    rows = db.query(model).join(Usuario).filter(Usuario.id_tenant == tenant_scope(user,tenant_id)).all()
    return [{field:getattr(p,field),"id_usuario":p.id_usuario,"ci_usuario":p.usuario.ci,
             "nombre":p.usuario.nombre,"correo":p.usuario.correo,"telefono":p.usuario.telefono} for p in rows]

def create_person(model, role, data, db, actor):
    tenant_id = tenant_scope(actor,data.id_tenant)
    tenant = db.query(Tenant).filter(Tenant.id_tenant == tenant_id).with_for_update().first()
    if not tenant or not tenant.estado:
        raise HTTPException(422,"Empresa inactiva o inexistente.")
    user = db.query(Usuario).filter(Usuario.ci == data.ci_usuario,Usuario.id_tenant == tenant_id).first()
    if not user:
        if not all([data.nombre,data.correo,data.password]):
            raise HTTPException(422,"Registre el usuario o proporcione nombre, correo y contraseña.")
        if existing_user(db,data.correo,data.ci_usuario,tenant_id):
            raise HTTPException(409,"Correo o CI duplicado.")
        rol = db.query(Rol).filter(func.lower(Rol.nombre).in_([role.lower(), "agente inmobiliario"] if role == "Agente" else [role.lower()])).first()
        if not rol:
            raise HTTPException(422,"Rol no configurado.")
        from planes import check_employee_limit
        check_employee_limit(db,tenant,rol.id_rol)
        user = Usuario(ci=data.ci_usuario,nombre=data.nombre,correo=data.correo.strip().lower(),telefono=data.telefono,
                       id_rol=rol.id_rol,id_tenant=tenant_id,password_hash=get_password_hash(data.password))
        db.add(user)
        db.flush()
    if db.query(model).filter(model.id_usuario == user.id).first():
        raise HTTPException(409,"El usuario ya tiene este perfil.")
    if model is Agente:
        from planes import PLANS, plan_name, employee_count, is_employee
        limit = PLANS[plan_name(tenant)]["empleados"]
        if not is_employee(db,user.id_rol) and limit is not None and employee_count(db,tenant_id) >= limit:
            raise HTTPException(409,"El plan alcanzó su límite de empleados.")
    new = model(id_usuario=user.id)
    db.add(new)
    db.commit()
    db.refresh(new)
    return new

def delete_person(model, field, id, db, actor):
    query = db.query(model).join(Usuario).filter(getattr(model,field) == id)
    if not is_superadmin(actor):
        query = query.filter(Usuario.id_tenant == actor.id_tenant)
    item = query.first()
    if not item:
        raise HTTPException(404,"Registro no encontrado.")
    for relationship in ("propiedades","visitas","contratos"):
        if getattr(item,relationship,[]):
            raise HTTPException(409,"El registro tiene operaciones relacionadas.")
    db.delete(item)
    db.commit()
    return {"ok":True}

@router.get("/clientes")
@router.get("/clientes_list")
def get_clientes(id_tenant: int | None = None, db: Session = Depends(get_db), user=Depends(require_staff)):
    return list_people(Cliente,"id_cliente",db,user,id_tenant)

@router.post("/clientes", status_code=201)
def create_cliente(data: schemas.ClienteCreate, db: Session = Depends(get_db), user=Depends(require_staff)):
    return create_person(Cliente,"Cliente",data,db,user)

@router.delete("/clientes/{id}")
def delete_cliente(id: int, db: Session = Depends(get_db), user=Depends(require_staff)):
    return delete_person(Cliente,"id_cliente",id,db,user)

@router.get("/propietarios")
@router.get("/propietarios_list")
def get_propietarios(id_tenant: int | None = None, db: Session = Depends(get_db), user=Depends(require_staff)):
    return list_people(Propietario,"id_propietario",db,user,id_tenant)

@router.post("/propietarios", status_code=201)
def create_propietario(data: schemas.PropietarioCreate, db: Session = Depends(get_db), user=Depends(require_staff)):
    return create_person(Propietario,"Propietario",data,db,user)

@router.delete("/propietarios/{id}")
def delete_propietario(id: int, db: Session = Depends(get_db), user=Depends(require_staff)):
    return delete_person(Propietario,"id_propietario",id,db,user)

@router.put("/propietarios/{id}")
def edit_propietario(id: int, data: schemas.PropietarioCreate, db: Session = Depends(get_db), actor=Depends(require_staff)):
    query = db.query(Propietario).join(Usuario).filter(Propietario.id_propietario == id)
    if not is_superadmin(actor):
        query = query.filter(Usuario.id_tenant == actor.id_tenant)
    item = query.first()
    if not item:
        raise HTTPException(404,"Propietario no encontrado.")
    target = db.query(Usuario).filter(Usuario.ci == data.ci_usuario,Usuario.id_tenant == item.usuario.id_tenant).first()
    if not target:
        raise HTTPException(422,"Usuario no encontrado en la empresa.")
    if db.query(Propietario).filter(Propietario.id_usuario == target.id,Propietario.id_propietario != id).first():
        raise HTTPException(409,"El usuario ya tiene perfil de propietario.")
    item.id_usuario = target.id
    db.commit()
    return {"ok":True}

@router.get("/agentes")
def get_agentes(id_tenant: int | None = None, db: Session = Depends(get_db), user=Depends(require_staff)):
    return list_people(Agente,"id_agente",db,user,id_tenant)

@router.post("/agentes", status_code=201)
def create_agente(data: schemas.AgenteCreate, db: Session = Depends(get_db), user=Depends(require_admin)):
    return create_person(Agente,"Agente",data,db,user)

@router.delete("/agentes/{id}")
def delete_agente(id: int, db: Session = Depends(get_db), user=Depends(require_admin)):
    return delete_person(Agente,"id_agente",id,db,user)

class EstadoUpdate(BaseModel):
    estado: schemas.Estado

@router.put("/propiedades/{id_propiedad}/estado", response_model=schemas.PropiedadResponse)
def update_estado(id_propiedad: int, data: EstadoUpdate, db: Session = Depends(get_db), user=Depends(require_staff)):
    prop = scoped_property(db,user,id_propiedad)
    final = {"Venta":"Vendida","Alquiler":"Alquilada","Anticretico":"Anticretico"}[prop.tipo_operacion]
    if data.estado not in {"Disponible","Reservada",final}:
        raise HTTPException(422,"Estado incompatible con la operación.")
    prop.estado = data.estado
    db.commit()
    db.refresh(prop)
    return prop

@router.post("/propiedades/{id_propiedad}/imagenes", response_model=schemas.ImagenResponse)
def upload_imagen(id_propiedad: int, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_staff)):
    scoped_property(db,user,id_propiedad)
    content = file.file.read(5*1024*1024+1)
    if len(content) > 5*1024*1024:
        raise HTTPException(413,"La imagen no puede superar 5 MB.")
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        extension = ".png"
    elif content.startswith(b"\xff\xd8\xff"):
        extension = ".jpg"
    elif content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        extension = ".webp"
    else:
        raise HTTPException(415,"Solo imágenes PNG, JPEG o WebP.")
    UPLOAD_DIR.mkdir(exist_ok=True)
    path = UPLOAD_DIR / (uuid.uuid4().hex + extension)
    path.write_bytes(content)
    try:
        image = Imagen(id_propiedad=id_propiedad,url="/uploads/"+path.name)
        db.add(image)
        db.commit()
        db.refresh(image)
        return image
    except Exception:
        path.unlink(missing_ok=True)
        raise

# Visitas de clientes: la confirmación se entrega únicamente después del commit.
from datetime import datetime, timedelta, timezone
from sqlalchemy import or_
from pydantic import Field
from auth import get_current_user
from database.models import Visita

class VisitaCreate(BaseModel):
    id_propiedad: int
    fecha_hora: datetime
    comentario: str = Field(default="",max_length=2000)

@router.post("/visitas",status_code=201)
def agendar_visita(data: VisitaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if data.fecha_hora.tzinfo is None:
        raise HTTPException(422,"Indique fecha con zona horaria.")
    fecha = data.fecha_hora.astimezone(timezone.utc).replace(tzinfo=None)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if fecha <= now or fecha > now + timedelta(days=60):
        raise HTTPException(422,"Seleccione una fecha futura dentro de 60 días.")
    prop = db.query(Propiedad).filter(Propiedad.id_propiedad == data.id_propiedad,
        Propiedad.id_tenant == user.id_tenant).with_for_update().first()
    if not prop or prop.estado != "Disponible":
        raise HTTPException(409,"El inmueble no está disponible en su inmobiliaria.")
    cliente = db.query(Cliente).filter(Cliente.id_usuario == user.id).first()
    if not cliente:
        raise HTTPException(403,"Se requiere un perfil de cliente para agendar una visita.")
    # Bloquea también el agente para serializar visitas a inmuebles distintos.
    db.query(Agente).filter(Agente.id_agente == prop.id_agente).with_for_update().first()
    conflict = db.query(Visita).filter(Visita.id_tenant == prop.id_tenant,Visita.estado == "Programada",
        or_(Visita.id_agente == prop.id_agente,Visita.id_propiedad == prop.id_propiedad,Visita.id_cliente == cliente.id_cliente),
        Visita.fecha_hora > fecha-timedelta(hours=1),Visita.fecha_hora < fecha+timedelta(hours=1)).first()
    if conflict:
        raise HTTPException(409,"Ese horario ya tiene una visita programada.")
    visita = Visita(id_tenant=prop.id_tenant,id_cliente=cliente.id_cliente,id_propiedad=prop.id_propiedad,
                    id_agente=prop.id_agente,fecha_hora=fecha,comentario=data.comentario,estado="Programada")
    db.add(visita)
    db.commit()
    db.refresh(visita)
    return {"id_visita":visita.id_visita,"fecha_hora":fecha.replace(tzinfo=timezone.utc),"estado":visita.estado}

@router.get("/visitas")
def mis_visitas(db: Session = Depends(get_db), user=Depends(get_current_user)):
    cliente = db.query(Cliente).filter(Cliente.id_usuario == user.id).first()
    if not cliente:
        return []
    return db.query(Visita).filter(Visita.id_tenant == user.id_tenant,Visita.id_cliente == cliente.id_cliente).order_by(Visita.fecha_hora).all()
