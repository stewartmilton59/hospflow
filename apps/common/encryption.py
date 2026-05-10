"""AES-256-GCM Field-Level Encryption for PHI"""
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class FieldEncryption:
    """AES-256-GCM encryption for sensitive PHI fields"""

    def __init__(self):
        key = getattr(settings, "FIELD_ENCRYPTION_KEY", None)
        if not key:
            raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY must be set in settings")

        if isinstance(key, str):
            key = base64.b64decode(key)

        if len(key) != 32:
            raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY must be 32 bytes (256 bits)")

        self.aesgcm = AESGCM(key)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""

        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        # Store nonce + ciphertext, base64 encoded
        encrypted = base64.b64encode(nonce + ciphertext).decode("utf-8")
        return encrypted

    def decrypt(self, encrypted: str) -> str:
        if not encrypted:
            return ""

        try:
            data = base64.b64decode(encrypted.encode("utf-8"))
            nonce = data[:12]
            ciphertext = data[12:]
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except Exception:
            return ""


# Singleton instance
_encryption = None

def get_encryption():
    global _encryption
    if _encryption is None:
        _encryption = FieldEncryption()
    return _encryption
