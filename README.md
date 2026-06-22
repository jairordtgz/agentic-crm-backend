# ISP / ERP – Gestión de Clientes, Líneas y Cobranza

Mini-servicio REST desarrollado con **Django + Django REST Framework**, que gestiona
clientes y líneas de servicio, e implementa un **proceso asíncrono y periódico**
(**Celery + Redis**) para el control de morosidad.

El proyecto simula un escenario típico de un **ISP / ERP**, donde las líneas deben
suspenderse o reactivarse automáticamente según su estado de cobranza, manteniendo
siempre **trazabilidad persistente** de cada ejecución.

---

## Stack tecnológico

- Django + Django REST Framework  
- SQLite (desarrollo local) / PostgreSQL (Docker)  
- Celery + Celery Beat  
- Redis (broker de mensajes)  
- pytest / pytest-django  

---

## Arquitectura — decisiones y trade-offs

Este proyecto prioriza **claridad, pragmatismo y adecuación al alcance del ejercicio**.

- **No se implementó Clean Architecture completa** (repositorios abstractos,
  entidades desacopladas del ORM). Para el tamaño del proyecto y con un único backend
  de persistencia, esa capa adicional introduce más complejidad que beneficios reales
  (principio *YAGNI*). El ORM de Django cumple correctamente el rol de capa de
  persistencia.

- **Separación de capas solo donde existe lógica de negocio no trivial**.  
  La app `cobranza` separa:
  - `tasks.py`: orquestación y ejecución asíncrona (Celery).
  - `services.py`: reglas de negocio puras (`MorosidadService`).

  Esto permite testear la lógica de suspensión/reactivación sin necesidad de levantar
  Redis ni Celery.  
  El CRUD de `cliente` y `linea` mantiene la validación en los serializers, que es el
  nivel de abstracción correcto dentro de DRF.

- **Principios SOLID aplicados de forma puntual**:
  - **SRP**:  
    `models.py` (estructura de datos),  
    `services.py` (reglas de negocio),  
    `tasks.py` (IO y ejecución asíncrona).
  - **OCP**: la política de suspensión está encapsulada en
    `_determinar_accion()`. Cambiar la regla no afecta el resto del flujo.
  - **DIP**: el task depende de `MorosidadService`, no de queries inline.

- **Soft delete**:  
  `Cliente` y `LineaServicio` usan `is_active=False`, nunca borrado físico.  
  `Rubro` no tiene `is_active`; el estado `ANULADO` cumple esa función.

- **Idempotencia del proceso**:  
  Cada ejecución recalcula desde cero `saldo_vencido` (agregación SQL, no
  acumulación) y compara el `estado_linea` actual antes de decidir acciones.
  Ejecuciones repetidas sin cambios producen siempre el mismo resultado.
  Se crea un `CollectionsRequestLog` por corrida de forma intencional para
  trazabilidad histórica.

- **Regla de negocio explícita**:  
  Las líneas en estado `CANCELADO` o `NO_INSTALADO` **nunca se suspenden**, incluso si
  tienen rubros vencidos. Aun así, se calcula `saldo_vencido` y `unpaid_count` para
  mantener trazabilidad, dejando `action_taken=NONE`.

- **Optimización de queries**:  
  Se evita el problema de N+1 queries utilizando agregaciones (`Count`, `Sum`) en una
  sola consulta por línea, en lugar de cargar todos los rubros en memoria.

- **Resiliencia y manejo de errores**:  
  - Cada log se crea con `status=FAILED` por defecto y solo se marca como `SUCCESS`
    si el proceso finaliza correctamente.
  - Errores por línea se capturan individualmente y no detienen el procesamiento del
    resto.
  - El task completo usa `autoretry_for` con backoff ante fallas sistémicas
    (por ejemplo, problemas de conexión a la base de datos).

- **Autenticación**:  
  Se utiliza **Token Authentication** de DRF (`rest_framework.authtoken`).
  - Usuarios autenticados pueden leer, crear y editar.
  - El `DELETE` (soft delete) está restringido a usuarios `is_staff` mediante
    `core/permissions.py`.

- **Endpoint `estado-cobranza`**:  
  Calcula `unpaid_count` en tiempo real (no a partir del último log), garantizando que
  el resumen sea correcto incluso si la tarea periódica aún no se ha ejecutado.

---

## Setup local

```bash
git clone <url-del-repo>
cd prueba-tecnica-desarrollador-backend
python -m venv venv

# Windows
venv\Scripts\Activate.ps1
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt

## Variables de entorno

| Variable | Default (sin definir) | Uso |
|---|---|---|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Broker de Celery |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Backend de resultados |
| `DB_ENGINE` | `django.db.backends.sqlite3` | Motor de BD |
| `DB_NAME` | `db.sqlite3` | Nombre/archivo de BD |
| `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | — | Solo si `DB_ENGINE` es Postgres |

Sin definir nada, el proyecto corre con SQLite local — útil para desarrollo rápido.

## Comandos

```bash
# Migraciones
python manage.py migrate

# Crear usuario admin (puede hacer DELETE)
python manage.py createsuperuser

# Servidor de desarrollo
python manage.py runserver

# Redis (si no usas Docker)
docker run -p 6379:6379 redis:7-alpine

# Worker de Celery (Windows requiere --pool=solo)
celery -A isp_erp_backend worker -l info --pool=solo
# Linux/macOS
celery -A isp_erp_backend worker -l info

# Celery Beat (tarea periódica cada 5 min)
celery -A isp_erp_backend beat -l info

# Tests
pytest -v
```

## Docker (alternativa completa)

```bash
docker-compose up --build
```

Levanta Postgres, Redis, `web`, `celery_worker` y `celery_beat`.

## Cómo probar

1. Obtener token:
```bash
   curl -X POST http://127.0.0.1:8000/api/auth/token/ \
     -d "username=admin&password=<tu_password>"
```
2. Usar el token en cada request: header `Authorization: Token <token>`.
3. Ver `requests.http` para ejemplos completos de cada endpoint.
4. Para probar el proceso de cobranza sin esperar 5 minutos:
```bash
   python manage.py shell
```
```python
   from cobranza.tasks import procesar_morosidad
   procesar_morosidad()  # corre sincrónico, sin necesidad de worker activo
```
5. Healthcheck: `GET /api/health/` · Métricas: `GET /api/metrics/`.

## Endpoints

| Método | Endpoint | Auth |
|---|---|---|
| POST | `/api/auth/token/` | No |
| GET/POST | `/api/clientes/` | Sí (cualquier usuario autenticado) |
| GET/PATCH | `/api/clientes/{id}/` | Sí |
| DELETE | `/api/clientes/{id}/` | Sí, solo `is_staff` |
| GET/POST | `/api/lineas/` | Sí |
| GET/PATCH | `/api/lineas/{id}/` | Sí |
| DELETE | `/api/lineas/{id}/` | Sí, solo `is_staff` |
| GET | `/api/lineas/{id}/estado-cobranza/` | Sí |
| GET | `/api/health/` | No |
| GET | `/api/metrics/` | No |
