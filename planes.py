"""Suscripciones mensuales. Los pagos de este proyecto son exclusivamente simulados."""
import calendar
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Session
from database.database import Base, get_db
from database.models import Tenant, Usuario, Rol, Propiedad
from auth import require_admin, get_current_user, is_superadmin, tenant_scope

PlanName = Literal["normal","pro","premium"]
TERMS_VERSION = "2026-10-25"
TERMS = [
    "El servicio se ofrece por períodos mensuales conforme al plan seleccionado.",
    "Los pagos y comprobantes de esta versión son simulados: no realizan cobros bancarios ni tienen validez fiscal.",
    "El administrador es responsable de la información publicada y del uso autorizado de las cuentas de su empresa.",
    "Se avisará en la aplicación desde siete días antes del vencimiento y durante el período de gracia de siete días.",
    "Tras el período de gracia se suspende el uso operativo y de IA; el administrador conserva acceso al plan y a la regularización. No se borran datos por impago.",
    "Un cambio de plan es inmediato y conserva el vencimiento mensual. No hay prorrateos ni cargos reales en esta demostración.",
    "Para bajar de plan se debe reducir previamente el uso al límite del plan de destino; el sistema no elimina registros automáticamente.",
    "La IA puede equivocarse y sus resultados deben revisarse. La disponibilidad depende del proveedor, de su cuota y de límites técnicos de protección.",
    "La cancelación desactiva la renovación y mantiene el acceso hasta el vencimiento ya cubierto. Se puede reactivar aceptando los términos vigentes.",
    "Los precios quedan sujetos a la configuración o acuerdo comercial; esta versión no asigna importes no definidos.",
]
PLANS = {
    "normal": {"nombre":"Normal","empleados":int(os.getenv("PLAN_NORMAL_EMPLEADOS","10")),"catalogo":int(os.getenv("PLAN_NORMAL_CATALOGO","20")),"ia":[]},
    "pro": {"nombre":"Pro","empleados":None,"catalogo":int(os.getenv("PLAN_PRO_CATALOGO","100")),"ia":["chat"]},
    "premium": {"nombre":"Premium","empleados":None,"catalogo":None,"ia":["chat","descripcion","reportes"]},
}
router = APIRouter(prefix="/suscripciones",tags=["Planes y suscripciones"])

class Suscripcion(Base):
    __tablename__ = "suscripcion"
    id_tenant = Column(Integer,ForeignKey("tenant.id_tenant"),primary_key=True)
    inicio = Column(Date,nullable=False)
    vencimiento = Column(Date,nullable=False)
    dia_cobro = Column(Integer,nullable=False)
    cancelada = Column(Integer,nullable=False,default=0)
    terminos_version = Column(String(30))
    aceptado_por = Column(Integer,ForeignKey("usuario.id"))
    aceptado_en = Column(DateTime)

class PagoSuscripcion(Base):
    __tablename__ = "pago_suscripcion"
    id = Column(Integer,primary_key=True)
    id_tenant = Column(Integer,ForeignKey("tenant.id_tenant"),nullable=False)
    periodo = Column(Date,nullable=False)
    nuevo_vencimiento = Column(Date,nullable=False)
    registrado_por = Column(Integer,ForeignKey("usuario.id"),nullable=False)
    fecha = Column(DateTime,nullable=False,default=datetime.utcnow)
    modo = Column(String(20),nullable=False,default="simulado")
    __table_args__ = (UniqueConstraint("id_tenant","periodo",name="uq_pago_suscripcion_periodo"),)

def today():
    return datetime.now(ZoneInfo("America/La_Paz")).date()

def next_month(value, anchor=None):
    month = value.month % 12 + 1
    year = value.year + (value.month == 12)
    return date(year,month,min(anchor or value.day,calendar.monthrange(year,month)[1]))

def plan_name(tenant):
    value = (tenant.plan or "normal").lower()
    return {"basico":"normal","básico":"normal"}.get(value,value) if value in {*PLANS,"basico","básico"} else "normal"

def employee_count(db, tenant_id):
    # Clientes y propietarios no son empleados. Los roles personalizados cuentan.
    return db.query(Usuario).outerjoin(Rol).filter(Usuario.id_tenant == tenant_id,
        (Rol.nombre.is_(None)) | (~func.lower(Rol.nombre).in_(["cliente","propietario"])) | Usuario.agente.has()).count()

def is_employee(db, role_id):
    role = db.get(Rol,role_id)
    return role is None or role.nombre.lower() not in {"cliente","propietario"}

def due_for(db, tenant):
    sub = db.get(Suscripcion,tenant.id_tenant)
    return sub, sub.vencimiento if sub else tenant.fecha_vencimiento_pago

def state(db, tenant, on=None):
    on = on or today()
    sub,due = due_for(db,tenant)
    if not tenant.estado:
        return "inactiva"
    if not due:
        return "activa"
    if sub and sub.cancelada and on >= due:
        return "cancelada"
    days = (due-on).days
    if days < -7:
        return "suspendida"
    if days <= 0:
        return "en_gracia"
    return "por_vencer" if days <= 7 else "activa"

def assert_operational(db,tenant):
    if state(db,tenant) in {"suspendida","cancelada","inactiva"}:
        raise HTTPException(402,"Suscripción suspendida o cancelada. El administrador puede regularizarla en Empresas y planes.")

def check_employee_limit(db,tenant,role_id):
    assert_operational(db,tenant)
    limit = PLANS[plan_name(tenant)]["empleados"]
    if is_employee(db,role_id) and limit is not None and employee_count(db,tenant.id_tenant) >= limit:
        raise HTTPException(409,f"El plan Normal permite {limit} empleados, incluido el administrador.")

def check_property_limit(db,tenant):
    assert_operational(db,tenant)
    limit = PLANS[plan_name(tenant)]["catalogo"]
    if limit is not None and db.query(Propiedad).filter(Propiedad.id_tenant == tenant.id_tenant).count() >= limit:
        raise HTTPException(409,f"Su plan permite {limit} inmuebles registrados.")

def require_ai(user, feature):
    from sqlalchemy.orm import object_session
    db = object_session(user)
    assert_operational(db,user.tenant)
    if feature not in PLANS[plan_name(user.tenant)]["ia"]:
        raise HTTPException(403,"Esta función de IA no está incluida en su plan.")

def initialize(db,tenant,actor=None,accepted=False):
    sub = db.get(Suscripcion,tenant.id_tenant)
    if not sub:
        start = today()
        sub = Suscripcion(id_tenant=tenant.id_tenant,inicio=start,dia_cobro=(tenant.fecha_vencimiento_pago or start).day,
                          vencimiento=tenant.fecha_vencimiento_pago or next_month(start),cancelada=0)
        db.add(sub)
    if accepted:
        sub.terminos_version=TERMS_VERSION
        sub.aceptado_por=actor.id
        sub.aceptado_en=datetime.utcnow()
    tenant.fecha_vencimiento_pago=sub.vencimiento
    return sub

def summary(db,tenant):
    sub,due=due_for(db,tenant)
    status=state(db,tenant)
    days=(due-today()).days if due else None
    notice = None
    if status == "por_vencer":
        notice=f"El pago mensual vence el {due.isoformat()} (en {days} días)."
    elif status == "en_gracia":
        notice=f"Pago vencido desde {due.isoformat()}. Regularice antes del {(due+timedelta(days=7)).isoformat()} para evitar la suspensión."
    elif status in {"suspendida","cancelada"}:
        notice="Suscripción " + status + ". Regularice o reactive su plan para continuar."
    if sub and sub.cancelada and status not in {"cancelada","suspendida"}:
        notice=f"Renovación cancelada. El acceso finaliza el {due.isoformat()}."
    return {"id_tenant":tenant.id_tenant,"nombre":tenant.nombre,"dominio":tenant.slug,"estado":tenant.estado,
            "plan":plan_name(tenant),"limites":PLANS[plan_name(tenant)],"empleados_usados":employee_count(db,tenant.id_tenant),
            "catalogo_usado":db.query(Propiedad).filter(Propiedad.id_tenant == tenant.id_tenant).count(),
            "vencimiento":due,"estado_suscripcion":status,"aviso":notice,"renovacion":not bool(sub and sub.cancelada),
            "terminos_aceptados":bool(sub and sub.terminos_version==TERMS_VERSION),"modo_pagos":"simulado"}

def get_tenant(db,user,tid,lock=False):
    tenant_scope(user,tid)
    query=db.query(Tenant).filter(Tenant.id_tenant==tid)
    tenant=(query.with_for_update() if lock else query).first()
    if not tenant:
        raise HTTPException(404,"Empresa no encontrada.")
    return tenant

@router.get("/planes")
def plans():
    return [{"id":key,**value,"precio_mensual":None} for key,value in PLANS.items()]

@router.get("/terminos")
def terms():
    return {"version":TERMS_VERSION,"condiciones":TERMS}

@router.get("/mi-estado")
def my_state(db: Session=Depends(get_db),user=Depends(get_current_user)):
    initialize(db,user.tenant)
    db.commit()
    return summary(db,user.tenant)

class CambioPlan(BaseModel):
    plan: PlanName
    acepta_terminos: bool = False

@router.put("/{tid}/plan")
def change_plan(tid:int,data:CambioPlan,db:Session=Depends(get_db),user=Depends(require_admin)):
    tenant=get_tenant(db,user,tid,True)
    if not data.acepta_terminos:
        raise HTTPException(422,"Debe aceptar los términos y condiciones.")
    limits=PLANS[data.plan]
    if limits["empleados"] is not None and employee_count(db,tid)>limits["empleados"]:
        raise HTTPException(409,"Reduzca la cantidad de empleados antes de bajar a este plan.")
    if limits["catalogo"] is not None and db.query(Propiedad).filter(Propiedad.id_tenant==tid).count()>limits["catalogo"]:
        raise HTTPException(409,"Reduzca el catálogo antes de bajar a este plan.")
    initialize(db,tenant,user,True)
    tenant.plan=data.plan
    # Campo antiguo de compatibilidad; el límite real usa None para ilimitado.
    tenant.max_propiedades=limits["catalogo"] or 2147483647
    db.commit()
    return summary(db,tenant)

class SimularPago(BaseModel):
    periodo: date
    confirma_simulacion: bool = False

@router.post("/{tid}/pagos-simulados")
def pay(tid:int,data:SimularPago,db:Session=Depends(get_db),user=Depends(require_admin)):
    tenant=get_tenant(db,user,tid,True)
    if not data.confirma_simulacion:
        raise HTTPException(422,"Confirme que se trata de un pago simulado.")
    previous=db.query(PagoSuscripcion).filter_by(id_tenant=tid,periodo=data.periodo).first()
    if previous:
        return {"pago_id":previous.id,"duplicado":True,"suscripcion":summary(db,tenant)}
    sub=initialize(db,tenant)
    if not sub.terminos_version:
        raise HTTPException(422,"Seleccione su plan y acepte los términos antes de registrar el pago.")
    if data.periodo!=sub.vencimiento:
        raise HTTPException(409,"El período cambió. Actualice la pantalla.")
    if sub.cancelada:
        raise HTTPException(409,"Reactive la renovación antes de pagar.")
    # Impagos deben regularizar cada mensualidad; un pago no elimina meses atrasados.
    new_due=next_month(sub.vencimiento,sub.dia_cobro)
    row=PagoSuscripcion(id_tenant=tid,periodo=sub.vencimiento,nuevo_vencimiento=new_due,registrado_por=user.id)
    db.add(row)
    sub.vencimiento=new_due
    tenant.fecha_vencimiento_pago=new_due
    db.commit()
    return {"pago_id":row.id,"duplicado":False,"suscripcion":summary(db,tenant)}

@router.get("/{tid}/pagos")
def history(tid:int,db:Session=Depends(get_db),user=Depends(require_admin)):
    get_tenant(db,user,tid)
    return db.query(PagoSuscripcion).filter_by(id_tenant=tid).order_by(PagoSuscripcion.fecha.desc()).all()

class Renovacion(BaseModel):
    activa: bool
    acepta_terminos: bool = False

@router.put("/{tid}/renovacion")
def renewal(tid:int,data:Renovacion,db:Session=Depends(get_db),user=Depends(require_admin)):
    tenant=get_tenant(db,user,tid,True)
    if data.activa and not data.acepta_terminos:
        raise HTTPException(422,"Debe aceptar los términos para reactivar.")
    sub=initialize(db,tenant,user,data.acepta_terminos)
    sub.cancelada=0 if data.activa else 1
    db.commit()
    return summary(db,tenant)
