# envios/admin.py

from django.contrib import admin
from django.utils.html import format_html

from .models import Empleado, Encomienda, HistorialEstado
from config.choices import EstadoEnvio


@admin.register(Encomienda)
class EncomiendaAdmin(admin.ModelAdmin):

    # Columnas visibles en el listado
    list_display = (
        'codigo',
        'remitente_nombre',
        'destinatario_nombre',
        'ruta',
        'estado_badge',
        'peso_kg',
        'fecha_registro',
    )

    # Filtros laterales
    list_filter = (
        'estado',
        'ruta',
        'fecha_registro',
    )

    # Búsqueda
    search_fields = (
        'codigo',
        'remitente__apellidos',
        'destinatario__apellidos',
        'remitente__nro_doc',
    )

    # Campos de solo lectura
    readonly_fields = (
        'codigo',
        'fecha_registro',
        'fecha_entrega_real',
    )

    # Ordenamiento por defecto
    ordering = ('-fecha_registro',)

    # Registros por página
    list_per_page = 20

    # Organizar campos en secciones
    fieldsets = (

        (
            'Identificación',
            {
                'fields': (
                    'codigo',
                    'descripcion',
                    'peso_kg',
                    'volumen_cm3',
                )
            }
        ),

        (
            'Partes',
            {
                'fields': (
                    'remitente',
                    'destinatario',
                    'ruta',
                    'empleado_registro',
                )
            }
        ),

        (
            'Estado y fechas',
            {
                'fields': (
                    'estado',
                    'costo_envio',
                    'fecha_registro',
                    'fecha_entrega_est',
                    'fecha_entrega_real',
                )
            }
        ),

        (
            'Notas',
            {
                'classes': ('collapse',),
                'fields': ('observaciones',)
            }
        ),
    )

    # Método personalizado para mostrar remitente
    def remitente_nombre(self, obj):
        return obj.remitente.nombre_completo

    remitente_nombre.short_description = 'Remitente'

    # Método personalizado para mostrar destinatario
    def destinatario_nombre(self, obj):
        return obj.destinatario.nombre_completo

    destinatario_nombre.short_description = 'Destinatario'

    # Método con HTML para colorear el estado
    def estado_badge(self, obj):

        colores = {
            'PE': '#6c757d',   # Pendiente
            'TR': '#0d6efd',   # En tránsito
            'DE': '#fd7e14',   # En destino
            'EN': '#198754',   # Entregado
            'DV': '#dc3545',   # Devuelto
        }

        color = colores.get(obj.estado, '#6c757d')

        return format_html(
            '''
            <span style="
                background:{};
                color:white;
                padding:2px 8px;
                border-radius:4px
            ">
                {}
            </span>
            ''',
            color,
            obj.get_estado_display()
        )

    estado_badge.short_description = 'Estado'


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):

    list_display = (
        'codigo',
        'apellidos',
        'nombres',
        'cargo',
        'email',
        'estado',
    )

    list_filter = (
        'cargo',
        'estado',
    )

    search_fields = (
        'codigo',
        'apellidos',
        'nombres',
        'email',
    )


@admin.register(HistorialEstado)
class HistorialEstadoAdmin(admin.ModelAdmin):

    list_display = (
        'encomienda',
        'estado_anterior',
        'estado_nuevo',
        'empleado',
        'fecha_cambio',
    )

    readonly_fields = (
        'encomienda',
        'estado_anterior',
        'estado_nuevo',
        'empleado',
        'fecha_cambio',
    )

    list_filter = (
        'estado_nuevo',
    )

    ordering = ('-fecha_cambio',)