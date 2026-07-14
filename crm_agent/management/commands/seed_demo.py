from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from crm_agent.models import Conversacion, Lead, Mensaje, TutorSesion


class Command(BaseCommand):
    help = 'Crea datos de prueba: usuario ejecutivo, leads, conversaciones y sesión de tutor.'

    def handle(self, *args, **options):
        ejecutivo, creado = User.objects.get_or_create(
            username='ejecutivo1', defaults={'is_staff': True},
        )
        if creado:
            ejecutivo.set_password('ejecutivo123')
            ejecutivo.save()
            self.stdout.write(self.style.SUCCESS('Usuario ejecutivo1 / ejecutivo123 creado.'))
        else:
            self.stdout.write('Usuario ejecutivo1 ya existía.')

        leads_data = [
            dict(tipo='B2C', nombre_contacto='María Torres', email='maria@example.com',
                 interes='Internet residencial 300MB', urgencia='ALTA',
                 etapa_embudo='NUEVO', prioridad_score=0, origen='chat_web'),
            dict(tipo='B2B', nombre_contacto='Constructora Andina S.A.', email='compras@andina.ec',
                 interes='Enlace dedicado + telefonía IP para 3 sucursales', urgencia='MEDIA',
                 etapa_embudo='CALIFICADO', prioridad_score=78, origen='chat_web'),
            dict(tipo='B2C', nombre_contacto='Jorge Salinas', email='jsalinas@example.com',
                 interes='Upgrade a fibra 500MB', urgencia='BAJA',
                 etapa_embudo='EN_NEGOCIACION', prioridad_score=55, origen='reactivacion_automatica'),
            dict(tipo='B2B', nombre_contacto='Distribuidora Litoral', email='it@litoral.ec',
                 interes='Redundancia de enlace principal', urgencia='ALTA',
                 etapa_embudo='CALIFICADO', prioridad_score=91, origen='chat_web'),
            dict(tipo='B2C', nombre_contacto='Ana Belén Ruiz', email='anab@example.com',
                 interes='Plan básico para departamento nuevo', urgencia='MEDIA',
                 etapa_embudo='GANADO', prioridad_score=60, origen='chat_web'),
        ]

        leads = []
        for data in leads_data:
            lead, _ = Lead.objects.get_or_create(email=data['email'], defaults=data)
            leads.append(lead)
        self.stdout.write(self.style.SUCCESS(f'{len(leads)} leads listos.'))

        conv1, _ = Conversacion.objects.get_or_create(
            lead=leads[0],
            defaults=dict(
                resumen='Necesita internet residencial de al menos 300MB, se muda en 2 semanas.',
                objeciones='Preguntó si hay descuento por pago anual.',
                siguiente_accion_sugerida='AGENDAR',
                estado_aprobacion='PENDIENTE',
                finalizada_en=timezone.now(),
            ),
        )
        Mensaje.objects.get_or_create(
            conversacion=conv1, emisor='LEAD',
            contenido='Hola, necesito internet para mi depa nuevo, algo rápido.',
        )
        Mensaje.objects.get_or_create(
            conversacion=conv1, emisor='AGENTE_IA',
            contenido='¡Con gusto! ¿Para cuántas personas y qué uso le darán?',
        )

        conv2, _ = Conversacion.objects.get_or_create(
            lead=leads[3],
            defaults=dict(
                resumen='Empresa con enlace único; requiere redundancia ante caídas frecuentes.',
                objeciones='Preocupados por el tiempo de instalación.',
                siguiente_accion_sugerida='DERIVAR_ESPECIALISTA',
                estado_aprobacion='APROBADA',
                aprobada_por=ejecutivo,
                finalizada_en=timezone.now() - timedelta(days=1),
            ),
        )
        Mensaje.objects.get_or_create(
            conversacion=conv2, emisor='LEAD',
            contenido='Se nos ha caído el internet 3 veces este mes, necesitamos respaldo urgente.',
        )

        TutorSesion.objects.get_or_create(
            tema_interes='Fondos indexados',
            defaults=dict(
                fuente_contenido='Futuro Academy - Guía de inversión pasiva',
                quiz_score=2,
                consentimiento_registrado=True,
                lead=leads[0],
            ),
        )

        self.stdout.write(self.style.SUCCESS('Datos de prueba creados correctamente.'))