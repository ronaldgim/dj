import requests
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.db import transaction

from datos.models import UsuarioSlack

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
        recipients: List[str],
        message: str
    ) -> SlackSendResult:

        if not recipients:
            return SlackSendResult(False, 0, 0, ["No recipients"])

        sent = 0
        failed = 0
        errors = []

        for user_id in recipients:
            try:
                self.send_dm(user_id, message)
                sent += 1
            except SlackAPIException as e:
                failed += 1
                errors.append(f"{user_id}: {str(e)}")

        return SlackSendResult(
            success=sent > 0,
            sent=sent,
            failed=failed,
            errors=errors
        )

    # HELPER ALTO NIVEL
    def send_simple(
        self,
        recipients: List[str],
        title: str,
        body: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO"
    ) -> SlackSendResult:

        message = self.build_message(title, body, metadata, level)

        return self.send(recipients, message)