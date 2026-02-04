"""
Password Validation & Requirements
Validação robusta de senhas com requisitos de segurança
"""

import re
from django.contrib.auth.password_validation import (
    validate_password as django_validate_password
)
from django.core.exceptions import ValidationError


class PasswordValidator:
    """
    Validador customizado de senhas
    Requisitos:
    - Mínimo 12 caracteres
    - Pelo menos uma letra maiúscula
    - Pelo menos uma letra minúscula
    - Pelo menos um número
    - Pelo menos um caractere especial
    """
    
    MIN_LENGTH = 12
    REQUIRED_SPECIAL_CHARS = r'!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    @staticmethod
    def validate(password, user=None):
        """
        Valida senha contra requisitos de segurança
        
        Args:
            password: String da senha
            user: User object (opcional, para validação contextual)
            
        Returns:
            dict: {'valid': bool, 'errors': [list de erros]}
        """
        errors = []
        
        # Validação básica
        if not password:
            errors.append('Senha é obrigatória')
            return {'valid': False, 'errors': errors}
        
        # Comprimento mínimo
        if len(password) < PasswordValidator.MIN_LENGTH:
            errors.append(
                f'Senha deve ter pelo menos {PasswordValidator.MIN_LENGTH} caracteres '
                f'(tem {len(password)})'
            )
        
        # Letra maiúscula
        if not re.search(r'[A-Z]', password):
            errors.append('Senha deve conter pelo menos uma letra MAIÚSCULA')
        
        # Letra minúscula
        if not re.search(r'[a-z]', password):
            errors.append('Senha deve conter pelo menos uma letra minúscula')
        
        # Número
        if not re.search(r'\d', password):
            errors.append('Senha deve conter pelo menos um número')
        
        # Caractere especial
        special_chars_pattern = '[' + re.escape(PasswordValidator.REQUIRED_SPECIAL_CHARS) + ']'
        if not re.search(special_chars_pattern, password):
            allowed = PasswordValidator.REQUIRED_SPECIAL_CHARS
            errors.append(f'Senha deve conter um caractere especial: {allowed}')
        
        # Verificar sequências simples
        if PasswordValidator._has_simple_sequence(password):
            errors.append('Senha contém sequência numérica ou alfabética óbvia')
        
        # Verificar padrões de teclado
        if PasswordValidator._has_keyboard_pattern(password):
            errors.append('Senha contém padrão de teclado óbvio (ex: qwerty, 123456)')
        
        # Usar validador do Django também
        try:
            if user:
                django_validate_password(password, user=user)
            else:
                django_validate_password(password)
        except ValidationError as e:
            errors.extend(e.messages)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': PasswordValidator.calculate_strength(password)
        }
    
    @staticmethod
    def _has_simple_sequence(password):
        """Detecta sequências simples (abc, 123, etc)"""
        # Verificar sequências numéricas
        if re.search(r'012|123|234|345|456|567|678|789|890', password):
            return True
        
        # Verificar sequências alfabéticas
        if re.search(r'abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz', password, re.IGNORECASE):
            return True
        
        return False
    
    @staticmethod
    def _has_keyboard_pattern(password):
        """Detecta padrões de teclado"""
        keyboard_patterns = [
            'qwerty', 'qwertz', 'azerty',
            '123456', '654321', '111111', '222222',
            'password', 'pass123', 'admin', 'letmein',
        ]
        
        password_lower = password.lower()
        for pattern in keyboard_patterns:
            if pattern in password_lower:
                return True
        
        return False
    
    @staticmethod
    def calculate_strength(password):
        """
        Calcula força da senha de 0-100
        """
        strength = 0
        
        # Comprimento (40 pontos)
        length = len(password)
        if length >= 12:
            strength += 10
        if length >= 16:
            strength += 10
        if length >= 20:
            strength += 20
        
        # Variedade de caracteres (40 pontos)
        if re.search(r'[a-z]', password):
            strength += 10
        if re.search(r'[A-Z]', password):
            strength += 10
        if re.search(r'\d', password):
            strength += 10
        if re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            strength += 10
        
        # Sem padrões óbvios (20 pontos)
        if not PasswordValidator._has_simple_sequence(password):
            strength += 10
        if not PasswordValidator._has_keyboard_pattern(password):
            strength += 10
        
        return min(100, strength)
    
    @staticmethod
    def get_strength_label(strength):
        """Retorna label da força da senha"""
        if strength < 40:
            return 'Muito Fraca ❌'
        elif strength < 60:
            return 'Fraca ⚠️'
        elif strength < 80:
            return 'Boa ✓'
        else:
            return 'Excelente ✅'


def validate_password_strength(password, user=None):
    """
    Atalho para validar senha
    Levanta ValidationError se inválida
    """
    result = PasswordValidator.validate(password, user)
    if not result['valid']:
        raise ValidationError(result['errors'])
    return result
