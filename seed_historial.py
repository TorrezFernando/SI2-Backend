import sys
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from database.database import engine
import database.models  # Registra todos los modelos modulares
from modulo_administracion_configuracion.models import Tenant
from gestion_usuarios.models import Rol, Usuario
from modulo_inmuebles.models import (
    Propietario, Agente, Cliente, Propiedad, Visita, Contrato, Pago, Bitacora
)
from auth import get_password_hash

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

random.seed(42)  # reproducibilidad

HOY = date.today()

# Cada tenant tendra un rango de historial distinto, entre 6 y 12 meses,
# para que los datos no se vean todos "iguales" entre inmobiliarias.
RANGO_MESES_MIN = 6
RANGO_MESES_MAX = 12

NUEVOS_CLIENTES_BASE = [
    {"ci": "9000001", "nombre": "Cliente Historial Uno", "telefono": "70090001", "password": "Cliente.123@"},
    {"ci": "9000002", "nombre": "Cliente Historial Dos", "telefono": "70090002", "password": "Cliente.123@"},
    {"ci": "9000003", "nombre": "Cliente Historial Tres", "telefono": "70090003", "password": "Cliente.123@"},
]

NUEVO_AGENTE_BASE = {"ci": "9100001", "nombre": "Agente Historial Uno", "telefono": "70091001", "password": "Agente.123@"}


def fecha_aleatoria_en_rango(inicio: date, fin: date) -> date:
    dias_totales = (fin - inicio).days
    if dias_totales <= 0:
        return inicio
    return inicio + timedelta(days=random.randint(0, dias_totales))


def crear_usuario_con_perfil(db: Session, tenant: Tenant, ci: str, nombre: str, correo: str,
                              telefono: str, password: str, id_rol: int, ModeloPerfil):
    usuario = db.query(Usuario).filter(
        Usuario.correo == correo, Usuario.id_tenant == tenant.id_tenant
    ).first()
    if not usuario:
        usuario = Usuario(
            ci=ci, nombre=nombre, correo=correo, telefono=telefono,
            id_rol=id_rol, id_tenant=tenant.id_tenant,
            password_hash=get_password_hash(password),
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    perfil = db.query(ModeloPerfil).filter(ModeloPerfil.id_usuario == usuario.id).first()
    if not perfil:
        perfil = ModeloPerfil(id_usuario=usuario.id)
        db.add(perfil)
        db.commit()
        db.refresh(perfil)
    return perfil


def poblar_historial_de_tenant(db: Session, tenant: Tenant, rol_cliente: Rol, rol_agente: Rol):
    meses_historial = random.randint(RANGO_MESES_MIN, RANGO_MESES_MAX)
    fecha_inicio_historial = HOY - timedelta(days=meses_historial * 30)

    print(f"\n{'=' * 60}")
    print(f"[*] Tenant: {tenant.nombre} (slug: {tenant.slug}) -> historial de {meses_historial} meses")
    print(f"    Rango: {fecha_inicio_historial} -> {HOY}")
    print("=" * 60)

    propiedades = db.query(Propiedad).filter(Propiedad.id_tenant == tenant.id_tenant).all()
    if not propiedades:
        print("[!] Este tenant no tiene propiedades. Se omite.")
        return

    # Clientes y agentes existentes del tenant (creados por seed_data.py)
    clientes = db.query(Cliente).join(Usuario).filter(Usuario.id_tenant == tenant.id_tenant).all()
    agentes = db.query(Agente).join(Usuario).filter(Usuario.id_tenant == tenant.id_tenant).all()

    # Agregamos clientes y agente extra, propios de este tenant, para variedad
    for c in NUEVOS_CLIENTES_BASE:
        correo = f"{c['nombre'].lower().replace(' ', '.')}@{tenant.slug}.com"
        perfil = crear_usuario_con_perfil(
            db, tenant, c["ci"], c["nombre"], correo, c["telefono"], c["password"],
            rol_cliente.id_rol, Cliente
        )
        if perfil not in clientes:
            clientes.append(perfil)

    correo_agente_extra = f"{NUEVO_AGENTE_BASE['nombre'].lower().replace(' ', '.')}@{tenant.slug}.com"
    agente_extra = crear_usuario_con_perfil(
        db, tenant, NUEVO_AGENTE_BASE["ci"], NUEVO_AGENTE_BASE["nombre"], correo_agente_extra,
        NUEVO_AGENTE_BASE["telefono"], NUEVO_AGENTE_BASE["password"], rol_agente.id_rol, Agente
    )
    if agente_extra not in agentes:
        agentes.append(agente_extra)

    print(f"[+] {len(clientes)} clientes y {len(agentes)} agentes disponibles para el historial.")

    # 1. VISITAS
    total_visitas = 0
    for prop in propiedades:
        num_visitas = random.randint(5, 12)
        for _ in range(num_visitas):
            fecha_visita = fecha_aleatoria_en_rango(fecha_inicio_historial, HOY)
            if fecha_visita >= HOY - timedelta(days=3):
                estado = "Programada"
            else:
                estado = random.choices(
                    ["Realizada", "Cancelada", "No Asistio"], weights=[0.7, 0.2, 0.1]
                )[0]

            db.add(Visita(
                id_cliente=random.choice(clientes).id_cliente,
                id_propiedad=prop.id_propiedad,
                id_agente=random.choice(agentes).id_agente,
                id_tenant=tenant.id_tenant,
                fecha_hora=datetime.combine(fecha_visita, datetime.min.time()) + timedelta(hours=random.randint(9, 18)),
                comentario=random.choice([
                    "Cliente interesado en conocer detalles de financiamiento.",
                    "Visita de rutina, cliente evaluando varias opciones.",
                    "Cliente solicito ver la propiedad en horario vespertino.",
                    "Segunda visita, cliente muy interesado.",
                    "Cliente referido por otro cliente actual.",
                ]),
                estado=estado,
            ))
            total_visitas += 1
    db.commit()
    print(f"[+] {total_visitas} visitas historicas creadas.")

    # 2. CONTRATOS Y PAGOS
    propiedades_con_contrato = random.sample(propiedades, k=max(1, len(propiedades) - 1))
    total_contratos = 0
    total_pagos = 0

    for prop in propiedades_con_contrato:
        limite_inicio = fecha_inicio_historial + timedelta(days=int(meses_historial * 30 * 0.66))
        fecha_inicio_contrato = fecha_aleatoria_en_rango(fecha_inicio_historial, limite_inicio)

        cliente = random.choice(clientes)
        agente = random.choice(agentes)

        if prop.tipo_operacion == "Venta":
            tipo_contrato = "Venta Definitiva"
            fecha_fin_contrato = fecha_inicio_contrato + timedelta(days=random.choice([90, 120, 180]))
            monto_total = prop.precio
        elif prop.tipo_operacion == "Alquiler":
            tipo_contrato = "Contrato de Alquiler"
            fecha_fin_contrato = fecha_inicio_contrato + timedelta(days=365)
            monto_total = prop.precio
        else:  # Anticretico
            tipo_contrato = "Contrato Anticretico"
            fecha_fin_contrato = fecha_inicio_contrato + timedelta(days=730)
            monto_total = prop.precio

        contrato = Contrato(
            id_cliente=cliente.id_cliente,
            id_propiedad=prop.id_propiedad,
            id_agente=agente.id_agente,
            id_tenant=tenant.id_tenant,
            tipo_contrato=tipo_contrato,
            monto_total=monto_total,
            fecha_inicio=fecha_inicio_contrato,
            fecha_fin=fecha_fin_contrato,
        )
        db.add(contrato)
        db.commit()
        db.refresh(contrato)
        total_contratos += 1

        prop.estado = "Vendida" if prop.tipo_operacion == "Venta" else "Alquilada"
        db.add(prop)

        if prop.tipo_operacion == "Venta":
            inicial = (monto_total * Decimal("0.30")).quantize(Decimal("0.01"))
            db.add(Pago(
                id_contrato=contrato.id_contrato, monto=inicial,
                fecha_pago=datetime.combine(fecha_inicio_contrato, datetime.min.time()),
                metodo_pago="Transferencia Bancaria",
                numero_recibo=f"REC-{tenant.slug.upper()}-{contrato.id_contrato:05d}-01",
            ))
            total_pagos += 1

            restante = monto_total - inicial
            num_cuotas = random.choice([2, 3])
            monto_cuota = (restante / num_cuotas).quantize(Decimal("0.01"))
            fin_pagos = min(fecha_fin_contrato, HOY)
            for i in range(1, num_cuotas + 1):
                fecha_cuota = fecha_inicio_contrato + timedelta(
                    days=int((fin_pagos - fecha_inicio_contrato).days * i / (num_cuotas + 1))
                )
                if fecha_cuota > HOY:
                    break
                db.add(Pago(
                    id_contrato=contrato.id_contrato, monto=monto_cuota,
                    fecha_pago=datetime.combine(fecha_cuota, datetime.min.time()),
                    metodo_pago=random.choice(["Transferencia Bancaria", "Deposito", "Cheque"]),
                    numero_recibo=f"REC-{tenant.slug.upper()}-{contrato.id_contrato:05d}-{i+1:02d}",
                ))
                total_pagos += 1
        else:
            fecha_pago_actual = fecha_inicio_contrato
            contador = 1
            while fecha_pago_actual <= HOY and fecha_pago_actual <= fecha_fin_contrato:
                if prop.tipo_operacion == "Anticretico" and contador > 1:
                    break
                monto_periodo = monto_total
                db.add(Pago(
                    id_contrato=contrato.id_contrato, monto=monto_periodo,
                    fecha_pago=datetime.combine(fecha_pago_actual, datetime.min.time()),
                    metodo_pago=random.choice(["Transferencia Bancaria", "Deposito", "Efectivo"]),
                    numero_recibo=f"REC-{tenant.slug.upper()}-{contrato.id_contrato:05d}-{contador:02d}",
                ))
                total_pagos += 1
                fecha_pago_actual += timedelta(days=30)
                contador += 1

        db.commit()

    print(f"[+] {total_contratos} contratos y {total_pagos} pagos historicos creados.")
    print(f"[i] {len(propiedades) - len(propiedades_con_contrato)} propiedad(es) quedaron 'Disponible'.")

    # 3. BITACORA
    admin = db.query(Usuario).join(Rol).filter(
        Usuario.id_tenant == tenant.id_tenant, Rol.nombre == "Administrador"
    ).first()
    if admin:
        num_puntos_revision = max(1, meses_historial // 2)
        acciones = [(fecha_inicio_historial, "Inicio de registro de actividad comercial del periodo")]
        for i in range(1, num_puntos_revision + 1):
            acciones.append((
                fecha_inicio_historial + timedelta(days=i * 60),
                "Revision periodica de cartera de propiedades",
            ))
        acciones.append((HOY, "Poblado de historial de actividad para pruebas de reportes"))

        for fecha_accion, descripcion in acciones:
            if fecha_accion > HOY:
                continue
            db.add(Bitacora(
                id_usuario=admin.id, id_tenant=tenant.id_tenant, accion=descripcion,
                fecha_hora=datetime.combine(fecha_accion, datetime.min.time()),
            ))
        db.commit()
        print(f"[+] {len(acciones)} entradas de bitacora registradas.")


def poblar_historial():
    print("=" * 60)
    print("[*] POBLANDO HISTORIAL DE ACTIVIDAD PARA TODOS LOS TENANTS")
    print("=" * 60)

    with Session(engine) as db:
        tenants = db.query(Tenant).all()
        if not tenants:
            print("[!] No hay tenants registrados. Ejecuta primero seed_data.py")
            sys.exit(1)

        rol_cliente = db.query(Rol).filter(Rol.nombre == "Cliente").first()
        rol_agente = db.query(Rol).filter(Rol.nombre == "Agente").first()
        if not rol_cliente or not rol_agente:
            print("[!] Faltan roles base (Cliente/Agente). Ejecuta primero seed_data.py")
            sys.exit(1)

        for tenant in tenants:
            poblar_historial_de_tenant(db, tenant, rol_cliente, rol_agente)

    print("\n" + "=" * 60)
    print("[*] HISTORIAL DE ACTIVIDAD POBLADO EXITOSAMENTE PARA TODOS LOS TENANTS")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    poblar_historial()