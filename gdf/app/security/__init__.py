"""
Módulos de segurança do app GDF.
- decorators: validação IDOR e sessão em views
- password_validator: requisitos e força de senha
- validators: sanitização e validação de entrada (SQL/XSS)
- middlewares: headers de segurança, rate limit, session fixation
"""
from app.security.decorators import (
    validate_idor_empresa,
    validate_idor_usuario,
    validate_session_required,
)
from app.security.password_validator import (
    PasswordValidator,
    validate_password_strength,
)
from app.security.validators import (
    InputValidator,
    sanitize,
    validate_input,
)

__all__ = [
    "validate_idor_empresa",
    "validate_idor_usuario",
    "validate_session_required",
    "PasswordValidator",
    "validate_password_strength",
    "InputValidator",
    "validate_input",
    "sanitize",
]
