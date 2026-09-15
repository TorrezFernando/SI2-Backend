import json
from datetime import datetime
from cryptography.fernet import Fernet
import os

# En producción, esto DEBE venir de una variable de entorno. 
# Para este proyecto universitario, la dejaremos quemada aquí por simplicidad.
# Llave generada con: Fernet.generate_key()
DEV_SECRET_KEY = b'xLgB9wYk4uC8m1J3p5d9R8fQ4z2n3pT5zM8xLgB9wYk=' 
fernet = Fernet(DEV_SECRET_KEY)
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "bitacora_segura.log")

def log_accion_segura(ip: str, usuario: str, accion: str):
    """
    Toma los datos, los convierte en un JSON, los encripta y los guarda en una nueva línea del archivo.
    """
    registro = {
        "ip": ip,
        "usuario": usuario,
        "accion": accion,
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    registro_json = json.dumps(registro)
    registro_encriptado = fernet.encrypt(registro_json.encode('utf-8')).decode('utf-8')
    
    with open(LOG_FILE_PATH, "a", encoding='utf-8') as file:
        file.write(registro_encriptado + "\n")

def leer_bitacora_segura(dev_key: str):
    """
    Lee el archivo encriptado, desencripta línea por línea y devuelve la lista de registros.
    """
    if dev_key != DEV_SECRET_KEY.decode('utf-8'):
        raise ValueError("Llave de desarrollador inválida")
        
    if not os.path.exists(LOG_FILE_PATH):
        return []
        
    registros = []
    with open(LOG_FILE_PATH, "r", encoding='utf-8') as file:
        lineas = file.readlines()
        for linea in lineas:
            linea = linea.strip()
            if linea:
                try:
                    registro_desencriptado = fernet.decrypt(linea.encode('utf-8')).decode('utf-8')
                    registros.append(json.loads(registro_desencriptado))
                except Exception as e:
                    # En caso de que una línea haya sido manipulada, la ignoramos o marcamos el error.
                    registros.append({"error": "Linea corrupta o manipulada externamente"})
                    
    return registros
