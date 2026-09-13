# Este archivo ahora solo sirve para importar los modelos modulares
# para que SQLAlchemy pueda registrarlos antes de hacer Base.metadata.create_all()

from modulo_administracion_configuracion.models import Tenant
from gestion_usuarios.models import Usuario, Rol
from modulo_inmuebles.models import Bitacora, Propietario, Agente, Cliente, Propiedad, Zona, TipoInmueble, Imagen, Caracteristica, Visita, Contrato, Pago

__all__ = [
    "Tenant", "Usuario", "Rol", "Bitacora", "Propietario", "Agente", 
    "Cliente", "Propiedad", "Zona", "TipoInmueble", "Imagen", "Caracteristica", "Visita", "Contrato", "Pago"
]
