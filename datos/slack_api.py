import requests
from typing import List, Optional
from django.conf import settings
from django.db import transaction
from dataclasses import dataclass
from datetime import datetime
from datos.models import UsuarioSlack

# DTOs
@dataclass
class SlackUser:
    id: str
    name: str
    real_name: str
    email: str

# EXCEPCIÓN
class SlackAPIException(Exception):
    pass


# CLIENTE
class SlackUserClient:

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
    
    # MÉTODO BASE
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

    # ENDPOINTS
    def list_users(self) -> List[SlackUser]:
        """
        GET /users/list
        """

        data = self._request("GET", "/users/list")

        users = data.get("users", [])

        return [
            SlackUser(
                id=user.get("id"),
                name=user.get("name"),
                real_name=user.get("real_name"),
                email=user.get("email"),
            )
            for user in users
        ]

    def get_user_by_email(self, email: str) -> Optional[SlackUser]:
        """
        POST /user/get-by-email
        """

        payload = {"email": email}

        data = self._request("POST", "/user/get-by-email", payload)

        user = data.get("user")

        if not user:
            return None

        return SlackUser(
            id=user.get("id"),
            name=user.get("name"),
            real_name=user.get("real_name"),
            email=user.get("email"),
        )


class SlackUserSyncService:

    def __init__(self):
        self.client = SlackUserClient()

    @transaction.atomic
    def sync_users(self):

        slack_users = self.client.list_users()

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

        # Soft delete (muy importante)
        deactivated = UsuarioSlack.objects.exclude(
            id__in=slack_user_ids
        ).update(is_active=False)

        return {
            "created": created,
            "updated": updated,
            "deactivated": deactivated,
            "total_api": len(slack_users)
        }