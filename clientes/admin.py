# clientes/admin.py
from django.contrib import admin
from .models import Cliente 

# Register your models here.
@admin.register(Cliente) 
class ClienteAdmin(admin.ModelAdmin): 
    list_display  = ('nro_doc', 'tipo_doc', 'apellidos', 'nombres', 'telefono', 'estado') 
    list_ﬁlter   = ('tipo_doc', 'estado') 
    search_ﬁelds = ('nro_doc', 'apellidos', 'nombres')
