# envios/views.py
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied

from .models import Encomienda, Empleado, HistorialEstado
from clientes.models import Cliente
from rutas.models import Ruta
from config.choices import EstadoEnvio
from .forms import EncomiendaForm

# ============================================================
# VISTA MÍNIMA
# ============================================================
def mi_vista(request):
    """Vista mínima de ejemplo"""
    return HttpResponse('Hola desde Django')

# ============================================================
# VISTAS PRINCIPALES
# ============================================================
@login_required
def dashboard(request):
    """Vista principal del sistema con estadísticas"""
    hoy = timezone.now().date()

    context = {
        'total_activas': Encomienda.objects.activas().count(),
        'en_transito': Encomienda.objects.en_transito().count(),
        'con_retraso': Encomienda.objects.con_retraso().count(),
        'entregadas_hoy': Encomienda.objects.filter(
            estado=EstadoEnvio.ENTREGADO,
            fecha_entrega_real=hoy
        ).count(),
        'ultimas': Encomienda.objects.con_relaciones()[:5],
    }

    return render(request, 'envios/dashboard.html', context)

@login_required
def encomienda_lista(request):

    qs = Encomienda.objects.con_relaciones()

    # Filtros opcionales
    # Si no hay estado en GET, usar el de la sesión
    estado = request.GET.get('estado', request.session.get('ultimo_filtro_estado', ''))
    q = request.GET.get('q', '')

    if estado:
        qs = qs.filter(estado=estado)
        # Guardar el filtro en sesión
        request.session['ultimo_filtro_estado'] = estado

    if q:
        qs = qs.filter(
            Q(codigo__icontains=q) |
            Q(remitente__apellidos__icontains=q) |
            Q(destinatario__apellidos__icontains=q)
        )

    # Paginación
    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page', 1)
    encomiendas = paginator.get_page(page_number)

    return render(
        request,
        'envios/lista.html',
        {
            'encomiendas': encomiendas,
            'estados': EstadoEnvio.choices,
            'estado_activo': estado,
            'q': q,
        }
    )

@login_required
def encomienda_detalle(request, pk):
    """Detalle de una encomienda usando get_object_or_404"""
    enc = get_object_or_404(Encomienda.objects.con_relaciones(), pk=pk)
    return render(request, 'envios/detalle.html', {
        'encomienda': enc,
        'estados': EstadoEnvio.choices
    })

@login_required
def encomiendas_por_ruta(request, ruta_pk):
    """Lista de encomiendas por ruta o devuelve 404 si está vacía"""
    encomiendas = get_list_or_404(Encomienda, ruta__pk=ruta_pk)
    return render(request, 'envios/lista.html', {'encomiendas': encomiendas})

@login_required
def encomienda_crear(request):
    """
    GET  → muestra el formulario vacío
    POST → valida, guarda y redirige al detalle
    """
    if request.method == 'POST':
        form = EncomiendaForm(request.POST)
        if form.is_valid():
            enc = form.save(commit=False)
            enc.empleado_registro = Empleado.objects.get(email=request.user.email)
            enc.save()

            # Guardar ruta seleccionada en sesión para próxima vez
            if enc.ruta_id:
                request.session['ruta_seleccionada'] = enc.ruta_id

            # Limpiar filtro de estado en sesión al crear nueva
            if 'ultimo_filtro_estado' in request.session:
                del request.session['ultimo_filtro_estado']

            messages.success(
                request,
                f'Encomienda {enc.codigo} registrada correctamente.'
            )
            return redirect('encomienda_detalle', pk=enc.pk)
    else:
        # Pre-seleccionar la ruta desde la sesión
        initial_data = {}
        ruta_id = request.session.get('ruta_seleccionada')
        if ruta_id:
            initial_data['ruta'] = ruta_id
        form = EncomiendaForm(initial=initial_data)

    return render(request, 'envios/form.html', {
        'form': form,
        'titulo': 'Nueva Encomienda',
    })

@login_required
@require_POST
def encomienda_cambiar_estado(request, pk):
    """Cambiar estado de una encomienda (solo POST)"""
    enc = get_object_or_404(Encomienda, pk=pk)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        observacion = request.POST.get('observacion', '')
        try:
            empleado = Empleado.objects.get(email=request.user.email)
            enc.cambiar_estado(nuevo_estado, empleado, observacion)
            messages.success(request, f'Estado actualizado a: {enc.get_estado_display()}')
        except ValueError as e:
            messages.error(request, str(e))

    return redirect('encomienda_detalle', pk=pk)


@login_required
def encomienda_editar(request, pk):
    """Editar una encomienda existente"""
    enc = get_object_or_404(Encomienda, pk=pk)

    if request.method == 'POST':
        form = EncomiendaForm(request.POST, instance=enc)
        if form.is_valid():
            enc = form.save()
            messages.success(request, f'Encomienda {enc.codigo} actualizada.')
            return redirect('encomienda_detalle', pk=enc.pk)
    else:
        form = EncomiendaForm(instance=enc)

    return render(request, 'envios/form.html', {
        'form': form,
        'titulo': f'Editar {enc.codigo}',
    })


# ============================================================
# ENDPOINTS AJAX / JSON
# ============================================================
@login_required
def encomienda_estado_json(request, pk):
    """Endpoint AJAX para el badge del navbar"""
    enc = get_object_or_404(Encomienda, pk=pk)
    return JsonResponse({
        'codigo': enc.codigo,
        'estado': enc.estado,
        'display': enc.get_estado_display(),
        'retraso': enc.tiene_retraso,
        'dias': enc.dias_en_transito,
    })


@login_required
def encomienda_api(request, uuid):
    """API endpoint que recibe UUID de encomienda"""
    from django.core.exceptions import ObjectDoesNotExist
    try:
        enc = Encomienda.objects.get(pk=uuid)
        return JsonResponse({
            'id': str(enc.pk),
            'codigo': enc.codigo,
            'estado': enc.estado,
            'descripcion': enc.descripcion,
            'peso_kg': float(enc.peso_kg),
            'remitente': enc.remitente.nombre_completo,
            'destinatario': enc.destinatario.nombre_completo,
            'ruta': str(enc.ruta),
            'costo_envio': float(enc.costo_envio),
            'fecha_registro': enc.fecha_registro.isoformat(),
        })
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Encomienda no encontrada'}, status=404)

# ============================================================
# VISTAS CON PERMISOS ESPECIALES
# ============================================================
@login_required
def encomienda_por_codigo(request, codigo):
    """Buscar encomienda por código"""
    try:
        enc = Encomienda.objects.get(codigo=codigo.upper())
    except Encomienda.DoesNotExist:
        raise Http404(f'No existe la encomienda {codigo}')
    return render(request, 'envios/detalle.html', {'encomienda': enc})

def es_empleado_activo(user):
    """True si el user tiene un Empleado activo asociado"""
    return (
        user.is_authenticated and
        Empleado.objects.filter(email=user.email, estado=1).exists()
    )

@user_passes_test(es_empleado_activo, login_url='/sin-permiso/')
def registrar_envio(request):
    """Vista solo para empleados activos"""
    pass  # Implementar según necesidad


@permission_required('envios.add_encomienda', raise_exception=True)
def encomienda_crear_con_permiso(request):
    """Vista con permiso específico"""
    pass  # Implementar según necesidad

@login_required
def eliminar_encomienda(request, pk):
    """Eliminar encomienda solo si está pendiente"""
    enc = get_object_or_404(Encomienda, pk=pk)

    # Solo se puede eliminar si está pendiente (lógica de negocio)
    if enc.estado != 'PE':
        raise PermissionDenied

    if request.method == 'POST':
        enc.delete()
        messages.success(request, 'Encomienda eliminada.')
        return redirect('encomienda_lista')

    return render(request, 'envios/confirmar_eliminar.html', {'enc': enc})

# ============================================================
# VISTA DE UTILIDAD
# ============================================================
def ping(request):
    """Endpoint de salud"""
    return HttpResponse('pong', status=200, content_type='text/plain')