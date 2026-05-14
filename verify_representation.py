import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['ALLOWED_HOSTS'] = 'testserver,localhost,127.0.0.1,*'
django.setup()

from django.contrib.auth.models import User
from envios.models import Encomienda
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

# Crear o recuperar usuarios
staff_user, _ = User.objects.get_or_create(username='staff_test', email='staff@enc.pe', is_staff=True)
normal_user, _ = User.objects.get_or_create(username='normal_test', email='normal@enc.pe', is_staff=False)

enc = Encomienda.objects.first()
if not enc:
    print("No se encontraron encomiendas en la BD para probar.")
    exit(0)

client = APIClient()

print("\n--- REQUEST CON USUARIO STAFF ---")
refresh_staff = RefreshToken.for_user(staff_user)
client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh_staff.access_token}')
resp_staff = client.get(f'/api/v1/encomiendas/{enc.id}/')

if resp_staff.status_code != 200:
    print("Error:", resp_staff.json())
else:
    data_staff = resp_staff.json()
    print("  estado_color:", data_staff.get('estado_color'))
    print("  ruta_codigo:", data_staff.get('ruta_codigo'))
    print("  ruta_destino:", data_staff.get('ruta_destino'))
    print("  costo_display:", data_staff.get('costo_display'))
    print("  ¿observaciones presente?:", 'observaciones' in data_staff)
    print("  ¿empleado_registro presente?:", 'empleado_registro' in data_staff)

print("\n--- REQUEST CON USUARIO NORMAL ---")
refresh_normal = RefreshToken.for_user(normal_user)
client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh_normal.access_token}')
resp_normal = client.get(f'/api/v1/encomiendas/{enc.id}/')

if resp_normal.status_code != 200:
    print("Error:", resp_normal.json())
else:
    data_normal = resp_normal.json()
    print("  estado_color:", data_normal.get('estado_color'))
    print("  ruta_codigo:", data_normal.get('ruta_codigo'))
    print("  ruta_destino:", data_normal.get('ruta_destino'))
    print("  costo_display:", data_normal.get('costo_display'))
    print("  ¿observaciones presente?:", 'observaciones' in data_normal)
    print("  ¿empleado_registro presente?:", 'empleado_registro' in data_normal)
