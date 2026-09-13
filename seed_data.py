import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from database.database import engine, Base
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


def poblar_base_de_datos(reset: bool = False):
    print("=" * 60)
    print("[*] INICIANDO POBLADO DE LA BASE DE DATOS - INMOBILIARIA RAICES")
    print("=" * 60)

    try:
        # Probar conexión
        with engine.connect() as conn:
            print("[+] Conexion exitosa a PostgreSQL.")
    except UnicodeDecodeError:
        print("\n[!] ERROR DE CONEXION A POSTGRESQL:")
        print("  PostgreSQL respondio con un error de autenticacion:")
        print("  -> La contrasena para el usuario 'postgres' no coincide, o la base de datos 'raices_db' no existe.")
        print("  -> Configura tu contrasena real en el archivo .env o en database/database.py.")
        sys.exit(1)
    except Exception as e:
        print("\n[!] ERROR DE CONEXION A POSTGRESQL:")
        print("  Verifica tus credenciales en el archivo .env o en database/database.py")
        print("  Asegurate de que el servicio de PostgreSQL este activo y la base de datos exista.")
        print(f"  Detalle: {e}\n")
        sys.exit(1)

    if reset:
        print("\n[!] Modo RESET activado: Eliminando tablas existentes...")
        Base.metadata.drop_all(bind=engine)
        print("[+] Tablas eliminadas.")

    print("\n[*] Creando estructura de tablas si no existen...")
    Base.metadata.create_all(bind=engine)
    print("[+] Estructura de tablas lista.")

    with Session(engine) as db:
        # 1. ROLES
        print("\n[1] Creando Roles del Sistema...")
        roles_def = [
            (1, "Administrador"),
            (2, "Agente"),
            (3, "Cliente"),
            (4, "Propietario")
        ]
        for id_r, nom in roles_def:
            r = db.query(Rol).filter(Rol.id_rol == id_r).first()
            if not r:
                r = Rol(id_rol=id_r, nombre=nom)
                db.add(r)
            else:
                r.nombre = nom
        db.commit()
        print("[+] Roles registrados (Administrador, Agente, Cliente, Propietario).")

        # 2. TENANT (INMOBILIARIA)
        print("\n[2] Creando Inmobiliaria (Tenant)...")
        tenant = db.query(Tenant).filter(Tenant.nombre == "Inmobiliaria Raíces").first()
        if not tenant:
            tenant = Tenant(
                nombre="Inmobiliaria Raíces",
                slug="raices",
                plan="pro",
                max_propiedades=100,
                estado=True,
                fecha_vencimiento_pago=date.today() + timedelta(days=365)
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        print(f"[+] Tenant activo: {tenant.nombre} (ID: {tenant.id_tenant}, Plan: {tenant.plan}).")

        # 3. USUARIOS
        print("\n[3] Creando Usuarios de Prueba...")
        usuarios_data = [
            {
                "ci": "1234567",
                "nombre": "Admin Raíces",
                "correo": "admin@raices.com",
                "telefono": "77712345",
                "id_rol": 1,
                "password": "Admin.123@"
            },
            {
                "ci": "2000000",
                "nombre": "Ana Agente",
                "correo": "agente@raices.com",
                "telefono": "70000001",
                "id_rol": 2,
                "password": "Password.123@"
            },
            {
                "ci": "3000000",
                "nombre": "Pablo Propietario",
                "correo": "propietario@raices.com",
                "telefono": "70000002",
                "id_rol": 4,
                "password": "Password.123@"
            },
            {
                "ci": "4000000",
                "nombre": "Carlos Cliente",
                "correo": "cliente@raices.com",
                "telefono": "70000003",
                "id_rol": 3,
                "password": "Password.123@"
            },
            # Usuario admin adicional para compatibilidad con scripts existentes
            {
                "ci": "123456",
                "nombre": "Admin Premium",
                "correo": "admin@premium.com",
                "telefono": "70011223",
                "id_rol": 1,
                "password": "Admin123!"
            }
        ]

        usuarios_creados = {}
        for u_data in usuarios_data:
            user = db.query(Usuario).filter(
                Usuario.correo == u_data["correo"],
                Usuario.id_tenant == tenant.id_tenant
            ).first()
            if not user:
                user = Usuario(
                    ci=u_data["ci"],
                    nombre=u_data["nombre"],
                    correo=u_data["correo"],
                    telefono=u_data["telefono"],
                    id_rol=u_data["id_rol"],
                    id_tenant=tenant.id_tenant,
                    password_hash=get_password_hash(u_data["password"])
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                user.id_rol = u_data["id_rol"]
                db.commit()
            usuarios_creados[u_data["correo"]] = user
        print("[+] Usuarios registrados con contraseñas encriptadas (bcrypt).")

        # 4. PERFILES (Agente, Propietario, Cliente)
        print("\n[4] Vinculando Perfiles Especializados...")

        usuario_agente = usuarios_creados["agente@raices.com"]
        usuario_propietario = usuarios_creados["propietario@raices.com"]
        usuario_cliente = usuarios_creados["cliente@raices.com"]

        agente = db.query(Agente).filter(Agente.id_usuario == usuario_agente.id).first()
        if not agente:
            agente = Agente(id_usuario=usuario_agente.id)
            db.add(agente)
            db.commit()
            db.refresh(agente)

        propietario = db.query(Propietario).filter(Propietario.id_usuario == usuario_propietario.id).first()
        if not propietario:
            propietario = Propietario(id_usuario=usuario_propietario.id)
            db.add(propietario)
            db.commit()
            db.refresh(propietario)

        cliente = db.query(Cliente).filter(Cliente.id_usuario == usuario_cliente.id).first()
        if not cliente:
            cliente = Cliente(id_usuario=usuario_cliente.id)
            db.add(cliente)
            db.commit()
            db.refresh(cliente)
        print("[+] Perfiles de Agente, Propietario y Cliente creados.")

        # 4.5 CATALOGOS: TIPOS DE INMUEBLE Y ZONAS
        print("\n[4.5] Creando Catalogos (Tipos de Inmueble y Zonas)...")

        tipos_inmueble_nombres = ["Departamento", "Casa", "Oficina", "Terreno"]
        tipos_inmueble = {}
        for nom in tipos_inmueble_nombres:
            t = db.query(TipoInmueble).filter(TipoInmueble.nombre == nom).first()
            if not t:
                t = TipoInmueble(nombre=nom)
                db.add(t)
                db.commit()
                db.refresh(t)
            tipos_inmueble[nom] = t

        zonas_nombres = ["Equipetrol", "Las Palmas", "Sirari", "Zona Norte", "Segundo Anillo"]
        zonas = {}
        for nom in zonas_nombres:
            z = db.query(Zona).filter(Zona.nombre == nom).first()
            if not z:
                z = Zona(nombre=nom)
                db.add(z)
                db.commit()
                db.refresh(z)
            zonas[nom] = z

        print(f"[+] {len(tipos_inmueble)} tipos de inmueble y {len(zonas)} zonas creadas.")

        # 5. PROPIEDADES
        print("\n[5] Creando Inmuebles y Propiedades de Demostracion...")
        propiedades_data = [
            {
                "titulo": "Departamento de Lujo en Equipetrol",
                "tipo_inmueble": "Departamento",
                "zona": "Equipetrol",
                "direccion": "Av. San Martín, Edificio SkyTower Piso 8, Equipetrol, Santa Cruz",
                "precio": Decimal("145000.00"),
                "tipo_operacion": "Venta",
                "estado": "Disponible",
                "habitaciones": 3,
                "banos": 2,
                "superficie_m2": Decimal("125.00"),
                "garaje": True,
                "antiguedad_anios": 2,
                "caracteristicas": [
                    ("Vista", "Panorámica ciudad"),
                    ("Amoblado", "Parcial"),
                    ("Piscina y Churrasquera", "Áreas comunes")
                ],
                "imagenes": [
                    "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1000&q=80",
                    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1000&q=80"
                ]
            },
            {
                "titulo": "Casa Familiar con Jardín y Piscina",
                "tipo_inmueble": "Casa",
                "zona": "Las Palmas",
                "direccion": "Barrio Las Palmas, Calle Los Tajibos #45, Santa Cruz",
                "precio": Decimal("285000.00"),
                "tipo_operacion": "Venta",
                "estado": "Disponible",
                "habitaciones": 4,
                "banos": 5,
                "superficie_m2": Decimal("320.00"),
                "garaje": True,
                "antiguedad_anios": 8,
                "caracteristicas": [
                    ("Superficie Terreno", "450 m²"),
                    ("Piscina privada", "Sí")
                ],
                "imagenes": [
                    "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1000&q=80",
                    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1000&q=80"
                ]
            },
            {
                "titulo": "Monoambiente Amoblado de Estilo Moderno",
                "tipo_inmueble": "Departamento",
                "zona": "Sirari",
                "direccion": "Sirari, Calle Los Gomeros #120, Piso 3",
                "precio": Decimal("480.00"),
                "tipo_operacion": "Alquiler",
                "estado": "Disponible",
                "habitaciones": 1,
                "banos": 1,
                "superficie_m2": Decimal("45.00"),
                "garaje": False,
                "antiguedad_anios": 3,
                "caracteristicas": [
                    ("Amoblado", "Completamente equipado"),
                    ("Servicios incluidos", "Internet y Expensas")
                ],
                "imagenes": [
                    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1000&q=80"
                ]
            },
            {
                "titulo": "Casa en Condominio Cerrado con Seguridad 24/7",
                "tipo_inmueble": "Casa",
                "zona": "Zona Norte",
                "direccion": "Zona Norte Km 9, Condominio Sevilla Los Jardines",
                "precio": Decimal("38000.00"),
                "tipo_operacion": "Anticretico",
                "estado": "Disponible",
                "habitaciones": 3,
                "banos": 3,
                "superficie_m2": Decimal("250.00"),
                "garaje": True,
                "antiguedad_anios": 5,
                "caracteristicas": [
                    ("Club House", "Canchas y piscinas")
                ],
                "imagenes": [
                    "https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1000&q=80"
                ]
            },
            {
                "titulo": "Oficina Corporativa en Torre Empresarial",
                "tipo_inmueble": "Oficina",
                "zona": "Segundo Anillo",
                "direccion": "Av. Cristóbal de Mendoza, 2do Anillo, Torre Dúo",
                "precio": Decimal("1200.00"),
                "tipo_operacion": "Alquiler",
                "estado": "Disponible",
                "habitaciones": None,
                "banos": 2,
                "superficie_m2": Decimal("85.00"),
                "garaje": True,
                "antiguedad_anios": 4,
                "caracteristicas": [
                    ("Divisiones", "3 ambientes + recepción")
                ],
                "imagenes": [
                    "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1000&q=80"
                ]
            }
        ]

        for p_data in propiedades_data:
            prop = db.query(Propiedad).filter(
                Propiedad.titulo == p_data["titulo"],
                Propiedad.id_tenant == tenant.id_tenant
            ).first()

            if not prop:
                prop = Propiedad(
                    titulo=p_data["titulo"],
                    direccion=p_data["direccion"],
                    precio=p_data["precio"],
                    tipo_operacion=p_data["tipo_operacion"],
                    estado=p_data["estado"],
                    habitaciones=p_data["habitaciones"],
                    banos=p_data["banos"],
                    superficie_m2=p_data["superficie_m2"],
                    garaje=p_data["garaje"],
                    antiguedad_anios=p_data["antiguedad_anios"],
                    id_propietario=propietario.id_propietario,
                    id_agente=agente.id_agente,
                    id_tipo_inmueble=tipos_inmueble[p_data["tipo_inmueble"]].id_tipo_inmueble,
                    id_zona=zonas[p_data["zona"]].id_zona,
                    id_tenant=tenant.id_tenant
                )
                db.add(prop)
                db.commit()
                db.refresh(prop)

                # Características
                for nom_c, val_c in p_data["caracteristicas"]:
                    caract = Caracteristica(
                        id_propiedad=prop.id_propiedad,
                        nombre=nom_c,
                        valor=val_c
                    )
                    db.add(caract)

                # Imágenes
                for url_img in p_data["imagenes"]:
                    img = Imagen(
                        id_propiedad=prop.id_propiedad,
                        url=url_img
                    )
                    db.add(img)

                db.commit()

        print(f"[+] {len(propiedades_data)} Propiedades creadas con caracteristicas e imagenes.")

        # 6. VISITAS Y CONTRATOS
        print("\n[6] Creando Visitas y Contratos de Muestra...")
        primera_prop = db.query(Propiedad).filter(Propiedad.id_tenant == tenant.id_tenant).first()
        if primera_prop:
            visita = db.query(Visita).filter(Visita.id_propiedad == primera_prop.id_propiedad).first()
            if not visita:
                visita = Visita(
                    id_cliente=cliente.id_cliente,
                    id_propiedad=primera_prop.id_propiedad,
                    id_agente=agente.id_agente,
                    id_tenant=tenant.id_tenant,
                    fecha_hora=datetime.now() + timedelta(days=2, hours=4),
                    comentario="Cliente interesado en conocer las areas comunes y formas de financiamiento.",
                    estado="Programada"
                )
                db.add(visita)

            contrato = db.query(Contrato).filter(Contrato.id_propiedad == primera_prop.id_propiedad).first()
            if not contrato:
                contrato = Contrato(
                    id_cliente=cliente.id_cliente,
                    id_propiedad=primera_prop.id_propiedad,
                    id_agente=agente.id_agente,
                    id_tenant=tenant.id_tenant,
                    tipo_contrato="Reserva de Venta",
                    monto_total=primera_prop.precio,
                    fecha_inicio=date.today(),
                    fecha_fin=date.today() + timedelta(days=90)
                )
                db.add(contrato)
                db.commit()
                db.refresh(contrato)

                pago = Pago(
                    id_contrato=contrato.id_contrato,
                    monto=Decimal("5000.00"),
                    metodo_pago="Transferencia Bancaria",
                    numero_recibo="REC-00129"
                )
                db.add(pago)

            # Bitacora
            usuario_admin = usuarios_creados["admin@raices.com"]
            bitacora = Bitacora(
                id_usuario=usuario_admin.id,
                id_tenant=tenant.id_tenant,
                accion="Poblado inicial de base de datos con datos de demostracion"
            )
            db.add(bitacora)
            db.commit()
            print("[+] Visita, contrato, pago y bitacora de ejemplo registrados.")

        # Guardamos estos valores ANTES de salir del bloque `with Session(...)`,
        # porque una vez cerrada la sesion, el objeto `tenant` queda "detached"
        # y ya no se pueden leer sus atributos sin relanzar una consulta.
        tenant_nombre_final = tenant.nombre
        tenant_slug_final = tenant.slug

    print("\n" + "=" * 60)
    print("[*] BASE DE DATOS POBLADA EXITOSAMENTE")
    print("=" * 60)
    print("\nCredenciales de prueba disponibles:")
    print("+---------------------+-------------------------+---------------+-------------+")
    print("| Rol                 | Correo                  | Contrasena    | CI          |")
    print("+---------------------+-------------------------+---------------+-------------+")
    print("| Administrador       | admin@raices.com        | Admin.123@    | 1234567     |")
    print("| Agente Inmobiliario | agente@raices.com       | Password.123@ | 2000000     |")
    print("| Propietario         | propietario@raices.com  | Password.123@ | 3000000     |")
    print("| Cliente             | cliente@raices.com      | Password.123@ | 4000000     |")
    print("+---------------------+-------------------------+---------------+-------------+")
    print(f"Inmobiliaria (Tenant): {tenant_nombre_final} (slug: {tenant_slug_final})\n")


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    poblar_base_de_datos(reset=reset_flag)