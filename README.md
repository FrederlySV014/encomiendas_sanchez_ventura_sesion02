# Sistema de Gestión de Encomiendas - API REST (Django REST Framework)

Este proyecto implementa una API REST completa, segura y altamente optimizada para la gestión del ciclo de vida completo de envíos y encomiendas, desarrollada con Django y Django REST Framework (DRF).

---

## Características Principales

### 1. Arquitectura REST y ViewSets
- Implementación de **ModelViewSets** y **Generic Views** para gestionar Encomiendas, Clientes y Rutas.
- Acciones personalizadas (`@action`) para operaciones clave como `cambiar_estado`, `pendientes`, `con_retraso` y `estadisticas`.
- Enrutamiento automático mediante `DefaultRouter`.

### 2. Serializadores Avanzados y Versionado
- **API v1**: Serializadores optimizados según el contexto (`EncomiendaListSerializer` ligero para tablas, `EncomiendaDetailSerializer` con anidamiento profundo para vistas de detalle).
- **API v2**: Estructura mejorada con metadatos (`meta`) y campos calculados avanzados.
- **Filtrado Dinámico**: Uso de `to_representation()` para ocultar información confidencial (ej. observaciones y datos de registro) a usuarios sin rol de staff.
- **Pre-Validación**: Normalización de datos en `to_internal_value()` (mayúsculas automáticas, sanitización de espacios y redondeo de moneda).

### 3. Seguridad y Control de Acceso
- **Autenticación JWT**: Integración con `djangorestframework-simplejwt` con claims y payload personalizados.
- **Permisos Granulares**: Clases personalizadas (`EsEmpleadoActivo`, `EsPropietarioOAdmin`) para asegurar que cada rol acceda únicamente a sus recursos permitidos.
- **Throttling (Límite de Peticiones)**: Protección contra ataques de fuerza bruta y saturación mediante `LoginRateThrottle` y `EmpleadoRateThrottle`.
- **CORS Configurado**: Integración completa con `django-cors-headers` para entornos de producción.

### 4. Rendimiento Extremo y Caching
- **Optimización de Consultas N+1**: Uso exhaustivo de `select_related()` y `prefetch_related()` en managers personalizados (`con_relaciones()`), reduciendo el listado de 61 a **2 consultas SQL**.
- **Caché en Memoria (Redis)**: Caché distribuido con Redis (`django-redis`). Endpoint de rutas y cálculo de estadísticas cacheados por 15 minutos, con **invalidación en tiempo real** al modificar encomiendas.
- **Bulk Operations**: Endpoints de procesamiento masivo (`bulk_create` y `bulk_estado`) capaces de procesar y cambiar estados de múltiples paquetes en una única transacción SQL.

### 5. Documentación y Estandarización
- **Manejador de Excepciones Personalizado**: Todas las respuestas de error (400, 401, 403, 404, 422, 500) devuelven una estructura JSON idéntica y predecible (`error`, `code`, `message`, `detail`).
- **OpenAPI / Swagger**: Documentación interactiva completa generada con `drf-spectacular` accesible en `/api/docs/`.

---

## Entorno y Despliegue con Docker

El proyecto está completamente dockerizado e incluye servicios para Django, PostgreSQL y Redis.

```bash
# Levantar la infraestructura en segundo plano
docker compose up -d --build

# Aplicar migraciones
docker compose exec web python manage.py migrate

# Crear superusuario para el panel de administración
docker compose exec web python manage.py createsuperuser
```

---

## Pruebas Unitarias (Testing)

El sistema cuenta con una suite completa de 23 pruebas automatizadas escritas en **pytest**, cubriendo flujos de autenticación, listados, filtrado, creación con validaciones cruzadas y versionado.

```bash
# Ejecutar todas las pruebas
docker compose exec web pytest
```

---

## Principales Endpoints

- `GET /api/v1/encomiendas/` - Listado paginado y optimizado (soporta `?estado=PE`, `?search=...`).
- `POST /api/v1/encomiendas/` - Registro de nueva encomienda.
- `GET /api/v1/encomiendas/{id}/` - Detalle completo de la encomienda y su historial.
- `POST /api/v1/encomiendas/{id}/cambiar_estado/` - Transición de estado con validación de negocio.
- `GET /api/v1/encomiendas/estadisticas/` - Contadores cacheados en Redis.
- `POST /api/v1/encomiendas/bulk_create/` - Alta masiva transaccional.
- `GET /api/docs/` - Interfaz Swagger UI.
- `GET /silk/` - Panel de profiling de consultas SQL (solo en entorno de desarrollo).
