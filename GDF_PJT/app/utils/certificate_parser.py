from dataclasses import dataclass
import re

from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID


@dataclass
class ParsedCertificate:
    not_valid_before: object
    not_valid_after: object
    issuer: str
    subject: str
    document: str
    serial_number: str


def _extract_document(subject: x509.Name) -> str:
    """Extrai CPF/CNPJ (somente digitos) do subject quando disponivel."""
    candidates = []
    for oid in (NameOID.SERIAL_NUMBER, NameOID.ORGANIZATION_NAME, NameOID.COMMON_NAME):
        for attr in subject.get_attributes_for_oid(oid):
            candidates.append(attr.value or "")

    candidates.append(subject.rfc4514_string())

    for text in candidates:
        if not text:
            continue
        cnpj = re.findall(r"\d{14}", text)
        if cnpj:
            return cnpj[0]
        cpf = re.findall(r"\d{11}", text)
        if cpf:
            return cpf[0]

    return ""


def _normalize_dt(cert, attr_utc: str, attr_legacy: str):
    if hasattr(cert, attr_utc):
        return getattr(cert, attr_utc)
    return getattr(cert, attr_legacy)


def _extract_preferred_name(name: x509.Name) -> str:
    """Retorna nome amigavel priorizando CN e, em seguida, Organization Name."""
    for oid in (NameOID.COMMON_NAME, NameOID.ORGANIZATION_NAME):
        attrs = name.get_attributes_for_oid(oid)
        if attrs and (attrs[0].value or "").strip():
            return attrs[0].value.strip()
    return name.rfc4514_string()


def load_certificate_metadata(raw_certificate: bytes, file_name: str = "", password: str = None) -> ParsedCertificate:
    """Carrega metadados de um certificado X.509 em PEM/DER ou PKCS#12 (.pfx/.p12)."""
    if not raw_certificate:
        raise ValueError("Arquivo de certificado vazio")

    cert_data = raw_certificate.strip()
    last_error = None
    cert = None

    file_name_l = (file_name or "").lower()
    if file_name_l.endswith((".pfx", ".p12")):
        pwd_bytes = password.encode("utf-8") if password else None
        try:
            _key, cert, _chain = pkcs12.load_key_and_certificates(cert_data, pwd_bytes)
        except Exception as exc:
            raise ValueError(
                "Nao foi possivel ler o arquivo .pfx/.p12. Verifique se a senha do certificado esta correta."
            ) from exc

        if cert is None:
            raise ValueError("Arquivo .pfx/.p12 sem certificado valido")

    if cert is None:
        for loader in (x509.load_pem_x509_certificate, x509.load_der_x509_certificate):
            try:
                cert = loader(cert_data)
                break
            except Exception as exc:
                last_error = exc
        else:
            raise ValueError(
                "Nao foi possivel ler o certificado enviado. Use um certificado X.509 valido (.crt, .txt, .pfx ou .p12)."
            ) from last_error

    not_valid_before = _normalize_dt(cert, "not_valid_before_utc", "not_valid_before")
    not_valid_after = _normalize_dt(cert, "not_valid_after_utc", "not_valid_after")

    return ParsedCertificate(
        not_valid_before=not_valid_before,
        not_valid_after=not_valid_after,
        issuer=_extract_preferred_name(cert.issuer),
        subject=_extract_preferred_name(cert.subject),
        document=_extract_document(cert.subject),
        serial_number=format(cert.serial_number, "X"),
    )