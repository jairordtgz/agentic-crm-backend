import pytest
from rest_framework.test import APIClient

from cliente.models import Cliente
from linea.models import LineaServicio

from .models import Conversacion, Lead


@pytest.fixture
def lead(db):
    return Lead.objects.create(tipo='B2C', nombre_contacto='Prospecto Test')


@pytest.mark.django_db
class TestLeadChat:
    def test_chat_crea_conversacion_y_mensajes(self, mocker, lead):
        mocker.patch(
            'crm_agent.services.gemini_client.responder_chat',
            return_value='¿Buscas una línea nueva o un upgrade?',
        )
        client = APIClient()
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='u1', password='p1')
        client.force_authenticate(user=user)

        response = client.post(f'/api/crm/leads/{lead.id}/chat/', {'mensaje': 'Hola, quiero info'})

        assert response.status_code == 200
        assert response.data['respuesta'] == '¿Buscas una línea nueva o un upgrade?'
        assert lead.conversaciones.count() == 1
        assert lead.conversaciones.first().mensajes.count() == 2

    def test_chat_rechaza_mensaje_vacio(self, lead):
        client = APIClient()
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='u2', password='p2')
        client.force_authenticate(user=user)

        response = client.post(f'/api/crm/leads/{lead.id}/chat/', {'mensaje': ''})
        assert response.status_code == 400


@pytest.mark.django_db
class TestConversacionCerrar:
    def test_cerrar_califica_lead(self, mocker, lead):
        conversacion = Conversacion.objects.create(lead=lead)
        mocker.patch(
            'crm_agent.services.gemini_client.calificar_lead',
            return_value={
                'prioridad_score': 80, 'urgencia': 'ALTA',
                'resumen_necesidad': 'Necesita 3 líneas nuevas',
                'objeciones': 'Precio', 'siguiente_accion_sugerida': 'AGENDAR',
            },
        )
        client = APIClient()
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='u3', password='p3')
        client.force_authenticate(user=user)

        response = client.post(f'/api/crm/conversaciones/{conversacion.id}/cerrar/')

        assert response.status_code == 200
        lead.refresh_from_db()
        assert lead.prioridad_score == 80
        assert lead.etapa_embudo == 'CALIFICADO'