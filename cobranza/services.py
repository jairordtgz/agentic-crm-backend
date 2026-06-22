from dataclasses import dataclass
from decimal import Decimal
from django.db.models import Count, Sum
from django.utils import timezone
from linea.models import LineaServicio
from .models import CollectionsRequestLog, Rubro

ESTADOS_EXENTOS_SUSPENSION = (
    LineaServicio.EstadoLinea.CANCELADO,
    LineaServicio.EstadoLinea.NO_INSTALADO,
)


@dataclass
class ResultadoProcesoLinea:
    unpaid_count: int
    saldo_vencido: Decimal
    action_taken: str
    estado_linea_final: str


def _determinar_accion(linea: LineaServicio, unpaid_count: int) -> str:

    if linea.estado_linea in ESTADOS_EXENTOS_SUSPENSION:
        return CollectionsRequestLog.AccionTomada.NONE

    if unpaid_count > 0:
        if linea.estado_linea != LineaServicio.EstadoLinea.SUSPENDIDO:
            return CollectionsRequestLog.AccionTomada.SUSPEND
        return CollectionsRequestLog.AccionTomada.NONE  # ya estaba suspendida, sin cambio

    if linea.estado_linea == LineaServicio.EstadoLinea.SUSPENDIDO:
        return CollectionsRequestLog.AccionTomada.UNSUSPEND

    return CollectionsRequestLog.AccionTomada.NONE


class MorosidadService:

    def procesar_linea(self, linea: LineaServicio) -> ResultadoProcesoLinea:
        agregado = Rubro.objects.filter(
            linea_servicio=linea,
            estado_rubro=Rubro.EstadoRubro.NO_PAGADO,
            fecha_vencimiento__lt=timezone.now(),
        ).aggregate(cantidad=Count('id'), total=Sum('valor_total'))

        unpaid_count = agregado['cantidad'] or 0
        saldo_vencido = agregado['total'] or Decimal('0.00')

        action_taken = _determinar_accion(linea, unpaid_count)

        if action_taken == CollectionsRequestLog.AccionTomada.SUSPEND:
            linea.estado_linea = LineaServicio.EstadoLinea.SUSPENDIDO
        elif action_taken == CollectionsRequestLog.AccionTomada.UNSUSPEND:
            linea.estado_linea = LineaServicio.EstadoLinea.ACTIVO

        linea.saldo_vencido = saldo_vencido
        linea.save(update_fields=['estado_linea', 'saldo_vencido', 'modified_at'])

        return ResultadoProcesoLinea(
            unpaid_count=unpaid_count,
            saldo_vencido=saldo_vencido,
            action_taken=action_taken,
            estado_linea_final=linea.estado_linea,
        )