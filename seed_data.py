import sys
from decimal import Decimal
from sqlalchemy.orm import Session

from database.database import engine, Base
import database.models  # Registra todos los modelos modulares
from modulo_administracion_configuracion.models import Tenant
from gestion_usuarios.models import Rol, Usuario
from modulo_inmuebles.models import (
    Propietario, Agente, Cliente, Propiedad, Imagen,
    Caracteristica, TipoInmueble, Zona
)
from auth import get_password_hash

from datasets import (
    tenant_raices, tenant_sunrise, tenant_delsur, tenant_metropoli, tenant_horizonte
)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Lista de datasets a procesar. Agregar un tenant nuevo es tan simple como
# crear su archivo en datasets/ e incluirlo aqui.
DATASETS = [tenant_raices, tenant_sunrise, tenant_delsur, tenant_metropoli, tenant_horizonte]

ROLES_GLOBALES = ["Administrador", "Agente", "Cliente", "Propietario"]

PERFIL_POR_ROL = {
    "Agente": Agente,
    "Propietario": Propietario,
    "Cliente": Cliente,
    # "Administrador" no tiene tabla de perfil especializado
}


def crear_roles(db: Session):
    print("\n[1] Creando Roles del Sistema (globales)...")
    roles_map = {}
    for nombre in ROLES_GLOBALES:
        rol = db.query(Rol).filter(Rol.nombre == nombre).first()
        if not rol:
            rol = Rol(nombre=nombre)
            db.add(rol)
            db.commit()
            db.refresh(rol)
        roles_map[nombre] = rol
    print(f"[+] {len(roles_map)} roles listos: {', '.join(roles_map.keys())}")
    return roles_map


def crear_catalogos_base(db: Session):
    """Catalogos globales minimos que deben existir antes de crear propiedades.
    Cada dataset puede referenciar tipos/zonas nuevas; se crean sobre la marcha
    en crear_propiedades() si no existen todavia."""
    print("\n[2] Verificando catalogos globales (Tipo de Inmueble y Zona)...")
    tipos_base = ["Departamento", "Casa", "Oficina", "Terreno"]
    for nombre in tipos_base:
        if not db.query(TipoInmueble).filter(TipoInmueble.nombre == nombre).first():
            db.add(TipoInmueble(nombre=nombre))
    db.commit()
    print("[+] Catalogo base de tipos de inmueble listo.")


def obtener_o_crear_tipo_inmueble(db: Session, nombre: str) -> TipoInmueble:
    tipo = db.query(TipoInmueble).filter(TipoInmueble.nombre == nombre).first()
    if not tipo:
        tipo = TipoInmueble(nombre=nombre)
        db.add(tipo)
        db.commit()
        db.refresh(tipo)
    return tipo


def obtener_o_crear_zona(db: Session, nombre: str) -> Zona:
    zona = db.query(Zona).filter(Zona.nombre == nombre).first()
    if not zona:
        zona = Zona(nombre=nombre)
        db.add(zona)
        db.commit()
        db.refresh(zona)
    return zona


def crear_tenant(db: Session, datos_tenant: dict) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.slug == datos_tenant["slug"]).first()
    if not tenant:
        tenant = Tenant(
            nombre=datos_tenant["nombre"],
            slug=datos_tenant["slug"],
            plan=datos_tenant["plan"],
            max_propiedades=datos_tenant["max_propiedades"],
            estado=True,
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant


def crear_usuarios_y_perfiles(db: Session, tenant: Tenant, usuarios_data: list, roles_map: dict) -> dict:
    """Crea los usuarios de un tenant y su perfil especializado.
    Devuelve un dict {correo: perfil_o_usuario} para uso posterior."""
    perfiles_por_correo = {}
    for u in usuarios_data:
        rol = roles_map[u["rol"]]
        usuario = db.query(Usuario).filter(
            Usuario.correo == u["correo"], Usuario.id_tenant == tenant.id_tenant
        ).first()
        if not usuario:
            usuario = Usuario(
                ci=u["ci"],
                nombre=u["nombre"],
                correo=u["correo"],
                telefono=u["telefono"],
                id_rol=rol.id_rol,
                id_tenant=tenant.id_tenant,
                password_hash=get_password_hash(u["password"]),
            )
            db.add(usuario)
            db.commit()
            db.refresh(usuario)

        ModeloPerfil = PERFIL_POR_ROL.get(u["rol"])
        if ModeloPerfil:
            perfil = db.query(ModeloPerfil).filter(ModeloPerfil.id_usuario == usuario.id).first()
            if not perfil:
                perfil = ModeloPerfil(id_usuario=usuario.id)
                db.add(perfil)
                db.commit()
                db.refresh(perfil)
            perfiles_por_correo[u["correo"]] = perfil
        else:
            perfiles_por_correo[u["correo"]] = usuario

    return perfiles_por_correo


def crear_propiedades(db: Session, tenant: Tenant, propiedades_data: list,
                       propietario: Propietario, agente: Agente):
    creadas = 0
    for p in propiedades_data:
        existente = db.query(Propiedad).filter(
            Propiedad.titulo == p["titulo"], Propiedad.id_tenant == tenant.id_tenant
        ).first()
        if existente:
            continue

        tipo_inmueble = obtener_o_crear_tipo_inmueble(db, p["tipo_inmueble"])
        zona = obtener_o_crear_zona(db, p["zona"])

        prop = Propiedad(
            titulo=p["titulo"],
            direccion=p["direccion"],
            precio=Decimal(p["precio"]),
            tipo_operacion=p["tipo_operacion"],
            estado=p["estado"],
            habitaciones=p["habitaciones"],
            banos=p["banos"],
            superficie_m2=Decimal(p["superficie_m2"]) if p["superficie_m2"] is not None else None,
            garaje=p["garaje"],
            antiguedad_anios=p["antiguedad_anios"],
            id_propietario=propietario.id_propietario,
            id_agente=agente.id_agente,
            id_tipo_inmueble=tipo_inmueble.id_tipo_inmueble,
            id_zona=zona.id_zona,
            id_tenant=tenant.id_tenant,
        )
        db.add(prop)
        db.commit()
        db.refresh(prop)

        for nombre_c, valor_c in p["caracteristicas"]:
            db.add(Caracteristica(id_propiedad=prop.id_propiedad, nombre=nombre_c, valor=valor_c))

        for url_img in p["imagenes"]:
            db.add(Imagen(id_propiedad=prop.id_propiedad, url=url_img))

        db.commit()
        creadas += 1

    return creadas


def poblar_base_de_datos(reset: bool = False):
    print("=" * 60)
    print("[*] INICIANDO POBLADO MULTI-TENANT (5 INMOBILIARIAS)")
    print("=" * 60)

    try:
        with engine.connect():
            print("[+] Conexion exitosa a PostgreSQL.")
    except Exception as e:
        print("\n[!] ERROR DE CONEXION A POSTGRESQL:")
        print("  Verifica tus credenciales en el archivo .env")
        print(f"  Detalle: {e}\n")
        sys.exit(1)

    if reset:
        print("\n[!] Modo RESET activado: Eliminando tablas existentes...")
        Base.metadata.drop_all(bind=engine)
        print("[+] Tablas eliminadas.")

    print("\n[*] Creando estructura de tablas si no existen...")
    Base.metadata.create_all(bind=engine)
    print("[+] Estructura de tablas lista.")

    resumen_credenciales = []

    with Session(engine) as db:
        roles_map = crear_roles(db)
        crear_catalogos_base(db)

        for dataset in DATASETS:
            print(f"\n{'=' * 60}")
            print(f"[*] Procesando tenant: {dataset.TENANT['nombre']} (slug: {dataset.TENANT['slug']})")
            print("=" * 60)

            tenant = crear_tenant(db, dataset.TENANT)
            print(f"[+] Tenant listo (ID: {tenant.id_tenant}).")

            perfiles = crear_usuarios_y_perfiles(db, tenant, dataset.USUARIOS, roles_map)
            print(f"[+] {len(dataset.USUARIOS)} usuarios y perfiles listos.")

            propietario = perfiles[dataset.PROPIETARIO_CORREO]
            agente = perfiles[dataset.AGENTE_CORREO]

            num_creadas = crear_propiedades(db, tenant, dataset.PROPIEDADES, propietario, agente)
            print(f"[+] {num_creadas} propiedades nuevas creadas (de {len(dataset.PROPIEDADES)} en el dataset).")

            for u in dataset.USUARIOS:
                resumen_credenciales.append((tenant.nombre, u["rol"], u["correo"], u["password"]))

    print("\n" + "=" * 60)
    print("[*] BASE DE DATOS MULTI-TENANT POBLADA EXITOSAMENTE")
    print("=" * 60)
    print("\nCredenciales de prueba disponibles:")
    print(f"{'Tenant':<25}{'Rol':<15}{'Correo':<28}{'Contrasena'}")
    print("-" * 90)
    for tenant_nombre, rol, correo, password in resumen_credenciales:
        print(f"{tenant_nombre:<25}{rol:<15}{correo:<28}{password}")
    print()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    poblar_base_de_datos(reset=reset_flag)