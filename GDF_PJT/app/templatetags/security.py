"""
Custom template tags para segurança
"""

from django import template
from django.middleware.csrf import get_token
from django.utils.html import escape, json_script as django_json_script
from django.utils.safestring import mark_safe
from app.security.middlewares.security_headers import XSSProtectionUtility

register = template.Library()


@register.filter(name='escapejs')
def escapejs_filter(value):
    """Escape valor para uso em JavaScript"""
    return XSSProtectionUtility.escape_js(value)


@register.filter(name='escape_url')
def escape_url_filter(value):
    """Escape URL para prevenir javascript: protocol"""
    return XSSProtectionUtility.escape_url(value)


@register.filter(name='safe_html')
def safe_html_filter(value):
    """Sanitiza HTML removendo tags perigosas"""
    return mark_safe(XSSProtectionUtility.sanitize_html(value))


@register.simple_tag(takes_context=True)
def csrf_token_value(context):
    """Retorna o valor do token CSRF para uso em meta tags ou JS."""
    request = context.get('request')
    if request:
        return get_token(request)
    return ''


@register.filter(name='truncate_safe')
def truncate_safe_filter(value, length=100):
    """Trunca string com segurança"""
    value_str = str(value)
    if len(value_str) > length:
        value_str = value_str[:length] + '...'
    return escape(value_str)


def _json_script_coerce_keys(obj):
    """
    Garante chaves de dict serializáveis em JSON (str/int/float/bool/None).
    Evita TypeError em json.dumps (ex.: Decimal ou UUID como chave vindo do ORM).
    """
    if isinstance(obj, dict):
        return {str(k): _json_script_coerce_keys(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_script_coerce_keys(x) for x in obj]
    return obj


@register.simple_tag(takes_context=True, name="json_script_nonce")
def json_script_with_nonce(context, data, element_id):
    """
    Mesmo que o filtro |json_script do Django, com atributo nonce para CSP (script sem unsafe-inline).
    O nonce é obtido de request.csp_nonce (django-csp).
    """
    data = _json_script_coerce_keys(data)
    html = django_json_script(data, element_id)
    request = context.get("request")
    if not request or not hasattr(request, "csp_nonce"):
        return html
    # request.csp_nonce é CheckableLazyObject: bool(nonce) é False até avaliar — forçar str().
    try:
        nonce_val = str(request.csp_nonce)
    except Exception:
        return html
    if not nonce_val:
        return html
    s = str(html)
    s = s.replace("<script", '<script nonce="' + escape(nonce_val) + '"', 1)
    return mark_safe(s)
