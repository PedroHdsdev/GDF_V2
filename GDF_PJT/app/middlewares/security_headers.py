"""
XSS Protection & Security Headers
Adiciona headers de segurança contra XSS, clickjacking, MIME sniffing
"""

from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adiciona headers de segurança em todas as responses
    Proteção contra: XSS, Clickjacking, MIME sniffing, etc
    """
    
    def process_response(self, request, response):
        # X-Content-Type-Options: Previne MIME sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options: Clickjacking protection
        response['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection: XSS filter (legacy, mas ainda útil)
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy: Limitar informação de referrer
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy: Limitar features do navegador
        response['Permissions-Policy'] = (
            'accelerometer=(), ambient-light-sensor=(), autoplay=(), '
            'battery=(), camera=(), cross-origin-isolated=(), display-capture=(), '
            'document-domain=(), encrypted-media=(), execution-while-not-rendered=(), '
            'execution-while-out-of-viewport=(), fullscreen=(), geolocation=(), '
            'gyroscope=(), magnetometer=(), microphone=(), midi=(), '
            'navigation-override=(), payment=(), picture-in-picture=(), '
            'publickey-credentials-get=(), sync-xhr=(), usb=(), '
            'xr-spatial-tracking=(), vr=(), wake-lock=()'
        )
        
        # Content-Security-Policy: Proteção avançada contra XSS
        csp_directives = [
            "default-src 'self'",  # Só aceitar recursos da origem
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com",  # Scripts
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",  # Estilos
            "img-src 'self' data: https:",  # Imagens
            "font-src 'self' https://fonts.gstatic.com",  # Fontes
            "connect-src 'self' https:",  # AJAX/WebSocket
            "frame-ancestors 'none'",  # Não embeded em frames
            "base-uri 'self'",  # Restringe <base> tag
            "form-action 'self'",  # Restringe <form> action
            "upgrade-insecure-requests",  # Atualizar HTTP para HTTPS
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Strict-Transport-Security (HSTS)
        # Forçar HTTPS por 1 ano (31536000 segundos)
        response['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains; preload'
        )
        
        return response


class XSSProtectionUtility:
    """Utilitário para escape seguro em templates"""
    
    @staticmethod
    def escape_html(text):
        """Escape básico de HTML"""
        from django.utils.html import escape
        return escape(text)
    
    @staticmethod
    def escape_js(text):
        """Escape para uso em JavaScript"""
        if not text:
            return ''
        # Substituir caracteres perigosos
        text = str(text)
        replacements = {
            '\\': '\\\\',
            '"': '\\"',
            "'": "\\'",
            '<': '\\x3c',
            '>': '\\x3e',
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text
    
    @staticmethod
    def escape_url(url):
        """Escape para URL (previne javascript: protocol)"""
        if not url:
            return ''
        url = str(url).strip()
        # Rejeitar javascript:, data:, vbscript:
        if url.lower().startswith(('javascript:', 'data:', 'vbscript:')):
            return ''
        return url
    
    @staticmethod
    def sanitize_html(html, allowed_tags=None):
        """
        Sanitiza HTML removendo tags perigosas
        Requer: pip install bleach
        """
        try:
            import bleach
            
            if allowed_tags is None:
                allowed_tags = {
                    'p': [],
                    'br': [],
                    'strong': [],
                    'em': [],
                    'u': [],
                    'a': ['href', 'title'],
                    'ul': [],
                    'ol': [],
                    'li': [],
                }
            
            allowed_attributes = {
                'a': ['href', 'title', 'target'],
                'img': ['src', 'alt', 'title'],
            }
            
            return bleach.clean(
                html,
                tags=list(allowed_tags.keys()),
                attributes=allowed_attributes,
                strip=True,
            )
        except ImportError:
            # Fallback se bleach não instalado
            from django.utils.html import escape
            return escape(html)
