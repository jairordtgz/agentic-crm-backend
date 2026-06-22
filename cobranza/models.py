from django.db import models

from core.models import Auditoria
from linea.models import LineaServicio

class Rubro(Auditoria):
    class EstadoRubro(models.TextChoices):
        NO_PAGADO = 'NO_PAGADO', 'No pagado'
        PAGADO = 'PAGADO', 'Pagado'
        VENCIDO = 'VENCIDO', 'Vencido'
        ANULADO = 'ANULADO', 'Anulado'

    linea_servicio = models.ForeignKey(
        LineaServicio, on_delete=models.PROTECT, related_name='rubros'
    )
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    estado_rubro = models.CharField(
        max_length=20, choices=EstadoRubro.choices, default=EstadoRubro.NO_PAGADO
    )
    fecha_emision = models.DateTimeField()
    fecha_vencimiento = models.DateTimeField()
    fecha_pago = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_vencimiento']

    def __str__(self):
        return f'Rubro {self.id} - línea {self.linea_servicio_id} - {self.estado_rubro}'


class CollectionsRequestLog(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Éxito'
        FAILED = 'FAILED', 'Fallido'

    class AccionTomada(models.TextChoices):
        NONE = 'NONE', 'Sin acción'
        SUSPEND = 'SUSPEND', 'Suspendida'
        UNSUSPEND = 'UNSUSPEND', 'Reactivada'

    linea_servicio = models.ForeignKey(
        LineaServicio, on_delete=models.PROTECT, related_name='logs_cobranza'
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices)
    unpaid_count = models.PositiveSmallIntegerField(default=0)
    action_taken = models.CharField(
        max_length=10, choices=AccionTomada.choices, default=AccionTomada.NONE
    )
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'Log línea {self.linea_servicio_id} - {self.status} - {self.started_at}'