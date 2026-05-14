// static/js/main.js

document.addEventListener('DOMContentLoaded', function () {
    // ─────────────────────────────────────────
    // Inicializar tooltips de Bootstrap
    // ─────────────────────────────────────────
    const tooltips = document.querySelectorAll(
        '[data-bs-toggle="tooltip"]'
    );
    tooltips.forEach(el => new bootstrap.Tooltip(el));

    // ─────────────────────────────────────────
    // Auto-cerrar alertas flash después de 5 segundos
    // (complementa la animación CSS)
    // ─────────────────────────────────────────
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (alert) {
            const bsAlert =
                bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);

    // ─────────────────────────────────────────
    // Confirmación antes de eliminar
    // ─────────────────────────────────────────
    // Uso en el template:
    // <button
    //     onclick="return confirmar('Eliminar este registro?')"
    //     form="formEliminar"
    // >
    //     Eliminar
    // </button>

    window.confirmar = function (mensaje) {
        return confirm(
            mensaje || '¿Estás seguro?'
        );
    };

    // ─────────────────────────────────────────
    // Resaltar fila al hacer clic
    // ─────────────────────────────────────────
    // Uso:
    // <tr
    //     class="fila-link"
    //     data-href="{% url 'encomienda_detalle' enc.pk %}"
    // >
    // </tr>

    document.querySelectorAll('.fila-link').forEach(function (fila) {
        fila.addEventListener('click', function () {

            window.location = this.dataset.href;

        });
    });
});