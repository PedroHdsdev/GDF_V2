from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _build_fernet_key() -> bytes:
    """
    Exige chave explicita em CERT_PASSWORD_FERNET_KEY.
    """
    explicit_key = (getattr(settings, "CERT_PASSWORD_FERNET_KEY", "") or "").strip()
    if not explicit_key:
        raise ValueError("CERT_PASSWORD_FERNET_KEY nao configurada")
    return explicit_key.encode("utf-8")


def validate_fernet_key() -> None:
    """Valida no startup se a chave Fernet está configurada e no formato correto."""
    key = _build_fernet_key()
    try:
        Fernet(key)
    except Exception as exc:
        raise ValueError("CERT_PASSWORD_FERNET_KEY invalida") from exc


def encrypt_cert_password(raw_password: str) -> str:
    if raw_password is None:
        return None
    value = str(raw_password)
    if value == "":
        return None

    token = Fernet(_build_fernet_key()).encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_cert_password(encrypted_password: str) -> str:
    if encrypted_password is None:
        return None

    token = str(encrypted_password)
    if token == "":
        return None

    try:
        data = Fernet(_build_fernet_key()).decrypt(token.encode("utf-8"))
        return data.decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Nao foi possivel descriptografar a senha do certificado") from exc