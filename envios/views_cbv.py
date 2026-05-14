# envios/views_cbv.py

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin

from .models import Encomienda, Empleado
from .forms import EncomiendaForm
from config.choices import EstadoEnvio
from django.db.models import Q

# ── ListView: lista paginada ──────────────────────────────────────
class EncomiendaListView(LoginRequiredMixin, ListView):

    model = Encomienda
    template_name = 'envios/lista.html'
    context_object_name = 'encomiendas'   # nombre en el template
    paginate_by = 15
    ordering = ['-fecha_registro']

    def get_queryset(self):
        qs = Encomienda.objects.con_relaciones()

        estado = self.request.GET.get('estado')
        q = self.request.GET.get('q', '')

        if estado:
            qs = qs.filter(estado=estado)

        if q:
            qs = qs.filter(
                Q(codigo__icontains=q) |
                Q(remitente__apellidos__icontains=q) |
                Q(destinatario__apellidos__icontains=q)
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['estados'] = EstadoEnvio.choices
        ctx['estado_activo'] = self.request.GET.get('estado', '')
        ctx['q'] = self.request.GET.get('q', '')
        return ctx

# ── DetailView: detalle de un registro ───────────────────────────
class EncomiendaDetailView(LoginRequiredMixin, DetailView):

    model = Encomienda
    template_name = 'envios/detalle.html'
    context_object_name = 'encomienda'

    def get_queryset(self):
        return Encomienda.objects.con_relaciones()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['historial'] = self.object.historial.select_related('empleado')
        ctx['estados'] = EstadoEnvio.choices
        return ctx

# ── CreateView: formulario de creación ───────────────────────────
class EncomiendaCreateView(
    LoginRequiredMixin,
    SuccessMessageMixin,
    CreateView
):

    model = Encomienda
    form_class = EncomiendaForm
    template_name = 'envios/form.html'

    success_message = 'Encomienda %(codigo)s creada correctamente.'

    def get_success_url(self):
        return reverse_lazy(
            'encomienda_detalle',
            kwargs={'pk': self.object.pk}
        )

    def form_valid(self, form):
        # Asignar el empleado antes de guardar
        try:
            empleado = Empleado.objects.get(email=self.request.user.email)
            form.instance.empleado_registro = empleado
        except Empleado.DoesNotExist:
            form.add_error(None, 'No se encontró un empleado asociado a este usuario.')
            return self.form_invalid(form)
        return super().form_valid(form)


# ── UpdateView: formulario de edición ────────────────────────────
class EncomiendaUpdateView(
    LoginRequiredMixin,
    SuccessMessageMixin,
    UpdateView
):

    model = Encomienda
    form_class = EncomiendaForm
    template_name = 'envios/form.html'

    success_message = 'Encomienda actualizada correctamente.'

    def get_success_url(self):
        return reverse_lazy(
            'encomienda_detalle',
            kwargs={'pk': self.object.pk}
        )