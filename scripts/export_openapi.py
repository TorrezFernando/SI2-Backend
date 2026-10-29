"""Exporta el contrato de API sin tocar la base de datos de desarrollo."""
import json
import os
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
os.environ['DATABASE_URL']='sqlite://'
from main import app
(root/'docs'/'openapi.json').write_text(json.dumps(app.openapi(),ensure_ascii=False,indent=2),encoding='utf-8')
print('docs/openapi.json actualizado')
