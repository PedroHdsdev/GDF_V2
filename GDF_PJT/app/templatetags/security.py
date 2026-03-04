"""
Custom template tags para segurança
"""

from django import template
from django.middleware.csrf import get_token
from django.utils.html import escape
from django.utils.safestring import mark_safe
from app.middlewares.security_headers import XSSProtectionUtility

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
