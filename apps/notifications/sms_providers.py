"""Tanzanian SMS Gateway Providers"""
import os
import requests
from typing import Dict, List
from django.conf import settings


class BaseSMSProvider:
    """Base class for SMS providers"""

    def __init__(self):
        self.api_key = settings.SMS_API_KEY
        self.api_secret = getattr(settings, "SMS_API_SECRET", "")
        self.sender_id = settings.SMS_SENDER_ID

    def send_sms(self, phone: str, message: str) -> Dict:
        raise NotImplementedError

    def send_bulk(self, phones: List[str], message: str) -> Dict:
        results = []
        for phone in phones:
            results.append(self.send_sms(phone, message))
        return {"results": results}


class NotifyAfricaProvider(BaseSMSProvider):
    """
    Notify Africa - Best for Startups & All-round
    24ms latency; localized Swahili support
    """
    BASE_URL = "https://api.notifyafrica.com/v1"

    def send_sms(self, phone: str, message: str) -> Dict:
        payload = {
            "api_key": self.api_key,
            "sender_id": self.sender_id,
            "to": self._format_phone(phone),
            "message": message,
            "language": "sw" if self._is_swahili(message) else "en"
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/sms/send",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": data.get("status") == "success",
                "message_id": data.get("message_id"),
                "provider": "notify_africa",
                "response": data
            }
        except requests.RequestException as e:
            return {"success": False, "error": str(e), "provider": "notify_africa"}

    def _format_phone(self, phone: str) -> str:
        """Ensure 255 format"""
        phone = phone.replace("+", "").replace(" ", "")
        if phone.startswith("0"):
            phone = "255" + phone[1:]
        return phone

    def _is_swahili(self, message: str) -> bool:
        swahili_words = ["habari", "asante", "tafadhali", "karibu", "pole"]
        return any(word in message.lower() for word in swahili_words)


class BeemAfricaProvider(BaseSMSProvider):
    """
    Beem Africa - Best for Enterprises
    Omnichannel API (SMS, USSD, WhatsApp)
    """
    BASE_URL = "https://apisms.beem.africa/v1"

    def send_sms(self, phone: str, message: str) -> Dict:
        payload = {
            "source_addr": self.sender_id,
            "encoding": 0,
            "schedule_time": "",
            "message": message,
            "recipients": [
                {"recipient_id": 1, "dest_addr": self._format_phone(phone)}
            ]
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/send",
                json=payload,
                auth=(self.api_key, self.api_secret),
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": data.get("successful"),
                "message_id": data.get("request_id"),
                "provider": "beem_africa",
                "response": data
            }
        except requests.RequestException as e:
            return {"success": False, "error": str(e), "provider": "beem_africa"}

    def _format_phone(self, phone: str) -> str:
        phone = phone.replace("+", "").replace(" ", "")
        if phone.startswith("0"):
            phone = "255" + phone[1:]
        return phone


class FastHubProvider(BaseSMSProvider):
    """
    FastHub - Best for Developers
    TCRA compliant; detailed delivery tracking
    """
    BASE_URL = "https://api.fasthub.co.tz/v1"

    def send_sms(self, phone: str, message: str) -> Dict:
        payload = {
            "api_key": self.api_key,
            "from": self.sender_id,
            "to": self._format_phone(phone),
            "text": message,
            "dlr": 1,  # Delivery receipt
            "dlr_url": f"{settings.ALLOWED_HOSTS[0]}/api/notifications/dlr/"
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/sms",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": data.get("code") == 200,
                "message_id": data.get("message_id"),
                "provider": "fasthub",
                "response": data
            }
        except requests.RequestException as e:
            return {"success": False, "error": str(e), "provider": "fasthub"}

    def _format_phone(self, phone: str) -> str:
        phone = phone.replace("+", "").replace(" ", "")
        if phone.startswith("0"):
            phone = "255" + phone[1:]
        return phone


class SMSFactory:
    """Factory to get configured SMS provider"""

    PROVIDERS = {
        "notify_africa": NotifyAfricaProvider,
        "beem_africa": BeemAfricaProvider,
        "fasthub": FastHubProvider,
    }

    @classmethod
    def get_provider(cls, provider_name: str = None):
        provider_name = provider_name or settings.SMS_PROVIDER
        provider_class = cls.PROVIDERS.get(provider_name, NotifyAfricaProvider)
        return provider_class()
