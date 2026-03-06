"""
Input Validation & Sanitization
Proteção contra SQL Injection, XSS, e ataques de entrada
"""

import re
from django.core.exceptions import ValidationError
from django.utils.html import escape


class InputValidator:
    """Validar e sanitizar entradas do usuário"""

    PATTERNS = {
        "alphanumeric": r"^[a-zA-Z0-9_\-\.]+$",
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone": r"^[\d\-\(\)\s\+]+$",
        "cnpj": r"^\d{14}$",
        "cpf": r"^\d{11}$",
        "url": r"^https?://[^\s/$.?#].[^\s]*$",
    }
    MAX_LENGTHS = {
        "username": 150,
        "email": 254,
        "phone": 20,
        "cnpj": 14,
        "cpf": 11,
        "razao_social": 200,
        "fantasia": 200,
        "street": 200,
        "number": 10,
        "complement": 100,
        "city": 100,
        "state": 2,
        "zip": 10,
        "search": 100,
    }

    @staticmethod
    def validate_and_sanitize(value, field_type, max_length=None):
        if not value:
            return ""
        value = str(value).strip()
        if max_length is None:
            max_length = InputValidator.MAX_LENGTHS.get(field_type, 100)
        if len(value) > max_length:
            raise ValidationError(f"{field_type} não pode ter mais de {max_length} caracteres")
        if field_type in InputValidator.PATTERNS:
            pattern = InputValidator.PATTERNS[field_type]
            if not re.match(pattern, value):
                raise ValidationError(f"{field_type} contém caracteres inválidos")
        dangerous_patterns = [
            r'[<>"`\'%;()&\+]',
            r"--",
            r"\/\*.*?\*\/",
            r"union\s+select",
            r"drop\s+table",
            r"insert\s+into",
            r"delete\s+from",
            r"update\s+",
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(f"Conteúdo inválido em {field_type}")
        value = escape(value)
        return value

    @staticmethod
    def validate_cnpj(cnpj_value):
        cnpj = re.sub(r"\D", "", cnpj_value)
        if len(cnpj) != 14:
            raise ValidationError("CNPJ deve ter 14 dígitos")
        if cnpj == cnpj[0] * 14:
            raise ValidationError("CNPJ inválido")
        return cnpj

    @staticmethod
    def validate_email(email_value):
        if not re.match(InputValidator.PATTERNS["email"], email_value):
            raise ValidationError("Email inválido")
        if len(email_value) > InputValidator.MAX_LENGTHS["email"]:
            raise ValidationError("Email muito longo")
        return email_value

    @staticmethod
    def validate_search_query(query, max_length=100):
        if not query:
            return ""
        query = str(query).strip()
        if len(query) > max_length:
            raise ValidationError(f"Busca não pode ter mais de {max_length} caracteres")
        dangerous = ["--", "/*", "*/", "union", "select", "drop", "insert", "delete", "update"]
        query_lower = query.lower()
        for danger in dangerous:
            if danger in query_lower:
                raise ValidationError(f"Query contém comando SQL: {danger}")
        query = escape(query)
        return query


def validate_input(value, field_type, max_length=None):
    return InputValidator.validate_and_sanitize(value, field_type, max_length)


def sanitize(value):
    return escape(str(value))
