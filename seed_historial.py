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
    Propietario, Agente, Cliente, Propiedad, Imagen,
    Caracteristica, Visita, Contrato, Pago, Bitacora,
    TipoInmueble, Zona
)
from auth import get_password_hash

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

random.seed(42)  # reproducibilidad: mismos datos cada vez que se corre

HOY = date.today()
MESES_HISTORIAL = 5
FECHA_INICIO_HISTORIAL = HOY - timedelta(days=MESES_HISTORIAL * 30)

TENANT_NOMBRE = "Inmobiliaria Raíces"

NUEVOS_CLIENTES = [
    {"ci": "5000001", "nombre": "Maria Fernandez", "correo": "maria.fernandez@raices.com",
     "telefono": "70011111", "password": "Cliente.123@"},
    {"ci": "5000002", "nombre": "Jorge Aguilar", "correo": "jorge.aguilar@raices.com",
     "telefono": "70022222", "password": "Cliente.123@"},
    {"ci": "5000003", "nombre": "Lucia Rojas", "correo": "lucia.rojas@raices.com",
     "telefono": "70033333", "password": "Cliente.123@"},
]

NUEVOS_AGENTES = [
    {"ci": "6000001", "nombre": "Diego Salazar", "correo": "diego.salazar@raices.com",
     "telefono": "70044444", "password": "Agente.123@"},
]


def fecha_aleatoria_en_rango(inicio: date, fin: date) -> date:
    """Devuelve una fecha aleatoria entre inicio y fin (inclusive)."""
    dias_totales = (fin - inicio).days
    if dias_totales <= 0:
        return inicio
    return inicio + timedelta(days=random.randint(0, dias_totales))


def crear_usuario_con_perfil(db: Session, tenant, datos: dict, id_rol: int, ModeloPerfil, campo_lista: list, nombre_map: dict):
    """Crea (si no existe) un Usuario + su perfil especializado (Agente/Cliente), y lo registra en nombre_map."""
    user = db.query(Usuario).filter(
        Usuario.correo == datos["correo"],
        Usuario.id_tenant == tenant.id_tenant
    ).first()
    if not user:
        user = Usuario(
            ci=datos["ci"],
            nombre=datos["nombre"],
            correo=datos["correo"],
            telefono=datos["telefono"],
            id_rol=id_rol,
            id_tenant=tenant.id_tenant,
            password_hash=get_password_hash(datos["password"])
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    perfil = db.query(ModeloPerfil).filter(ModeloPerfil.id_usuario == user.id).first()
    if not perfil:
        perfil = ModeloPerfil(id_usuario=user.id)
        db.add(perfil)
        db.commit()
        db.refresh(perfil)

    nombre_map[datos["correo"]] = perfil
    return perfil


def poblar_historial():
    print("=" * 60)
    print("[*] POBLANDO HISTORIAL DE ACTIVIDAD (ULTIMOS {} MESES)".format(MESES_HISTORIAL))
    print("=" * 60)
    print(f"[i] Rango de fechas: {FECHA_INICIO_HISTORIAL} -> {HOY}")

    with Session(engine) as db:
        tenant = db.query(Tenant).filter(Tenant.nombre == TENANT_NOMBRE).first()
        if not tenant:
            print(f"[!] No se encontro el tenant '{TENANT_NOMBRE}'. Ejecuta primero seed_data.py")
            sys.exit(1)

        propiedades = db.query(Propiedad).filter(Propiedad.id_tenant == tenant.id_tenant).all()
        if not propiedades:
            print("[!] No hay propiedades registradas. Ejecuta primero seed_data.py")
            sys.exit(1)

        rol_cliente = db.query(Rol).filter(Rol.nombre == "Cliente").first()
        rol_agente = db.query(Rol).filter(Rol.nombre == "Agente").first()

        # 1. CLIENTES Y AGENTES ADICIONALES
        print("\n[1] Creando clientes y agentes adicionales...")
        clientes_map = {}
        agentes_map = {}

        cliente_original = db.query(Cliente).join(Usuario).filter(
            Usuario.correo == "cliente@raices.com", Usuario.id_tenant == tenant.id_tenant
        ).first()
        if cliente_original:
            clientes_map["cliente@raices.com"] = cliente_original

        agente_original = db.query(Agente).join(Usuario).filter(
            Usuario.correo == "agente@raices.com", Usuario.id_tenant == tenant.id_tenant
        ).first()
        if agente_original:
            agentes_map["agente@raices.com"] = agente_original

        for c in NUEVOS_CLIENTES:
            crear_usuario_con_perfil(db, tenant, c, rol_cliente.id_rol, Cliente, [], clientes_map)

        for a in NUEVOS_AGENTES:
            crear_usuario_con_perfil(db, tenant, a, rol_agente.id_rol, Agente, [], agentes_map)

        clientes = list(clientes_map.values())
        agentes = list(agentes_map.values())
        print(f"[+] {len(clientes)} clientes y {len(agentes)} agentes disponibles para el historial.")

        # 2. VISITAS HISTORICAS (varias por propiedad, distribuidas en el rango)
        print("\n[2] Generando visitas historicas...")
        total_visitas = 0
        visitas_por_propiedad = {}

        for prop in propiedades:
            num_visitas = random.randint(4, 9)
            visitas_prop = []
            for _ in range(num_visitas):
                fecha_visita = fecha_aleatoria_en_rango(FECHA_INICIO_HISTORIAL, HOY)
                # Estado segun que tan en el pasado quedo la visita
                if fecha_visita >= HOY - timedelta(days=3):
                    estado = "Programada"
                else:
                    estado = random.choices(
                        ["Realizada", "Cancelada", "No Asistio"],
                        weights=[0.7, 0.2, 0.1]
                    )[0]

                visita = Visita(
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
                        "Cliente referido por otro cliente actual."
                    ]),
                    estado=estado
                )
                db.add(visita)
                visitas_prop.append((visita, fecha_visita))
                total_visitas += 1
            visitas_por_propiedad[prop.id_propiedad] = visitas_prop

        db.commit()
        print(f"[+] {total_visitas} visitas historicas creadas.")

        # 3. CONTRATOS HISTORICOS (algunas propiedades se "concretan")
        print("\n[3] Generando contratos y pagos historicos...")
        # Elegimos un subconjunto de propiedades para que tengan contrato,
        # dejando el resto solo con visitas (inventario aun disponible).
        propiedades_con_contrato = random.sample(propiedades, k=max(1, len(propiedades) - 2))

        total_contratos = 0
        total_pagos = 0

        for prop in propiedades_con_contrato:
            # Fecha de inicio del contrato: en algun punto de los primeros 2/3 del rango,
            # para dejar espacio a pagos posteriores.
            limite_inicio = FECHA_INICIO_HISTORIAL + timedelta(days=int(MESES_HISTORIAL * 30 * 0.66))
            fecha_inicio_contrato = fecha_aleatoria_en_rango(FECHA_INICIO_HISTORIAL, limite_inicio)

            cliente = random.choice(clientes)
            agente = random.choice(agentes)

            if prop.tipo_operacion == "Venta":
                tipo_contrato = "Venta Definitiva"
                # Contrato de venta a 90-180 dias
                fecha_fin_contrato = fecha_inicio_contrato + timedelta(days=random.choice([90, 120, 180]))
                monto_total = prop.precio
            elif prop.tipo_operacion == "Alquiler":
                tipo_contrato = "Contrato de Alquiler"
                fecha_fin_contrato = fecha_inicio_contrato + timedelta(days=365)  # contrato anual tipico
                monto_total = prop.precio  # monto mensual de referencia
            else:  # Anticretico
                tipo_contrato = "Contrato Anticretico"
                fecha_fin_contrato = fecha_inicio_contrato + timedelta(days=730)  # anticretico tipico 2 anios
                monto_total = prop.precio

            contrato = Contrato(
                id_cliente=cliente.id_cliente,
                id_propiedad=prop.id_propiedad,
                id_agente=agente.id_agente,
                id_tenant=tenant.id_tenant,
                tipo_contrato=tipo_contrato,
                monto_total=monto_total,
                fecha_inicio=fecha_inicio_contrato,
                fecha_fin=fecha_fin_contrato
            )
            db.add(contrato)
            db.commit()
            db.refresh(contrato)
            total_contratos += 1

            # Actualizamos el estado de la propiedad segun el tipo de operacion
            if prop.tipo_operacion == "Venta":
                prop.estado = "Vendida"
            else:
                prop.estado = "Alquilada"
            db.add(prop)

            # PAGOS asociados, escalonados en el tiempo
            if prop.tipo_operacion == "Venta":
                # Pago inicial (30%) + 2-3 cuotas hasta hoy o fecha_fin (lo que sea antes)
                inicial = (monto_total * Decimal("0.30")).quantize(Decimal("0.01"))
                pago_inicial = Pago(
                    id_contrato=contrato.id_contrato,
                    monto=inicial,
                    fecha_pago=datetime.combine(fecha_inicio_contrato, datetime.min.time()),
                    metodo_pago="Transferencia Bancaria",
                    numero_recibo=f"REC-{contrato.id_contrato:05d}-01"
                )
                db.add(pago_inicial)
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
                    pago_cuota = Pago(
                        id_contrato=contrato.id_contrato,
                        monto=monto_cuota,
                        fecha_pago=datetime.combine(fecha_cuota, datetime.min.time()),
                        metodo_pago=random.choice(["Transferencia Bancaria", "Deposito", "Cheque"]),
                        numero_recibo=f"REC-{contrato.id_contrato:05d}-{i+1:02d}"
                    )
                    db.add(pago_cuota)
                    total_pagos += 1

            else:
                # Alquiler / Anticretico: pagos periodicos (mensuales) desde fecha_inicio hasta hoy
                fecha_pago_actual = fecha_inicio_contrato
                contador = 1
                while fecha_pago_actual <= HOY and fecha_pago_actual <= fecha_fin_contrato:
                    monto_periodo = monto_total if prop.tipo_operacion == "Alquiler" else (
                        monto_total if contador == 1 else Decimal("0.00")
                    )
                    # Para anticretico, el monto grande se paga una sola vez al inicio;
                    # los periodos siguientes no generan nuevo pago (es un deposito, no renta).
                    if prop.tipo_operacion == "Anticretico" and contador > 1:
                        break

                    pago_periodo = Pago(
                        id_contrato=contrato.id_contrato,
                        monto=monto_periodo,
                        fecha_pago=datetime.combine(fecha_pago_actual, datetime.min.time()),
                        metodo_pago=random.choice(["Transferencia Bancaria", "Deposito", "Efectivo"]),
                        numero_recibo=f"REC-{contrato.id_contrato:05d}-{contador:02d}"
                    )
                    db.add(pago_periodo)
                    total_pagos += 1
                    fecha_pago_actual += timedelta(days=30)
                    contador += 1

            db.commit()

        print(f"[+] {total_contratos} contratos y {total_pagos} pagos historicos creados.")
        print(f"[i] {len(propiedades) - len(propiedades_con_contrato)} propiedad(es) quedaron 'Disponible' (solo con visitas).")

        # 4. BITACORA: registrar las acciones principales con su fecha real
        print("\n[4] Registrando bitacora de auditoria historica...")
        admin = db.query(Usuario).filter(
            Usuario.correo == "admin@raices.com", Usuario.id_tenant == tenant.id_tenant
        ).first()

        acciones_bitacora = [
            (FECHA_INICIO_HISTORIAL, "Inicio de registro de actividad comercial del periodo"),
            (FECHA_INICIO_HISTORIAL + timedelta(days=30), "Revision mensual de cartera de propiedades"),
            (FECHA_INICIO_HISTORIAL + timedelta(days=60), "Revision mensual de cartera de propiedades"),
            (FECHA_INICIO_HISTORIAL + timedelta(days=90), "Revision mensual de cartera de propiedades"),
            (HOY, "Poblado de historial de actividad para pruebas de reportes"),
        ]
        for fecha_accion, descripcion in acciones_bitacora:
            bitacora = Bitacora(
                id_usuario=admin.id,
                id_tenant=tenant.id_tenant,
                accion=descripcion,
                fecha_hora=datetime.combine(fecha_accion, datetime.min.time())
            )
            db.add(bitacora)
        db.commit()
        print(f"[+] {len(acciones_bitacora)} entradas de bitacora registradas.")

    print("\n" + "=" * 60)
    print("[*] HISTORIAL DE ACTIVIDAD POBLADO EXITOSAMENTE")
    print("=" * 60)
    print(f"\nPeriodo simulado: {FECHA_INICIO_HISTORIAL} al {HOY} ({MESES_HISTORIAL} meses)")
    print("Listo para probar reportes y dashboards con datos historicos.\n")


if __name__ == "__main__":
    poblar_historial()