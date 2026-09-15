"""Dataset del tenant: Inmobiliaria Metropoli (Santa Cruz)."""

TENANT = {
    "nombre": "Inmobiliaria Metropoli",
    "slug": "metropoli",
    "plan": "pro",
    "max_propiedades": 100,
}

USUARIOS = [
    {"ci": "3300001", "nombre": "Admin Metropoli", "correo": "admin@metropoli.com",
     "telefono": "73300001", "rol": "Administrador", "password": "Admin.123@"},
    {"ci": "3300002", "nombre": "Valeria Suarez", "correo": "agente@metropoli.com",
     "telefono": "73300002", "rol": "Agente", "password": "Password.123@"},
    {"ci": "3300003", "nombre": "Ricardo Mendez", "correo": "propietario@metropoli.com",
     "telefono": "73300003", "rol": "Propietario", "password": "Password.123@"},
    {"ci": "3300004", "nombre": "Paola Justiniano", "correo": "cliente@metropoli.com",
     "telefono": "73300004", "rol": "Cliente", "password": "Password.123@"},
]

PROPIETARIO_CORREO = "propietario@metropoli.com"
AGENTE_CORREO = "agente@metropoli.com"

PROPIEDADES = [
    {
        "titulo": "Oficina Corporativa en Torre Empresarial",
        "tipo_inmueble": "Oficina", "zona": "Segundo Anillo",
        "direccion": "Av. Cristóbal de Mendoza, 2do Anillo, Torre Dúo, Santa Cruz",
        "precio": "1200.00", "tipo_operacion": "Alquiler", "estado": "Disponible",
        "habitaciones": None, "banos": 2, "superficie_m2": "85.00", "garaje": True, "antiguedad_anios": 4,
        "caracteristicas": [("Divisiones", "3 ambientes + recepción")],
        "imagenes": ["https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Casa en Condominio Cerrado con Seguridad 24/7",
        "tipo_inmueble": "Casa", "zona": "Zona Norte",
        "direccion": "Zona Norte Km 9, Condominio Sevilla Los Jardines, Santa Cruz",
        "precio": "38000.00", "tipo_operacion": "Anticretico", "estado": "Disponible",
        "habitaciones": 3, "banos": 3, "superficie_m2": "250.00", "garaje": True, "antiguedad_anios": 5,
        "caracteristicas": [("Club House", "Canchas y piscinas")],
        "imagenes": ["https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1000&q=80"],
    },
    {
        "titulo": "Departamento Ejecutivo Amoblado",
        "tipo_inmueble": "Departamento", "zona": "Equipetrol",
        "direccion": "Av. San Martín, Equipetrol, Santa Cruz",
        "precio": "650.00", "tipo_operacion": "Alquiler", "estado": "Disponible",
        "habitaciones": 2, "banos": 2, "superficie_m2": "80.00", "garaje": True, "antiguedad_anios": 1,
        "caracteristicas": [("Amoblado", "Si, completamente")],
        "imagenes": ["https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1000&q=80"],
    },
]