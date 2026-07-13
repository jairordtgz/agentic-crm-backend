from django.conf import settings
from django.db import models

from cliente.models import Cliente
from core.models import Auditoria
from linea.models import LineaServicio


class Lead(Auditoria):
    class Tipo(models.TextChoices):
        B2B = 'B2B', 'B2B'
        B2C = 'B2C', 'B2C'

    class EtapaEmbudo(models.TextChoices):
        NUEVO = 'NUEVO', 'Nuevo'
        CALIFICADO = 'CALIFICADO', 'Calificado'
        EN_NEGOCIACION = 'EN_NEGOCIACION', 'En negociación'
        GANADO = 'GANADO', 'Ganado'
        PERDIDO = 'PERDIDO', 'Perdido'

    class Urgencia(models.TextChoices):
        BAJA = 'BAJA', 'Baja'
        MEDIA = 'MEDIA', 'Media'
        ALTA = 'ALTA', 'Alta'

    cliente = models.ForeignKey(
        Cliente, null=True, blank=True, on_delete=models.SET_NULL, related_name='leads',
    )
    tipo = models.CharField(max_length=3, choices=Tipo.choices)
    nombre_contacto = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    interes = models.CharField(max_length=255, blank=True)
    presupuesto_estimado = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    urgencia = models.CharField(max_length=5, choices=Urgencia.choices, default=Urgencia.MEDIA)
    prioridad_score = models.PositiveSmallIntegerField(default=0)
    etapa_embudo = models.CharField(
        max_length=20, choices=EtapaEmbudo.choices, default=EtapaEmbudo.NUEVO,
    )
    origen = models.CharField(max_length=30, default='chat_web')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.nombre_contacto} ({self.tipo}) - {self.etapa_embudo}'


class Oportunidad(models.Model):
    class Estado(models.TextChoices):
        ABIERTA = 'ABIERTA', 'Abierta'
        GANADA = 'GANADA', 'Ganada'
        PERDIDA = 'PERDIDA', 'Perdida'

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='oportunidades')
    linea_servicio = models.ForeignKey(
        LineaServicio, null=True, blank=True, on_delete=models.SET_NULL,
    )
    descripcion = models.CharField(max_length=255)
    valor_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.ABIERTA)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.descripcion} - {self.estado}'


class Conversacion(models.Model):
    class AccionSugerida(models.TextChoices):
        AGENDAR = 'AGENDAR', 'Agendar reunión'
        ENVIAR_MATERIAL = 'ENVIAR_MATERIAL', 'Enviar material educativo'
        DERIVAR_ESPECIALISTA = 'DERIVAR_ESPECIALISTA', 'Derivar a especialista'
        NONE = 'NONE', 'Sin acción'

    class EstadoAprobacion(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        APROBADA = 'APROBADA', 'Aprobada'
        EDITADA = 'EDITADA', 'Editada'
        RECHAZADA = 'RECHAZADA', 'Rechazada'

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='conversaciones')
    canal = models.CharField(max_length=20, default='web_chat')
    iniciada_en = models.DateTimeField(auto_now_add=True)
    finalizada_en = models.DateTimeField(null=True, blank=True)
    resumen = models.TextField(blank=True)
    objeciones = models.TextField(blank=True)
    siguiente_accion_sugerida = models.CharField(
        max_length=25, choices=AccionSugerida.choices, default=AccionSugerida.NONE,
    )
    estado_aprobacion = models.CharField(
        max_length=10, choices=EstadoAprobacion.choices, default=EstadoAprobacion.PENDIENTE,
    )
    aprobada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f'Conversación {self.id} - lead {self.lead_id}'


class Mensaje(models.Model):
    class Emisor(models.TextChoices):
        LEAD = 'LEAD', 'Lead'
        AGENTE_IA = 'AGENTE_IA', 'Agente IA'
        EJECUTIVO = 'EJECUTIVO', 'Ejecutivo'

    conversacion = models.ForeignKey(
        Conversacion, on_delete=models.CASCADE, related_name='mensajes',
    )
    emisor = models.CharField(max_length=10, choices=Emisor.choices)
    contenido = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']


class TutorSesion(models.Model):
    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL)
    tema_interes = models.CharField(max_length=150)
    fuente_contenido = models.CharField(max_length=255, blank=True)
    quiz_score = models.PositiveSmallIntegerField(null=True, blank=True)
    consentimiento_registrado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)