import urllib.request
import json

def fetch(url, data, headers):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

print("Haciendo login...")
login_data = {"correo": "admin@premium.com", "password": "Admin123!"}
status, text = fetch("http://localhost:8000/gestion_usuarios/auth/login", login_data, {"Content-Type": "application/json"})
if status != 200:
    print("Error login:", status, text)
    exit(1)

token = json.loads(text)["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print("\nIntentando crear Cliente con CI 999999...")
status, text = fetch("http://localhost:8000/modulo_inmuebles/clientes", {"ci_usuario": "999999"}, headers)
print("Status:", status)
print("Response:", text)

print("\nIntentando crear Propietario con CI 123456...")
status, text = fetch("http://localhost:8000/modulo_inmuebles/propietarios", {"ci_usuario": "123456"}, headers)
print("Status:", status)
print("Response:", text)
