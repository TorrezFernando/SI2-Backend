"""Dataset del tenant: Inmobiliaria Raices (Santa Cruz)."""

TENANT = {
    "nombre": "Inmobiliaria Raíces",
    "slug": "raices",
    "plan": "pro",
    "max_propiedades": 100,
}

USUARIOS = [
    {"ci": "1234567", "nombre": "Admin Raíces", "correo": "admin@raices.com",
     "telefono": "77712345", "rol": "Administrador", "password": "Admin.123@"},
    {"ci": "2000000", "nombre": "Ana Agente", "correo": "agente@raices.com",
     "telefono": "70000001", "rol": "Agente", "password": "Password.123@"},
    {"ci": "3000000", "nombre": "Pablo Propietario", "correo": "propietario@raices.com",
     "telefono": "70000002", "rol": "Propietario", "password": "Password.123@"},
    {"ci": "4000000", "nombre": "Carlos Cliente", "correo": "cliente@raices.com",
     "telefono": "70000003", "rol": "Cliente", "password": "Password.123@"},
]

# correo del usuario que actua como propietario/agente por defecto para las propiedades
PROPIETARIO_CORREO = "propietario@raices.com"
AGENTE_CORREO = "agente@raices.com"

PROPIEDADES = [
    {
        "titulo": "Departamento de Lujo en Equipetrol",
        "tipo_inmueble": "Departamento", "zona": "Equipetrol",
        "direccion": "Av. San Martín, Edificio SkyTower Piso 8, Santa Cruz",
        "precio": "145000.00", "tipo_operacion": "Venta", "estado": "Disponible",
        "habitaciones": 3, "banos": 2, "superficie_m2": "125.00", "garaje": True, "antiguedad_anios": 2,
        "caracteristicas": [("Vista", "Panorámica ciudad"), ("Piscina y Churrasquera", "Áreas comunes")],
        "imagenes": ["https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Casa Familiar con Jardín y Piscina",
        "tipo_inmueble": "Casa", "zona": "Las Palmas",
        "direccion": "Barrio Las Palmas, Calle Los Tajibos #45, Santa Cruz",
        "precio": "285000.00", "tipo_operacion": "Venta", "estado": "Disponible",
        "habitaciones": 4, "banos": 5, "superficie_m2": "320.00", "garaje": True, "antiguedad_anios": 8,
        "caracteristicas": [("Superficie Terreno", "450 m²"), ("Piscina privada", "Sí")],
        "imagenes": ["https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Monoambiente Amoblado de Estilo Moderno",
        "tipo_inmueble": "Departamento", "zona": "Sirari",
        "direccion": "Sirari, Calle Los Gomeros #120, Piso 3, Santa Cruz",
        "precio": "480.00", "tipo_operacion": "Alquiler", "estado": "Disponible",
        "habitaciones": 1, "banos": 1, "superficie_m2": "45.00", "garaje": False, "antiguedad_anios": 3,
        "caracteristicas": [("Amoblado", "Completamente equipado")],
        "imagenes": ["https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1000&q=80"],
    },
]