"""Contratos, cuotas y comunicaciones del sprint 3. Importes en moneda del contrato."""
import calendar
import json
import os
import smtplib
import ssl
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_DOWN
from email.message import EmailMessage
from io import BytesIO
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Session
from database.database import Base, get_db, SessionLocal
from database.models import Contrato, Pago, Cliente, Agente, Usuario, Propiedad
from auth import get_current_user, require_admin, require_staff, is_admin
from planes import today, require_ai

router = APIRouter(prefix="/api", tags=["Operaciones sprint 3"])

class Cuota(Base):
    __tablename__ = "cuota_contrato"
    id = Column(Integer, primary_key=True)
    id_contrato = Column(Integer, ForeignKey("contrato.id_contrato"), nullable=False)
    numero = Column(Integer, nullable=False)
    vencimiento = Column(Date, nullable=False)
    monto = Column(Numeric(12,2), nullable=False)
    __table_args__ = (UniqueConstraint("id_contrato","numero"),)

class Abono(Base):
    __tablename__ = "abono_cuota"
    id = Column(Integer, primary_key=True)
    id_cuota = Column(Integer, ForeignKey("cuota_contrato.id"), nullable=False)
    id_pago = Column(Integer, ForeignKey("pago.id_pago"), nullable=False, unique=True)
    clave = Column(String(80), nullable=False)
    id_tenant = Column(Integer, ForeignKey("tenant.id_tenant"), nullable=False)
    __table_args__ = (UniqueConstraint("id_tenant","clave"),)

class Dispositivo(Base):
    __tablename__ = "dispositivo_fcm"
    id = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    dispositivo = Column(String(100), nullable=False)
    token = Column(String(4096), nullable=False, unique=True)
    plataforma = Column(String(10), nullable=False)
    __table_args__ = (UniqueConstraint("id_usuario","dispositivo"),)

class AvisoPush(Base):
    __tablename__ = "aviso_cuota_fcm"
    id = Column(Integer, primary_key=True)
    id_cuota = Column(Integer, ForeignKey("cuota_contrato.id"), nullable=False)
    dispositivo_id = Column(Integer, ForeignKey("dispositivo_fcm.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    __table_args__ = (UniqueConstraint("id_cuota","dispositivo_id","fecha"),)

def contrato_visible(db, user, cid, staff=False):
    c = db.query(Contrato).filter_by(id_contrato=cid,id_tenant=user.id_tenant).first()
    if not c or (not staff and not is_admin(user) and c.cliente.id_usuario != user.id):
        raise HTTPException(404,"Contrato no encontrado.")
    return c

def pagado(db, cuota):
    return sum((p.monto for p in db.query(Pago).join(Abono,Abono.id_pago==Pago.id_pago).filter(Abono.id_cuota==cuota.id)),Decimal("0"))

def cuota_json(db,q):
    abonado=pagado(db,q)
    saldo=max(Decimal("0"),q.monto-abonado)
    return {"id":q.id,"numero":q.numero,"id_contrato":q.id_contrato,"vencimiento":q.vencimiento,
            "monto":q.monto,"pagado":abonado,"saldo":saldo,
            "estado":"pagada" if not saldo else "vencida" if q.vencimiento<today() else "pendiente"}

class AltaContrato(BaseModel):
    id_cliente: int
    id_propiedad: int
    id_agente: int
    tipo_contrato: Literal["Venta","Alquiler","Anticretico"]
    monto_total: Decimal = Field(gt=0,max_digits=12,decimal_places=2)
    fecha_inicio: date
    fecha_fin: date | None = None
    cuotas: int = Field(ge=1,le=360)
    primer_vencimiento: date
    @model_validator(mode="after")
    def dates(self):
        if self.fecha_fin and self.fecha_fin<self.fecha_inicio:
            raise ValueError("Fecha final anterior al inicio")
        if self.primer_vencimiento<self.fecha_inicio or self.monto_total<Decimal(self.cuotas)/100:
            raise ValueError("Vencimiento o importe insuficiente para las cuotas")
        return self

@router.post("/contratos",status_code=201)
def alta_contrato(data:AltaContrato,db:Session=Depends(get_db),user=Depends(require_admin)):
    for model,pk,ident in [(Cliente,Cliente.id_cliente,data.id_cliente),(Agente,Agente.id_agente,data.id_agente)]:
        if not db.query(model).join(Usuario).filter(pk==ident,Usuario.id_tenant==user.id_tenant).first():
            raise HTTPException(422,"Cliente o agente de otra empresa.")
    if not db.query(Propiedad).filter_by(id_propiedad=data.id_propiedad,id_tenant=user.id_tenant).first():
        raise HTTPException(422,"Inmueble no válido.")
    c=Contrato(**data.model_dump(exclude={"cuotas","primer_vencimiento"}),id_tenant=user.id_tenant)
    db.add(c); db.flush()
    base=(data.monto_total/data.cuotas).quantize(Decimal("0.01"),rounding=ROUND_DOWN)
    for i in range(data.cuotas):
        month=data.primer_vencimiento.month-1+i
        year=data.primer_vencimiento.year+month//12
        due=date(year,month%12+1,min(data.primer_vencimiento.day,calendar.monthrange(year,month%12+1)[1]))
        db.add(Cuota(id_contrato=c.id_contrato,numero=i+1,vencimiento=due,
                     monto=base if i<data.cuotas-1 else data.monto_total-base*(data.cuotas-1)))
    db.commit()
    return {"id_contrato":c.id_contrato,"cuotas":data.cuotas}

class CuotaResponse(BaseModel):
    id:int
    numero:int
    id_contrato:int
    vencimiento:date
    monto:Decimal
    pagado:Decimal
    saldo:Decimal
    estado:Literal["pagada","vencida","pendiente"]

class PagoResponse(BaseModel):
    id_pago:int
    monto:Decimal
    fecha:datetime | None
    recibo:str | None

class ContratoResponse(BaseModel):
    id_contrato:int
    tipo:str
    monto_total:Decimal
    pagado:Decimal
    saldo:Decimal
    cuotas:list[CuotaResponse]
    pagos:list[PagoResponse]
    cronograma_disponible:bool

class CuentaResponse(BaseModel):
    contratos:list[ContratoResponse]

@router.get("/mi-cuenta",response_model=CuentaResponse)
def mi_cuenta(db:Session=Depends(get_db),user=Depends(get_current_user)):
    contratos=db.query(Contrato).join(Cliente).filter(Contrato.id_tenant==user.id_tenant,Cliente.id_usuario==user.id).all()
    return cuenta_resultado(db,contratos)

def cuenta_resultado(db,contratos):
    result=[]
    for c in contratos:
        cuotas=[cuota_json(db,q) for q in db.query(Cuota).filter_by(id_contrato=c.id_contrato).order_by(Cuota.numero)]
        pagos=db.query(Pago).filter_by(id_contrato=c.id_contrato).all()
        result.append({"id_contrato":c.id_contrato,"tipo":c.tipo_contrato,"monto_total":c.monto_total,
                       "pagado":sum((p.monto for p in pagos),Decimal("0")),"saldo":max(Decimal("0"),c.monto_total-sum((p.monto for p in pagos),Decimal("0"))),
                       "cuotas":cuotas,"pagos":[{"id_pago":p.id_pago,"monto":p.monto,"fecha":p.fecha_pago,"recibo":p.numero_recibo} for p in pagos],
                       "cronograma_disponible":bool(cuotas)})
    return {"contratos":result}

@router.get("/contratos",response_model=CuentaResponse)
def contratos(db:Session=Depends(get_db),user=Depends(require_admin)):
    return cuenta_resultado(db,db.query(Contrato).filter_by(id_tenant=user.id_tenant).all())

@router.get("/contratos/{cid}/cuotas",response_model=list[CuotaResponse])
def cuotas(cid:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    contrato_visible(db,user,cid)
    return [cuota_json(db,q) for q in db.query(Cuota).filter_by(id_contrato=cid).order_by(Cuota.numero)]

class PagoCuota(BaseModel):
    monto: Decimal = Field(gt=0,max_digits=12,decimal_places=2)
    clave_idempotencia: str = Field(min_length=8,max_length=80)
    confirma_simulacion: Literal[True]

@router.post("/cuotas/{qid}/pagos",status_code=201)
def pagar(qid:int,data:PagoCuota,db:Session=Depends(get_db),user=Depends(require_admin)):
    q=db.query(Cuota).filter_by(id=qid).with_for_update().first()
    if not q: raise HTTPException(404,"Cuota no encontrada.")
    c=contrato_visible(db,user,q.id_contrato,True)
    db.query(Contrato).filter_by(id_contrato=c.id_contrato).with_for_update().first()
    previous=db.query(Abono).filter_by(id_tenant=user.id_tenant,clave=data.clave_idempotencia).first()
    if previous:
        p=db.get(Pago,previous.id_pago)
        if previous.id_cuota!=qid or p.monto!=data.monto: raise HTTPException(409,"Clave reutilizada con otros datos.")
        return {"id_pago":p.id_pago,"duplicado":True}
    total=sum((p.monto for p in db.query(Pago).filter_by(id_contrato=c.id_contrato)),Decimal("0"))
    if data.monto>q.monto-pagado(db,q) or data.monto>c.monto_total-total:
        raise HTTPException(409,"El abono excede el saldo.")
    p=Pago(id_contrato=c.id_contrato,monto=data.monto,metodo_pago="Simulado")
    db.add(p);db.flush();p.numero_recibo=f"DEMO-{user.id_tenant}-{p.id_pago}"
    db.add(Abono(id_cuota=qid,id_pago=p.id_pago,id_tenant=user.id_tenant,clave=data.clave_idempotencia));db.commit()
    return {"id_pago":p.id_pago,"duplicado":False}

def recibo(db,user,pid):
    p=db.get(Pago,pid)
    if not p: raise HTTPException(404,"Pago no encontrado.")
    contrato_visible(db,user,p.id_contrato)
    from reportlab.pdfgen import canvas
    out=BytesIO();pdf=canvas.Canvas(out)
    for y,text in [(790,"RECIBO DE DEMOSTRACION"),(755,f"Referencia: {p.numero_recibo or p.id_pago}"),
                   (730,f"Contrato: {p.id_contrato}"),(705,f"Importe: {p.monto}"),(680,f"Fecha: {p.fecha_pago}"),
                   (645,"Sin cobro bancario ni validez fiscal.")]:
        pdf.drawString(45,y,text)
    pdf.save()
    return p,out.getvalue()

@router.get("/pagos/{pid}/recibo.pdf",responses={200:{"content":{"application/pdf":{}}}})
def pdf_recibo(pid:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    _,content=recibo(db,user,pid)
    return Response(content,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="recibo-{pid}.pdf"'})

@router.post("/pagos/{pid}/enviar-recibo")
def enviar_recibo(pid:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    p,content=recibo(db,user,pid)
    recipient=p.contrato.cliente.usuario.correo
    host=os.getenv("SMTP_HOST");login=os.getenv("SMTP_USER");password=os.getenv("SMTP_PASSWORD")
    if not all([host,login,password]): raise HTTPException(503,"SMTP no configurado.")
    msg=EmailMessage();msg["From"]=login;msg["To"]=recipient;msg["Subject"]=f"Recibo simulado {p.numero_recibo or p.id_pago}"
    msg.set_content("Adjuntamos su recibo de demostración. No representa un cobro real.")
    msg.add_attachment(content,maintype="application",subtype="pdf",filename=f"recibo-{pid}.pdf")
    try:
        with smtplib.SMTP(host,int(os.getenv("SMTP_PORT","587")),timeout=20) as smtp:
            smtp.starttls(context=ssl.create_default_context());smtp.login(login,password);smtp.send_message(msg)
    except (OSError,smtplib.SMTPException): raise HTTPException(502,"El servidor SMTP no confirmó el envío.")
    return {"estado":"aceptado_por_smtp","destinatario":recipient}

class TokenFCM(BaseModel):
    dispositivo: str = Field(min_length=1,max_length=100)
    token: str = Field(min_length=20,max_length=4096)
    plataforma: Literal["web","android","ios"]

@router.put("/notificaciones/tokens",status_code=200)
def registrar_token(data:TokenFCM,db:Session=Depends(get_db),user=Depends(get_current_user)):
    other=db.query(Dispositivo).filter_by(token=data.token).first()
    if other and (other.id_usuario!=user.id or other.dispositivo!=data.dispositivo):
        raise HTTPException(409,"Token vinculado a otro dispositivo. Darlo de baja antes de reasignarlo.")
    row=db.query(Dispositivo).filter_by(id_usuario=user.id,dispositivo=data.dispositivo).first()
    if not row: row=Dispositivo(id_usuario=user.id);db.add(row)
    for k,v in data.model_dump().items():setattr(row,k,v)
    db.commit();return {"id":row.id,"dispositivo":row.dispositivo,"plataforma":row.plataforma}

@router.delete("/notificaciones/tokens/{ident}",status_code=204)
def baja_token(ident:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    row=db.query(Dispositivo).filter_by(id=ident,id_usuario=user.id).first()
    if not row:raise HTTPException(404,"Dispositivo no encontrado.")
    db.query(AvisoPush).filter_by(dispositivo_id=ident).delete();db.delete(row);db.commit()
    return Response(status_code=204)

@router.get("/notificaciones/tokens")
def tokens(db:Session=Depends(get_db),user=Depends(get_current_user)):
    return [{"id":r.id,"dispositivo":r.dispositivo,"plataforma":r.plataforma} for r in db.query(Dispositivo).filter_by(id_usuario=user.id)]

def enviar_avisos(tenant_id=None):
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):raise HTTPException(503,"Firebase no configurado.")
    import firebase_admin
    from firebase_admin import messaging
    try:
        try: app=firebase_admin.get_app()
        except ValueError:app=firebase_admin.initialize_app()
    except Exception:raise HTTPException(503,"Credenciales Firebase no disponibles o inválidas.")
    sent=failed=0
    with SessionLocal() as db:
        query=db.query(Cuota).join(Contrato).filter(Cuota.vencimiento<=date.fromordinal(today().toordinal()+7))
        if tenant_id is not None:query=query.filter(Contrato.id_tenant==tenant_id)
        for q in query.all():
            if pagado(db,q)>=q.monto:continue
            c=db.get(Contrato,q.id_contrato)
            for device in db.query(Dispositivo).filter_by(id_usuario=c.cliente.id_usuario).all():
                if db.query(AvisoPush).filter_by(id_cuota=q.id,dispositivo_id=device.id,fecha=today()).first():continue
                try:
                    messaging.send(messaging.Message(notification=messaging.Notification(title="Recordatorio de cuota",body=f"Revise su cuota con vencimiento {q.vencimiento}."),token=device.token),app=app)
                except Exception:
                    failed+=1;continue
                db.add(AvisoPush(id_cuota=q.id,dispositivo_id=device.id,fecha=today()));db.commit();sent+=1
    return {"enviados":sent,"fallidos":failed}

@router.post("/notificaciones/procesar")
def procesar(user=Depends(require_admin)):
    return enviar_avisos(user.id_tenant)

class TasacionRequest(BaseModel):
    id_propiedad: int

class TasacionIA(BaseModel):
    minimo: Decimal = Field(gt=0,max_digits=12,decimal_places=2)
    estimado: Decimal = Field(gt=0,max_digits=12,decimal_places=2)
    maximo: Decimal = Field(gt=0,max_digits=12,decimal_places=2)
    explicacion: str = Field(min_length=10,max_length=3000)
    @model_validator(mode="after")
    def rango(self):
        if not self.minimo<=self.estimado<=self.maximo:raise ValueError("Rango inconsistente")
        return self

@router.post("/ia/tasaciones",response_model=TasacionIA)
def tasar(data:TasacionRequest,db:Session=Depends(get_db),user=Depends(get_current_user)):
    require_ai(user,"tasacion")
    p=db.query(Propiedad).filter_by(id_propiedad=data.id_propiedad,id_tenant=user.id_tenant).first()
    if not p:raise HTTPException(404,"Inmueble no encontrado.")
    comps=db.query(Propiedad).filter(Propiedad.id_tenant==user.id_tenant,Propiedad.id_propiedad!=p.id_propiedad,
             Propiedad.id_zona==p.id_zona,Propiedad.id_tipo_inmueble==p.id_tipo_inmueble,Propiedad.tipo_operacion==p.tipo_operacion).limit(20).all()
    if len(comps)<3:raise HTTPException(422,"Se requieren al menos tres inmuebles comparables de igual zona, tipo y operación.")
    from ia_router import generate
    facts=lambda x:{"precio":str(x.precio),"superficie":str(x.superficie_m2),"habitaciones":x.habitaciones}
    prompt="Estima un rango orientativo de precio basándote exclusivamente en estos anuncios internos, no ventas verificadas. Misma moneda y operación. No inventes datos de mercado. Devuelve JSON minimo, estimado, maximo, explicacion. Inmueble: "+json.dumps(facts(p))+" Comparables: "+json.dumps([facts(x) for x in comps])
    try:return TasacionIA.model_validate_json(generate(prompt,user,True))
    except ValueError:raise HTTPException(502,"Gemini devolvió una tasación inválida.")
