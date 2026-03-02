import requests
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.db import transaction

from datos.models import UsuarioSlack, NotificacionInstanceSlack, NotificacionSlack

# DTOs
@dataclass
class SlackUser:
    id: str
    name: str
    real_name: str
    email: str


@dataclass
class SlackSendResult:
    success: bool
    sent: int
    failed: int
    errors: List[str]


# EXCEPCIÓN
class SlackAPIException(Exception):
    pass


# SERVICE UNIFICADO
class SlackService:

    def __init__(self, base_url: Optional[str] = None, timeout: int = 10):
        self.base_url = base_url or getattr(
            settings,
            "SLACK_API_BASE_URL",
            "http://gimpromed.com/app/api/slack/dm"
        )
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json"
        }

    # REQUEST BASE
    def _request(self, method: str, endpoint: str, payload=None):
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            if not data.get("success", False):
                raise SlackAPIException(f"Slack API error: {data}")

            return data

        except requests.exceptions.Timeout:
            raise SlackAPIException("Timeout al conectar con Slack API")

        except requests.exceptions.RequestException as e:
            raise SlackAPIException(f"Error HTTP: {str(e)}")

    # USERS
    def list_users(self) -> List[SlackUser]:
        data = self._request("GET", "/users/list")

        return [
            SlackUser(
                id=user.get("id"),
                name=user.get("name"),
                real_name=user.get("real_name"),
                email=user.get("email"),
            )
            for user in data.get("users", [])
        ]

    def get_user_by_email(self, email: str) -> Optional[SlackUser]:
        data = self._request("POST", "/user/get-by-email", {"email": email})

        user = data.get("user")
        if not user:
            return None

        return SlackUser(
            id=user.get("id"),
            name=user.get("name"),
            real_name=user.get("real_name"),
            email=user.get("email"),
        )

    # SYNC USERS (DB)
    @transaction.atomic
    def sync_users(self):

        slack_users = self.list_users()
        now = datetime.now()

        slack_user_ids = set()
        created = 0
        updated = 0

        for user in slack_users:
            slack_user_ids.add(user.id)

            obj, was_created = UsuarioSlack.objects.update_or_create(
                id=user.id,
                defaults={
                    "name": user.name,
                    "real_name": user.real_name,
                    "email": user.email,
                    "is_active": True,
                    "last_sync": now
                }
            )

            if was_created:
                created += 1
            else:
                updated += 1

        deactivated = UsuarioSlack.objects.exclude(
            id__in=slack_user_ids
        ).update(is_active=False)

        return {
            "created": created,
            "updated": updated,
            "deactivated": deactivated,
            "total_api": len(slack_users)
        }

    # MESSAGE BUILDER
    def build_message(
        self,
        title: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ) -> str:

        emoji_map = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }

        prefix = emoji_map.get(level, "")

        message = f"{prefix} *{title}*\n{body}"

        if metadata:
            message += "\n\n"
            for key, value in metadata.items():
                message += f"*{key}:* {value}\n"

        return message.strip()

    # SEND DM
    def send_dm(self, user_id: str, message: str):
        return self._request("POST", "/send", {
            "user_id": user_id,
            "message": message
        })
        
    # SEND GENERIC
    def send(
        self,
        recipients: List[str] | str,
        message: str,
        title: Optional[str] = None,
        level: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SlackSendResult:

        if not recipients:
            return SlackSendResult(False, 0, 0, ["No recipients"])

        # Normalizar recipients (string o lista)
        if isinstance(recipients, str):
            recipients_payload = recipients
        else:
            recipients_payload = list(set(recipients))  # evitar duplicados

        payload = {
            "recipients": recipients_payload,
            "message": message,
        }

        # Rich message (opcional)
        if title:
            payload["title"] = title

        if level:
            payload["type"] = level.lower()  # la API usa "error", "info", etc.

        if metadata:
            payload["additional_fields"] = metadata

        try:
            data = self._request("POST", "/send", payload)

            # =========================
            # RESPUESTA SIMPLE
            # =========================
            if "message" in data and "timestamp" in data:
                return SlackSendResult(
                    success=True,
                    sent=1,
                    failed=0,
                    errors=[]
                )

            # =========================
            # RESPUESTA MULTIPLE
            # =========================
            if "details" in data:
                errors = [
                    f"{d.get('email')}: {d.get('error')}"
                    for d in data.get("details", [])
                    if not d.get("success")
                ]

                return SlackSendResult(
                    success=data.get("successful", 0) > 0,
                    sent=data.get("successful", 0),
                    failed=data.get("failed", 0),
                    errors=errors
                )

            # fallback
            return SlackSendResult(True, 1, 0, [])

        except SlackAPIException as e:
            return SlackSendResult(False, 0, 1, [str(e)])

    # HELPER ALTO NIVEL
    def send_simple(
        self,
        recipients: List[str] | str,
        title: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ) -> SlackSendResult:

        return self.send(
            recipients=recipients,
            message=body,
            title=title,
            level=level,
            metadata=metadata
        )
        
    def send_from_instance(
        self, 
        instance: NotificacionInstanceSlack,     
    ) -> SlackSendResult:
        
        try:
            payload = instance.payload

            result = self.send(
                recipients=payload.get("recipients"),
                message=payload.get("message"),
                title=payload.get("title"),
                level=payload.get("type"),
                metadata=payload.get("additional_fields"),
            )
            
            instance.marcar_enviado()

            return result
        except Exception as e:
            instance.failed(err=str(e))
            return None


### utils
def noti_creacion_transferencia(n_transf_wms: str):
    noti = NotificacionSlack.objects.get(proceso='transf_pendiente')

    # Obtener correos desde relación M2M
    recipients = list(
        noti.usuarios.values_list('email', flat=True)
    )

    payload = {
        "recipients": recipients,
        "title": noti.titulo,
        "message": noti.mensaje,
        "type": noti.tipo_msg,
        "additional_fields": {
            "Proceso": "Transferencia",
            "# Transferencia WMS": n_transf_wms
        }
    }

    noti_instance = NotificacionInstanceSlack.objects.create(
        notificacion=noti,
        referencia_id=n_transf_wms,
        payload=payload,
        last_sent_at = datetime.now(),
        envios=0
    )

    return noti_instance


