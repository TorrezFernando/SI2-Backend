"""Dataset del tenant: Inmobiliaria Sunrise (La Paz)."""

TENANT = {
    "nombre": "Inmobiliaria Sunrise",
    "slug": "sunrise",
    "plan": "basico",
    "max_propiedades": 30,
}

USUARIOS = [
    {"ci": "1100001", "nombre": "Admin Sunrise", "correo": "admin@sunrise.com",
     "telefono": "71100001", "rol": "Administrador", "password": "Admin.123@"},
    {"ci": "1100002", "nombre": "Elena Vargas", "correo": "agente@sunrise.com",
     "telefono": "71100002", "rol": "Agente", "password": "Password.123@"},
    {"ci": "1100003", "nombre": "Marco Quispe", "correo": "propietario@sunrise.com",
     "telefono": "71100003", "rol": "Propietario", "password": "Password.123@"},
    {"ci": "1100004", "nombre": "Rosa Mamani", "correo": "cliente@sunrise.com",
     "telefono": "71100004", "rol": "Cliente", "password": "Password.123@"},
]

PROPIETARIO_CORREO = "propietario@sunrise.com"
AGENTE_CORREO = "agente@sunrise.com"

PROPIEDADES = [
    {
        "titulo": "Departamento con Vista al Illimani",
        "tipo_inmueble": "Departamento", "zona": "Sopocachi",
        "direccion": "Av. 20 de Octubre, Sopocachi, La Paz",
        "precio": "98000.00", "tipo_operacion": "Venta", "estado": "Disponible",
        "habitaciones": 2, "banos": 2, "superficie_m2": "90.00", "garaje": True, "antiguedad_anios": 5,
        "caracteristicas": [("Vista", "Illimani despejado"), ("Calefaccion", "Si")],
        "imagenes": ["https://images.unsplash.com/photo-1502672023488-70e25813eb80?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Casa en Achumani con Jardín Amplio",
        "tipo_inmueble": "Casa", "zona": "Achumani",
        "direccion": "Calle 15, Achumani, La Paz",
        "precio": "210000.00", "tipo_operacion": "Venta", "estado": "Disponible",
        "habitaciones": 4, "banos": 3, "superficie_m2": "280.00", "garaje": True, "antiguedad_anios": 12,
        "caracteristicas": [("Jardin", "Amplio con arboles frutales")],
        "imagenes": ["https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Oficina Ejecutiva en Zona Central",
        "tipo_inmueble": "Oficina", "zona": "Sopocachi",
        "direccion": "Av. Arce, Zona Central, La Paz",
        "precio": "900.00", "tipo_operacion": "Alquiler", "estado": "Disponible",
        "habitaciones": None, "banos": 1, "superficie_m2": "60.00", "garaje": True, "antiguedad_anios": 6,
        "caracteristicas": [("Divisiones", "2 ambientes")],
        "imagenes": ["https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1000&q=80"],
    },
]