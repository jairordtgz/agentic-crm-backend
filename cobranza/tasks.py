from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from django.utils import timezone
from linea.models import LineaServicio
from .models import CollectionsRequestLog
from .services import MorosidadService

logger = get_task_logger(__name__)

@shared_task(
    name='cobranza.tasks.procesar_morosidad',
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
    soft_time_limit=480,
    time_limit=600,
)
def procesar_morosidad():

    servicio = MorosidadService()
    lineas = LineaServicio.objects.filter(is_active=True)

    procesadas, fallidas = 0, 0

    for linea in lineas:
        log = CollectionsRequestLog.objects.create(
            linea_servicio=linea,
            started_at=timezone.now(),
            status=CollectionsRequestLog.Status.FAILED,  # default seguro; se sobreescribe si todo va bien
        )
        try:
            with transaction.atomic():
                resultado = servicio.procesar_linea(linea)

            log.unpaid_count = resultado.unpaid_count
            log.action_taken = resultado.action_taken
            log.status = CollectionsRequestLog.Status.SUCCESS
            log.finished_at = timezone.now()
            log.save(update_fields=['unpaid_count', 'action_taken', 'status', 'finished_at'])
            procesadas += 1
            
            if resultado.action_taken == 'UNSUSPEND':
                from crm_agent.models import Lead
                Lead.objects.get_or_create(
                    cliente=linea.cliente,
                    etapa_embudo=Lead.EtapaEmbudo.NUEVO,
                    origen='reactivacion_automatica',
                    defaults={
                        'tipo': Lead.Tipo.B2C,
                        'nombre_contacto': linea.cliente.razon_social,
                        'interes': 'Reactivación de línea — posible upsell',
                    },
                )

        except Exception as exc:
            log.error_message = str(exc)
            log.finished_at = timezone.now()
            log.save(update_fields=['error_message', 'finished_at'])
            fallidas += 1
            logger.error('Error procesando línea %s: %s', linea.id, exc)

    logger.info('Morosidad procesada: %s ok, %s fallidas', procesadas, fallidas)
    return {'procesadas': procesadas, 'fallidas': fallidas}