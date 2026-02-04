"""
Input Validation & Sanitization
Proteção contra SQL Injection, XSS, e ataques de entrada
"""

from django.core.exceptions import ValidationError
from django.utils.html import escape
import re


class InputValidator:
    """Validar e sanitizar entradas do usuário"""
    
    # Padrões permitidos
    PATTERNS = {
        'alphanumeric': r'^[a-zA-Z0-9_\-\.]+$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^[\d\-\(\)\s\+]+$',
        'cnpj': r'^\d{14}$',
        'cpf': r'^\d{11}$',
        'url': r'^https?://[^\s/$.?#].[^\s]*$',
    }
    
    MAX_LENGTHS = {
        'username': 150,
        'email': 254,
        'phone': 20,
        'cnpj': 14,
        'cpf': 11,
        'razao_social': 200,
        'fantasia': 200,
        'street': 200,
        'number': 10,
        'complement': 100,
        'city': 100,
        'state': 2,
        'zip': 10,
        'search': 100,
    }
    
    @staticmethod
    def validate_and_sanitize(value, field_type, max_length=None):
        """
        Valida e sanitiza entrada
        
        Args:
            value: Valor a ser validado
            field_type: Tipo de campo ('email', 'phone', 'cnpj', 'search', etc)
            max_length: Comprimento máximo (default: do tipo)
            
        Returns:
            Valor sanitizado
            
        Raises:
            ValidationError: Se inválido
        """
        if not value:
            return ''
        
        # Converter para string e remover whitespace
        value = str(value).strip()
        
        # Determinar max_length
        if max_length is None:
            max_length = InputValidator.MAX_LENGTHS.get(field_type, 100)
        
        # Verificar comprimento
        if len(value) > max_length:
            raise ValidationError(
                f"{field_type} não pode ter mais de {max_length} caracteres"
            )
        
        # Validar contra padrão específico
        if field_type in InputValidator.PATTERNS:
            pattern = InputValidator.PATTERNS[field_type]
            if not re.match(pattern, value):
                raise ValidationError(f"{field_type} contém caracteres inválidos")
        
        # Remover caracteres perigosos
        dangerous_patterns = [
            r'[<>"`\'%;()&\+]',  # Caracteres SQL/XSS perigosos
            r'--',                # SQL comment
            r'\/\*.*?\*\/',       # SQL comment block
            r'union\s+select',    # SQL injection comum
            r'drop\s+table',      # SQL injection
            r'insert\s+into',     # SQL injection
            r'delete\s+from',     # SQL injection
            r'update\s+',         # SQL injection
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(f"Conteúdo inválido em {field_type}")
        
        # Escape para XSS
        value = escape(value)
        
        return value
    
    @staticmethod
    def validate_cnpj(cnpj_value):
        """Valida CNPJ"""
        cnpj = re.sub(r'\D', '', cnpj_value)
        
        if len(cnpj) != 14:
            raise ValidationError("CNPJ deve ter 14 dígitos")
        
        if cnpj == cnpj[0] * 14:  # Todos iguais
            raise ValidationError("CNPJ inválido")
        
        # Verificar dígito verificador (simplificado)
        return cnpj
    
    @staticmethod
    def validate_email(email_value):
        """Valida email"""
        if not re.match(InputValidator.PATTERNS['email'], email_value):
            raise ValidationError("Email inválido")
        if len(email_value) > InputValidator.MAX_LENGTHS['email']:
            raise ValidationError("Email muito longo")
        return email_value
    
    @staticmethod
    def validate_search_query(query, max_length=100):
        """Valida query de busca - permite mais caracteres que otros campos"""
        if not query:
            return ''
        
        query = str(query).strip()
        
        if len(query) > max_length:
            raise ValidationError(f"Busca não pode ter mais de {max_length} caracteres")
        
        # Remover SQL injection attempts
        dangerous = ['--', '/*', '*/', 'union', 'select', 'drop', 'insert', 'delete', 'update']
        query_lower = query.lower()
        for danger in dangerous:
            if danger in query_lower:
                raise ValidationError(f"Query contém comando SQL: {danger}")
        
        # Escape básico
        query = escape(query)
        
        return query


# Helper functions
def validate_input(value, field_type, max_length=None):
    """Atalho para validar entrada"""
    return InputValidator.validate_and_sanitize(value, field_type, max_length)


def sanitize(value):
    """Sanitiza valor para XSS"""
    return escape(str(value))
