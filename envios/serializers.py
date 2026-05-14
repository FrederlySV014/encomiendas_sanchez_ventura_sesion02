# envios/serializers.py

from rest_framework import serializers
from django.utils import timezone

from .models import Encomienda, HistorialEstado, Empleado
from clientes.models import Cliente
from rutas.models import Ruta

# ── Cliente Serializer ────────────────────────────────────────────
class ClienteSerializer(serializers.ModelSerializer):
    # @property del modelo expuesta como campo de solo lectura
    nombre_completo = serializers.ReadOnlyField()
    esta_activo = serializers.ReadOnlyField()

    class Meta:
        model = Cliente
        fields = [
            'id',
            'tipo_doc',
            'nro_doc',
            'nombres',
            'apellidos',
            'nombre_completo',
            'telefono',
            'email',
            'esta_activo',
        ]

# ── Ruta Serializer ───────────────────────────────────────────────
class RutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruta
        fields = [
            'id',
            'codigo',
            'origen',
            'destino',
            'precio_base',
            'dias_entrega',
            'estado',
        ]

# ── Historial Estado Serializer ──────────────────────────────────
class HistorialEstadoSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.ReadOnlyField(
        source='empleado.__str__'
    )

    estado_anterior_display = serializers.CharField(
        source='get_estado_anterior_display',
        read_only=True
    )

    estado_nuevo_display = serializers.CharField(
        source='get_estado_nuevo_display',
        read_only=True
    )

    class Meta:
        model = HistorialEstado
        fields = [
            'id',
            'estado_anterior',
            'estado_anterior_display',
            'estado_nuevo',
            'estado_nuevo_display',
            'empleado_nombre',
            'observacion',
            'fecha_cambio',
        ]

# ── Encomienda Bulk Serializer ──────────────────────────────────────
class EncomiendaBulkSerializer(serializers.ListSerializer):
    """
    Serializer para operaciones masivas.
    Se activa automaticamente cuando se usa EncomiendaSerializer(many=True).
    Reemplaza los metodos create() y update() por versiones optimizadas
    que hacen una sola query SQL en lugar de N queries.
    """

    def create(self, validated_data):
        """
        Crear multiples encomiendas con una sola query SQL.
        """
        encomiendas = [
            Encomienda(**item)
            for item in validated_data
        ]
        return Encomienda.objects.bulk_create(encomiendas)

    def update(self, instances, validated_data):
        """
        Actualizar multiples encomiendas en batch.
        """
        instance_map = {enc.id: enc for enc in instances}
        updated = []

        for item in validated_data:
            enc_id = item.pop('id', None)
            enc = instance_map.get(enc_id)

            if enc:
                for campo, valor in item.items():
                    setattr(enc, campo, valor)
                updated.append(enc)

        if updated:
            Encomienda.objects.bulk_update(
                updated,
                ['estado', 'observaciones', 'costo_envio'],
            )

        return updated

# ── Encomienda Serializer ─────────────────────────────────────────
class EncomiendaSerializer(serializers.ModelSerializer):
    # Propiedades del modelo como campos de solo lectura
    esta_entregada = serializers.ReadOnlyField()
    tiene_retraso = serializers.ReadOnlyField()
    dias_en_transito = serializers.ReadOnlyField()
    descripcion_corta = serializers.ReadOnlyField()
    # Campo calculado con método
    estado_display = serializers.SerializerMethodField()

    class Meta:
        model = Encomienda
        fields = [
            'id',
            'codigo',
            'descripcion',
            'descripcion_corta',
            'peso_kg',
            'volumen_cm3',
            'costo_envio',
            'remitente',
            'destinatario',
            'ruta',
            'empleado_registro',
            'estado',
            'estado_display',
            'fecha_registro',
            'fecha_entrega_est',
            'fecha_entrega_real',
            'esta_entregada',
            'tiene_retraso',
            'dias_en_transito',
            'observaciones',
        ]

        read_only_fields = [
            'fecha_registro',
            'fecha_entrega_real',
            'empleado_registro',
        ]
        list_serializer_class = EncomiendaBulkSerializer

    def get_estado_display(self, obj):
        return obj.get_estado_display()

    # ── NUEVO: personalizar la salida JSON ───────────────────────────
    def to_representation(self, instance):
        """
        Se ejecuta al serializar (convertir objeto -> JSON).
        Permite modificar la respuesta despues de que DRF la genera.
        """
        data = super().to_representation(instance)

        # 1. Agregar campos de conveniencia calculados desde la ruta
        if getattr(instance, 'ruta_id', None):
            data['ruta_codigo'] = instance.ruta.codigo
            data['ruta_destino'] = instance.ruta.destino
            data['ruta_origen'] = instance.ruta.origen

        # 2. Formatear el costo con prefijo de moneda
        if getattr(instance, 'costo_envio', None) is not None:
            data['costo_display'] = f'S/ {instance.costo_envio:.2f}'

        # 3. Ocultar campos sensibles para usuarios no staff
        request = self.context.get('request')

        if request and not request.user.is_staff:
            data.pop('observaciones', None)
            data.pop('empleado_registro', None)

        # 4. Agregar indicador visual del estado para el frontend
        colores = {
            'PE': 'gray',
            'TR': 'blue',
            'DE': 'orange',
            'EN': 'green',
            'DV': 'red',
        }

        data['estado_color'] = colores.get(instance.estado, 'gray')

        return data

    # ── NUEVO: normalizar datos entrantes ─────────────────────────
    def to_internal_value(self, data):
        """
        Se ejecuta al deserializar (convertir JSON -> objeto Python).
        Se usa para limpiar y normalizar ANTES de la validacion.
        """
        # Necesitamos una copia mutable del dict
        if hasattr(data, '_mutable'):
            data._mutable = True

        data = data.copy() if hasattr(data, 'copy') else dict(data)

        # 1. Normalizar el codigo: forzar mayusculas y quitar espacios
        if 'codigo' in data and data['codigo']:
            data['codigo'] = str(data['codigo']).upper().strip()

        # 2. Limpiar la descripcion: quitar espacios extra
        if 'descripcion' in data and data['descripcion']:
            data['descripcion'] = str(data['descripcion']).strip()

        # 3. Asegurar que el costo tenga maximo 2 decimales
        if 'costo_envio' in data and data['costo_envio']:
            try:
                from decimal import Decimal, ROUND_HALF_UP
                costo = Decimal(str(data['costo_envio']))
                data['costo_envio'] = str(
                    costo.quantize(
                        Decimal('0.01'),
                        rounding=ROUND_HALF_UP
                    )
                )
            except Exception:
                pass  # si falla, la validacion posterior lo rechazara

        return super().to_internal_value(data)

    # ── Validator de campo: validate_{nombre} ──────────────────────
    def validate_peso_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'El peso debe ser mayor a 0 kg.'
            )
        if value > 500:
            raise serializers.ValidationError(
                'El peso máximo permitido es 500 kg.'
            )
        return value

    def validate_codigo(self, value):
        if not value.startswith('ENC-'):
            raise serializers.ValidationError(
                'El código debe comenzar con ENC-'
            )
        return value.upper()

    def validate_costo_envio(self, value):
        if value < 0:
            raise serializers.ValidationError(
                'El costo no puede ser negativo.'
            )
        return value

    # ── Validación cruzada: validate() ──────────────────────────
    def validate(self, data):
        errors = {}

        # Regla 1: remitente != destinatario
        if data.get('remitente') == data.get('destinatario'):
            errors['destinatario'] = (
                'El destinatario no puede ser el mismo que el remitente.'
            )

        # Regla 2: fecha estimada no en el pasado
        fecha_est = data.get('fecha_entrega_est')
        if fecha_est and fecha_est < timezone.now().date():
            errors['fecha_entrega_est'] = (
                'La fecha estimada no puede ser en el pasado.'
            )

        # Regla 3: costo mínimo según la ruta
        ruta = data.get('ruta')
        costo = data.get('costo_envio')
        if ruta and costo and costo < float(ruta.precio_base):
            errors['costo_envio'] = (
                f'El costo mínimo para esta ruta es S/ {ruta.precio_base}.'
            )

        if errors:
            raise serializers.ValidationError(errors)
        return data

# ── Encomienda List Serializer (Ligero) ──────────────────────────
class EncomiendaListSerializer(serializers.ModelSerializer):
    """
    Serializer optimizado para el listado.

    Solo los campos necesarios para mostrar la tabla.
    No incluye descripcion larga, observaciones ni historial.
    """

    remitente_nombre = serializers.ReadOnlyField(source='remitente.nombre_completo')
    destinatario_nombre = serializers.ReadOnlyField(source='destinatario.nombre_completo')
    ruta_destino = serializers.ReadOnlyField(source='ruta.destino')
    estado_display = serializers.SerializerMethodField()
    tiene_retraso = serializers.ReadOnlyField()

    class Meta:
        model = Encomienda
        fields = [
            'id', 'codigo', 'estado', 'estado_display',
            'remitente_nombre', 'destinatario_nombre',
            'ruta_destino', 'peso_kg', 'costo_envio',
            'fecha_registro', 'fecha_entrega_est', 'tiene_retraso',
        ]
        read_only_fields = ['articulo_id']

    def get_estado_display(self, obj):
        return obj.get_estado_display()

# ── Encomienda Detail Serializer ─────────────────────────────────
class EncomiendaDetailSerializer(EncomiendaSerializer):
    """Serializer con objetos anidados completos (para el detalle)"""
    remitente = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta = RutaSerializer(read_only=True)
    historial = HistorialEstadoSerializer(
        many=True,
        read_only=True
    )

    remitente_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(),
        write_only=True,
        source='remitente'
    )

    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(),
        write_only=True,
        source='destinatario'
    )

    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(),
        write_only=True,
        source='ruta'
    )

    class Meta(EncomiendaSerializer.Meta):
        fields = [
            'id', 'codigo', 'descripcion', 'peso_kg',
            'remitente', 'remitente_id',
            'destinatario', 'destinatario_id',
            'ruta', 'ruta_id',
            'estado', 'costo_envio',
            'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real',
            'esta_entregada', 'tiene_retraso', 'dias_en_transito',
            'historial', 'observaciones',
        ]

class EncomiendaV2Serializer(serializers.ModelSerializer):
    """
    Serializer para la API v2.

    Diferencias con v1:
    - remitente y destinatario como objetos anidados completos
    - ruta como objeto anidado
    - Campos de analisis: dias_en_transito, descripcion_corta
    - Campo 'meta' con informacion de la version
    """

    # Objetos anidados completos (en v1 son solo IDs)
    remitente = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta = RutaSerializer(read_only=True)

    # Para escritura: seguir aceptando IDs
    remitente_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(),
        write_only=True,
        source='remitente'
    )

    destinatario_id = serializers.PrimaryKeyRelatedField(
        queryset=Cliente.objects.activos(),
        write_only=True,
        source='destinatario'
    )

    ruta_id = serializers.PrimaryKeyRelatedField(
        queryset=Ruta.objects.activas(),
        write_only=True,
        source='ruta'
    )

    # Campos nuevos en v2 (propiedades del modelo)
    dias_en_transito = serializers.ReadOnlyField()
    tiene_retraso = serializers.ReadOnlyField()
    esta_entregada = serializers.ReadOnlyField()
    descripcion_corta = serializers.ReadOnlyField()

    # Campo de metadatos de la version
    meta = serializers.SerializerMethodField()

    class Meta:
        model = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'descripcion_corta',
            'peso_kg', 'volumen_cm3', 'costo_envio',
            'remitente', 'remitente_id',
            'destinatario', 'destinatario_id',
            'ruta', 'ruta_id',
            'estado', 'fecha_registro', 'fecha_entrega_est',
            'dias_en_transito', 'tiene_retraso', 'esta_entregada',
            'observaciones', 'meta',
        ]
        read_only_fields = ['codigo', 'fecha_registro']

    def get_meta(self, obj):
        """Metadatos utiles para el cliente que consume la API"""
        from django.utils import timezone

        return {
            'version': 'v2',
            'generado': timezone.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'puede_editar': not obj.esta_entregada,
        }