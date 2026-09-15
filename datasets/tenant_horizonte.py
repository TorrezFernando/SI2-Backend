"""Dataset del tenant: Inmobiliaria Horizonte (Tarija)."""

TENANT = {
    "nombre": "Inmobiliaria Horizonte",
    "slug": "horizonte",
    "plan": "basico",
    "max_propiedades": 30,
}

USUARIOS = [
    {"ci": "4400001", "nombre": "Admin Horizonte", "correo": "admin@horizonte.com",
     "telefono": "74400001", "rol": "Administrador", "password": "Admin.123@"},
    {"ci": "4400002", "nombre": "Beatriz Cardozo", "correo": "agente@horizonte.com",
     "telefono": "74400002", "rol": "Agente", "password": "Password.123@"},
    {"ci": "4400003", "nombre": "Oscar Trigo", "correo": "propietario@horizonte.com",
     "telefono": "74400003", "rol": "Propietario", "password": "Password.123@"},
    {"ci": "4400004", "nombre": "Sandra Vaca", "correo": "cliente@horizonte.com",
     "telefono": "74400004", "rol": "Cliente", "password": "Password.123@"},
]

PROPIETARIO_CORREO = "propietario@horizonte.com"
AGENTE_CORREO = "agente@horizonte.com"

PROPIEDADES = [
    {
        "titulo": "Casa de Campo con Viñedo",
        "tipo_inmueble": "Casa", "zona": "Valle de la Concepción",
        "direccion": "Ruta al Valle, Valle de la Concepción, Tarija",
        "precio": "165000.00", "tipo_operacion": "Venta", "estado": "Disponible",
        "habitaciones": 3, "banos": 2, "superficie_m2": "300.00", "garaje": True, "antiguedad_anios": 15,
        "caracteristicas": [("Vinedo", "0.5 hectareas")],
        "imagenes": ["https://images.unsplash.com/photo-1449844908441-8829872d2607?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Departamento Céntrico Recién Construido",
        "tipo_inmueble": "Departamento", "zona": "Centro Tarija",
        "direccion": "Calle Sucre, Centro, Tarija",
        "precio": "72000.00", "tipo_operacion": "Venta", "estado": "Disponible",
        "habitaciones": 2, "banos": 1, "superficie_m2": "65.00", "garaje": True, "antiguedad_anios": 1,
        "caracteristicas": [("Estado", "A estrenar")],
        "imagenes": ["https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Terreno Agrícola en las Afueras",
        "tipo_inmueble": "Terreno", "zona": "Valle de la Concepción",
        "direccion": "Camino Rural, Valle de la Concepción, Tarija",
        "precio": "40000.00", "tipo_operacion": "Venta", "estado": "Disponible",
        "habitaciones": None, "banos": None, "superficie_m2": "1000.00", "garaje": False, "antiguedad_anios": None,
        "caracteristicas": [("Uso de suelo", "Agricola")],
        "imagenes": ["https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1000&q=80"],
    },
]