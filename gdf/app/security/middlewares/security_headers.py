"""
XSS Protection & Security Headers
Adiciona headers de segurança contra XSS, clickjacking, MIME sniffing
"""

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adiciona headers de segurança em todas as responses
    Proteção contra: XSS, Clickjacking, MIME sniffing, etc
    """

    def process_response(self, request, response):
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "SAMEORIGIN"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Apenas features reconhecidas pelos navegadores atuais (evita erros no console)
        response["Permissions-Policy"] = (
            "accelerometer=(), autoplay=(), camera=(), display-capture=(), "
            "encrypted-media=(), fullscreen=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), midi=(), payment=(), "
            "picture-in-picture=(), publickey-credentials-get=(), usb=()"
        )
        frame_sources = getattr(
            settings,
            "STREAMLIT_FRAME_ORIGINS",
            [
                "https://homo.processit.com.br",
                "https://localhost:8600",
                "https://127.0.0.1:8600",
            ],
        )
        response["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        return response


class XSSProtectionUtility:
    """Utilitário para escape seguro em templates"""

    @staticmethod
    def escape_html(text):
        from django.utils.html import escape
        return escape(text)

    @staticmethod
    def escape_js(text):
        if not text:
            return ""
        text = str(text)
        replacements = {
            "\\": "\\\\",
            '"': '\\"',
            "'": "\\'",
            "<": "\\x3c",
            ">": "\\x3e",
            "\n": "\\n",
            "\r": "\\r",
            "\t": "\\t",
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    @staticmethod
    def escape_url(url):
        if not url:
            return ""
        url = str(url).strip()
        if url.lower().startswith(("javascript:", "data:", "vbscript:")):
            return ""
        return url

    @staticmethod
    def sanitize_html(html, allowed_tags=None):
        try:
            import bleach
            if allowed_tags is None:
                allowed_tags = {
                    "p": [], "br": [], "strong": [], "em": [], "u": [],
                    "a": ["href", "title"], "ul": [], "ol": [], "li": [],
                }
            allowed_attributes = {"a": ["href", "title", "target"], "img": ["src", "alt", "title"]}
            return bleach.clean(
                html,
                tags=list(allowed_tags.keys()),
                attributes=allowed_attributes,
                strip=True,
            )
        except ImportError:
            from django.utils.html import escape
            return escape(html)
