"""Dataset del tenant: Inmobiliaria Del Sur (Cochabamba)."""

TENANT = {
    "nombre": "Inmobiliaria Del Sur",
    "slug": "delsur",
    "plan": "basico",
    "max_propiedades": 30,
}

USUARIOS = [
    {"ci": "2200001", "nombre": "Admin Del Sur", "correo": "admin@delsur.com",
     "telefono": "72200001", "rol": "Administrador", "password": "Admin.123@"},
    {"ci": "2200002", "nombre": "Fernando Zambrana", "correo": "agente@delsur.com",
     "telefono": "72200002", "rol": "Agente", "password": "Password.123@"},
    {"ci": "2200003", "nombre": "Gladys Torrico", "correo": "propietario@delsur.com",
     "telefono": "72200003", "rol": "Propietario", "password": "Password.123@"},
    {"ci": "2200004", "nombre": "Hugo Peredo", "correo": "cliente@delsur.com",
     "telefono": "72200004", "rol": "Cliente", "password": "Password.123@"},
]

PROPIETARIO_CORREO = "propietario@delsur.com"
AGENTE_CORREO = "agente@delsur.com"

PROPIEDADES = [
    {
        "titulo": "Casa Colonial Remodelada en el Centro",
        "tipo_inmueble": "Casa", "zona": "Centro Cochabamba",
        "direccion": "Calle España, Centro, Cochabamba",
        "precio": "175000.00", "tipo_operacion": "Venta", "estado": "Disponible",
        "habitaciones": 3, "banos": 2, "superficie_m2": "200.00", "garaje": False, "antiguedad_anios": 40,
        "caracteristicas": [("Estilo", "Colonial remodelado")],
        "imagenes": ["https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Terreno para Proyecto Residencial",
        "tipo_inmueble": "Terreno", "zona": "Zona Norte Cochabamba",
        "direccion": "Km 5 Zona Norte, Cochabamba",
        "precio": "60000.00", "tipo_operacion": "Venta", "estado": "Disponible",
        "habitaciones": None, "banos": None, "superficie_m2": "500.00", "garaje": False, "antiguedad_anios": None,
        "caracteristicas": [("Uso de suelo", "Residencial")],
        "imagenes": ["https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Departamento Anticretico Cerca de la Universidad",
        "tipo_inmueble": "Departamento", "zona": "Centro Cochabamba",
        "direccion": "Av. Heroínas, Centro, Cochabamba",
        "precio": "15000.00", "tipo_operacion": "Anticretico", "estado": "Disponible",
        "habitaciones": 2, "banos": 1, "superficie_m2": "70.00", "garaje": False, "antiguedad_anios": 10,
        "caracteristicas": [("Cercania", "5 min a pie de la universidad")],
        "imagenes": ["https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=1000&q=80"],
    },
]