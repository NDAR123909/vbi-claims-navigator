"""Security utilities for PII/PHI handling and encryption."""
import re
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64
from app.core.config import settings


def get_encryption_key() -> bytes:
    """
    Get or generate encryption key from settings.

    Returns:
        Encryption key as bytes
    """
    key_str = settings.ENCRYPTION_KEY
    if len(key_str) < 32:
        # Pad or hash to 32 bytes
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'vbi_salt_2024',  # TODO: Use proper salt from config
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(key_str.encode()))
    else:
        # Use first 32 bytes
        return base64.urlsafe_b64encode(key_str[:32].encode().ljust(32, b'0')[:32])


def encrypt_field(value: str) -> str:
    """
    Encrypt a field value.

    Args:
        value: Plain text value to encrypt

    Returns:
        Encrypted string (base64)
    """
    if not value:
        return ""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted = f.encrypt(value.encode())
    return encrypted.decode()


def decrypt_field(encrypted_value: str) -> str:
    """
    Decrypt a field value.

    Args:
        encrypted_value: Encrypted string (base64)

    Returns:
        Decrypted plain text
    """
    if not encrypted_value:
        return ""
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_value.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"Error decrypting field: {e}")
        return "[DECRYPTION_ERROR]"


def mask_piis(text: str) -> str:
    """
    Mask PII in text for logging/display.

    Args:
        text: Text containing potential PII

    Returns:
        Text with PII masked
    """
    if not text:
        return text

    # Mask SSN (XXX-XX-XXXX)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', 'XXX-XX-XXXX', text)
    text = re.sub(r'\b\d{9}\b', 'XXXXXXXXX', text)

    # Mask email (keep domain visible)
    text = re.sub(r'\b([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b', r'***@\2', text)

    # Mask phone numbers
    text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', 'XXX-XXX-XXXX', text)
    text = re.sub(r'\b\(\d{3}\)\s?\d{3}-\d{4}\b', '(XXX) XXX-XXXX', text)

    # Mask credit card numbers (basic)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'XXXX-XXXX-XXXX-XXXX', text)

    return text


def mask_name(name: str) -> str:
    """
    Mask a name (show first letter, mask rest).

    Args:
        name: Name to mask

    Returns:
        Masked name (e.g., "John" -> "J***")
    """
    if not name or len(name) <= 1:
        return "***"
    return name[0] + "*" * (len(name) - 1)

