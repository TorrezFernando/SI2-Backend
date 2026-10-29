"""Regresiones de seguridad y CRUD. Solo SQLite en memoria y datos ficticios."""
import asyncio
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = secrets.token_urlsafe(48)
os.environ["GEMINI_API_KEY"] = ""
os.environ["SUPERADMIN_USER_IDS"] = ""
os.environ["ENABLE_SCHEDULER"] = "false"
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool
import database.database as database
database.engine = create_engine("sqlite://",poolclass=StaticPool,connect_args={"check_same_thread":False})
@event.listens_for(database.engine,"connect")
def fk(conn, record):
    conn.execute("PRAGMA foreign_keys=ON")
database.SessionLocal.configure(bind=database.engine)
import main
from database.models import Tenant,Rol,Usuario,Propietario,Agente,Cliente,Propiedad,TipoInmueble,Zona
from auth import user_token,get_password_hash,create_access_token

async def request(method,path,data=None,token=None):
    path,_,query=path.partition("?")
    body=json.dumps(data).encode() if data is not None else b""
    headers=[(b"content-type",b"application/json")]
    if token:
        headers.append((b"authorization",f"Bearer {token}".encode()))
    scope={"type":"http","asgi":{"version":"3.0"},"http_version":"1.1","method":method,
           "scheme":"http","path":path,"raw_path":path.encode(),"query_string":query.encode(),
           "root_path":"","headers":headers,"client":("127.0.0.1",1),"server":("test",80)}
    messages=[]
    async def receive():
        return {"type":"http.request","body":body,"more_body":False}
    async def send(m):
        messages.append(m)
    await main.app(scope,receive,send)
    status=next(m["status"] for m in messages if m["type"]=="http.response.start")
    raw=b"".join(m.get("body",b"") for m in messages)
    return status,json.loads(raw) if raw else None

class Regression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw=get_password_hash("Prueba.123!")

    def setUp(self):
        database.Base.metadata.drop_all(database.engine)
        database.Base.metadata.create_all(database.engine)
        with database.SessionLocal() as db:
            db.add_all([Tenant(id_tenant=i,nombre=f"Empresa {i}",slug=f"empresa-{i}") for i in (1,2)])
            # Cliente = 4 y Propietario = 3 para comprobar que no se confía en IDs fijos.
            db.add_all([Rol(id_rol=i,nombre=n) for i,n in [(1,"Administrador"),(2,"Agente"),(3,"Propietario"),(4,"Cliente")]])
            db.add_all([TipoInmueble(id_tipo_inmueble=1,nombre="Casa"),Zona(id_zona=1,nombre="Centro")])
            db.commit()
            for i,role,tenant in [(1,1,1),(2,2,1),(3,4,1),(4,1,2),(5,3,1),(6,2,2),(7,3,2)]:
                db.add(Usuario(id=i,ci=f"CI{i}",nombre=f"Persona {i}",correo=f"u{i}@example.test",id_rol=role,id_tenant=tenant,password_hash=self.pw))
            db.commit()
            self.tokens={u.id:user_token(u) for u in db.query(Usuario).all()}
            db.add_all([Propietario(id_propietario=1,id_usuario=5),Propietario(id_propietario=2,id_usuario=7),
                        Agente(id_agente=1,id_usuario=2),Agente(id_agente=2,id_usuario=6),Cliente(id_cliente=1,id_usuario=3)])
            db.commit()
            db.add_all([Propiedad(id_propiedad=i,id_propietario=i,id_agente=i,id_tipo_inmueble=1,id_zona=1,
                      titulo=f"Casa {i}",direccion="Ficticia",precio=100000*i,tipo_operacion="Venta",id_tenant=i) for i in (1,2)])
            db.commit()

    def call(self,method,path,data=None,uid=None,expected=200):
        status,result=asyncio.run(request(method,path,data,self.tokens.get(uid)))
        self.assertEqual(status,expected,(path,result))
        return result

    def property_data(self):
        return {"titulo":"Nueva","direccion":"Ficticia","precio":120,"tipo_operacion":"Anticretico",
                "id_propietario":1,"id_agente":1,"id_tipo_inmueble":1,"id_zona":1,"descripcion":"Texto generado " * 30}

    def test_anonymous_and_client_cannot_administer(self):
        self.call("DELETE","/modulo_inmuebles/clientes/1",expected=401)
        self.call("DELETE","/modulo_inmuebles/clientes/1",uid=3,expected=403)
        self.call("POST","/gestion_usuarios/roles",{"nombre":"Administrador"},expected=401)
        self.call("GET","/gestion_usuarios/usuarios",uid=3,expected=403)
        self.call("POST","/api/backup/manual",uid=1,expected=403)

    def test_register_cannot_assign_admin(self):
        data={"ci":"NEW","nombre":"Nuevo","correo":"new@example.test","password":"Prueba.123!","id_tenant":1,"id_rol":1}
        self.call("POST","/gestion_usuarios/auth/register",data,expected=403)
        data["id_rol"]=4
        self.call("POST","/gestion_usuarios/auth/register",data,expected=201)
        with database.SessionLocal() as db:
            self.assertEqual(db.query(Cliente).count(),2)

    def test_cross_tenant_changes_denied(self):
        self.call("PUT","/modulo_inmuebles/propiedades/2/estado",{"estado":"Vendida"},uid=2,expected=404)
        self.call("GET","/modulo_inmuebles/propiedades?id_tenant=2",uid=1,expected=403)
        self.call("DELETE","/modulo_inmuebles/propietarios/2",uid=1,expected=404)
        with database.SessionLocal() as db:
            self.assertEqual(db.get(Propiedad,2).estado,"Disponible")

    def test_create_people_and_duplicate(self):
        for kind in ["clientes","propietarios","agentes"]:
            data={"ci_usuario":"NEW"+kind,"nombre":"Nuevo","correo":kind+"@example.test","password":"Prueba.123!"}
            self.call("POST","/modulo_inmuebles/"+kind,data,uid=1,expected=201)
            self.call("POST","/modulo_inmuebles/"+kind,data,uid=1,expected=409)
        rows=self.call("GET","/modulo_inmuebles/clientes",uid=1)
        self.assertTrue(all("ci_usuario" in x and "telefono" in x for x in rows))

    def test_property_crud_and_description(self):
        data=self.property_data()
        created=self.call("POST","/modulo_inmuebles/propiedades",data,uid=2,expected=201)
        pid=created["id_propiedad"]
        self.assertEqual(created["descripcion"],data["descripcion"])
        data["titulo"]="Editada"
        data["descripcion"]="Otro texto"
        self.call("PUT",f"/modulo_inmuebles/propiedades/{pid}",data,uid=2)
        rows=self.call("GET","/modulo_inmuebles/propiedades",uid=1)
        self.assertEqual(next(x for x in rows if x["id_propiedad"]==pid)["descripcion"],"Otro texto")
        self.call("DELETE",f"/modulo_inmuebles/propiedades/{pid}",uid=2)

    def test_property_validation(self):
        data=self.property_data()
        data["id_agente"]=2
        self.call("POST","/modulo_inmuebles/propiedades",data,uid=1,expected=422)
        data["id_agente"]=1
        data["precio"]=-1
        self.call("POST","/modulo_inmuebles/propiedades",data,uid=1,expected=422)
        self.call("PUT","/modulo_inmuebles/propiedades/1/estado",{"estado":"Alquilada"},uid=1,expected=422)

    def test_catalog_filters(self):
        self.assertEqual(self.call("GET","/modulo_inmuebles/propiedades/catalogo?precio_max=1"),[])
        self.assertEqual(self.call("GET","/modulo_inmuebles/propiedades/catalogo?tipo_operacion=Alquiler"),[])
        rows=self.call("GET","/modulo_inmuebles/propiedades/catalogo?precio_max=150000&tipo_operacion=Venta")
        self.assertEqual([x["id_propiedad"] for x in rows],[1])

    def test_reports_scoped_filtered_and_persisted(self):
        self.call("POST","/reportes/generar",{"entidad":"usuarios"},expected=401)
        self.call("POST","/reportes/generar",{"entidad":"usuarios"},uid=2,expected=403)
        result=self.call("POST","/reportes/generar",{"entidad":"propiedades"},uid=1)
        self.assertEqual([x["id_propiedad"] for x in result["data"]],[1])
        cfg={"entidad":"propiedades","columnas":["titulo"],"filtros":[{"columna":"precio","operador":"lt","valor":1}]}
        self.assertEqual(self.call("POST","/reportes/generar",cfg,uid=1)["data"],[])
        self.call("POST","/reportes/guardados",{"nombre":"Mi reporte","configuracion":json.dumps(cfg)},uid=1,expected=201)
        self.assertEqual(len(self.call("GET","/reportes/guardados",uid=1)),1)
        self.assertEqual(self.call("GET","/reportes/guardados",uid=4),[])
        self.call("POST","/reportes/generar",{"entidad":"usuarios","columnas":["password_hash"]},uid=1,expected=422)

    def test_duplicate_email_requires_tenant_and_resolves_identity(self):
        with database.SessionLocal() as db:
            db.get(Usuario,4).correo="u1@example.test"
            db.commit()
        data={"correo":"u1@example.test","password":"Prueba.123!"}
        self.call("POST","/login",data,expected=401)
        result=self.call("POST","/login",{**data,"id_tenant":2})
        status,me=asyncio.run(request("GET","/auth/me",token=result["access_token"]))
        self.assertEqual(status,200)
        self.assertEqual(me["id"],4)
        self.assertEqual(me["id_tenant"],2)

    def test_password_change_requires_current_and_revokes_token(self):
        self.call("PUT","/gestion_usuarios/users/me/password",{"nueva_password":"Nueva.123!","actual_password":"Incorrecta"},uid=1,expected=400)
        self.call("PUT","/gestion_usuarios/users/me/password",{"nueva_password":"x","actual_password":"Prueba.123!"},uid=1,expected=422)
        self.call("PUT","/gestion_usuarios/users/me/password",{"nueva_password":"Nueva.123!","actual_password":"Prueba.123!"},uid=1)
        self.call("GET","/auth/me",uid=1,expected=401)

    def test_suspended_tenant(self):
        with database.SessionLocal() as db:
            db.get(Tenant,1).estado=False
            db.commit()
        self.call("GET","/auth/me",uid=1,expected=403)
        self.assertEqual([x["id_tenant"] for x in self.call("GET","/modulo_inmuebles/propiedades/catalogo")],[2])

    def test_profile_and_ia_no_fake_success(self):
        me=self.call("GET","/auth/me",uid=2)
        self.assertIn("UI:MENU_PROPIEDADES",me["permisos"])
        self.assertEqual(me["roles"][0]["name"],"Agente")
        payload={"titulo":"Casa","direccion":"Ficticia","precio":100,"tipo_operacion":"Venta"}
        self.call("POST","/api/ia/generar-descripcion",payload,expected=401)
        self.call("POST","/api/ia/generar-descripcion",payload,uid=2,expected=503)
        with patch("ia_router.generate",return_value='{"entidad":"propiedades","columnas":["password_hash"]}'):
            self.call("POST","/api/ia/reporte-voz",{"texto":"venta"},uid=2,expected=422)
        with patch("ia_router.generate",return_value='{"entidad":"propiedades","columnas":["titulo"],"filtros":[]}'):
            self.call("POST","/api/ia/reporte-voz",{"texto":"venta"},uid=2)

    def test_visits_persist_and_reject_overlap(self):
        from datetime import datetime, timedelta, timezone
        fecha=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()
        data={"id_propiedad":1,"fecha_hora":fecha,"comentario":"Prueba"}
        self.call("POST","/modulo_inmuebles/visitas",data,uid=3,expected=201)
        self.call("POST","/modulo_inmuebles/visitas",data,uid=3,expected=409)
        rows=self.call("GET","/modulo_inmuebles/visitas",uid=3)
        self.assertEqual(len(rows),1)
        self.call("POST","/modulo_inmuebles/visitas",{**data,"id_propiedad":2},uid=3,expected=409)

    def test_global_access_requires_explicit_configuration(self):
        self.assertEqual(len(self.call("GET","/admin/empresas",uid=1)),1)
        with patch.dict(os.environ,{"SUPERADMIN_USER_IDS":"1"}):
            self.assertEqual(len(self.call("GET","/admin/empresas",uid=1)),2)
            rows=self.call("GET","/modulo_inmuebles/propiedades?id_tenant=2",uid=1)
            self.assertEqual(rows[0]["id_tenant"],2)

    def test_sqlite_backup_is_readable(self):
        import sqlite3
        import modulo_administracion_configuracion.backup_manager as backup
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/"source.db"
            conn_src = sqlite3.connect(source)
            try:
                conn_src.execute("CREATE TABLE sample(value INTEGER)")
                conn_src.execute("INSERT INTO sample VALUES (7)")
                conn_src.commit()
            finally:
                conn_src.close()
            with patch.object(backup,"SQLALCHEMY_DATABASE_URL","sqlite:///"+source.as_posix()), patch.object(backup,"BACKUP_DIR",Path(temp)/"backups"):
                output=backup.realizar_backup()
                conn_out = sqlite3.connect(output)
                try:
                    self.assertEqual(conn_out.execute("SELECT value FROM sample").fetchone()[0],7)
                finally:
                    conn_out.close()

    def test_missing_contracts_coverage(self):
        # Permisos
        permisos = self.call("GET", "/permisos", uid=1)
        self.assertTrue(len(permisos) > 0)
        self.call("PUT", "/roles/1/permisos", [1, 2], uid=1)

        # Empresas (superadmin only)
        new_emp = {"nombre":"Nueva Inmobiliaria","admin_ci":"CI999","admin_nombre":"Admin Nuevo","admin_correo":"newadmin@example.test"}
        self.call("POST", "/admin/empresas", new_emp, uid=1, expected=403)
        with patch.dict(os.environ, {"SUPERADMIN_USER_IDS":"1"}):
            created_emp = self.call("POST", "/admin/empresas", new_emp, uid=1, expected=201)
            self.assertTrue(created_emp["id_tenant"] > 0)
            self.call("PUT", f"/admin/empresas/{created_emp['id_tenant']}/reset-admin-password", {}, uid=1, expected=200)

        # Recuperación y sesión
        self.call("POST", "/gestion_usuarios/auth/forgot-password", {"correo":"u1@example.test"}, expected=200)
        self.call("POST", "/auth/forgot-password", {"email":"u1@example.test"}, expected=200)
        self.call("POST", "/auth/reset-password", {"token":"secure_token_12345", "new_password":"NewPassword.123!"}, expected=200)
        self.call("POST", "/auth/logout", {"refresh_token":"any"}, expected=200)

if __name__=="__main__":
    unittest.main(verbosity=2)

