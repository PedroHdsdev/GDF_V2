# Security – Módulos de segurança

Pasta que concentra **decorators**, **validadores**, **middlewares** e utilitários de segurança do app GDF.

## Estrutura

| Módulo | Descrição |
|--------|-----------|
| **decorators.py** | `validate_idor_empresa`, `validate_idor_usuario`, `validate_session_required` – proteção IDOR e sessão em views |
| **password_validator.py** | `PasswordValidator`, `validate_password_strength` – requisitos e força de senha |
| **validators.py** | `InputValidator`, `validate_input`, `sanitize` – validação e sanitização de entrada (SQL/XSS) |
| **middlewares/** | |
| → security_headers.py | `SecurityHeadersMiddleware`, `XSSProtectionUtility` – headers XSS, clickjacking, HSTS; escape JS/HTML/URL |
| → rate_limit.py | `RateLimitMiddleware` – limite de requisições por IP/usuário |
| → session_fixation.py | `SessionFixationMiddleware`, `JWTTokenValidator`, `validate_jwt_required` – proteção de sessão e JWT |

## Uso

- **Views**: `from app.security.decorators import validate_idor_empresa, ...`
- **Senha**: `from app.security import PasswordValidator, validate_password_strength`
- **Entrada**: `from app.security import InputValidator, validate_input, sanitize`
- **Templates**: filtros em `app.templatetags.security` usam `XSSProtectionUtility` de `app.security.middlewares.security_headers`
- **Settings**: middlewares em `MIDDLEWARE` como `app.security.middlewares.*`
