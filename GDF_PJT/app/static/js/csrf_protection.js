/**
 * CSRF Protection for AJAX
 * Adiciona X-CSRFToken automaticamente a todas as requisições AJAX POST/PUT/DELETE
 */

(function() {
    'use strict';

    /**
     * Obter CSRF token do cookie ou do DOM
     */
    function getCsrfToken() {
        // Método 1: Do cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith('csrftoken=')) {
                return cookie.substring('csrftoken='.length);
            }
        }

        // Método 2: Do input hidden no formulário
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput) {
            return tokenInput.value;
        }

        // Método 3: Do meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            return metaTag.getAttribute('content');
        }

        console.warn('CSRF token não encontrado');
        return '';
    }

    /**
     * Setup jQuery AJAX com CSRF
     */
    if (typeof jQuery !== 'undefined') {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                // Não adicionar CSRF token para requisições cross-domain
                const isLocal = new URL(settings.url, window.location.href).hostname === window.location.hostname;
                const isUnsafeMethod = /^(POST|PUT|DELETE|PATCH)$/i.test(settings.type);

                if (isLocal && isUnsafeMethod) {
                    xhr.setRequestHeader('X-CSRFToken', getCsrfToken());
                }
            }
        });
    }

    /**
     * Setup Fetch API com CSRF
     * Intercepta todas as chamadas fetch
     */
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const [resource, config] = args;
        const options = config || {};
        
        // Verificar se é requisição local e unsafe
        const url = new URL(resource, window.location.href);
        const isLocal = url.hostname === window.location.hostname;
        const isUnsafeMethod = /^(POST|PUT|DELETE|PATCH)$/i.test((options.method || 'GET').toUpperCase());

        // Adicionar CSRF token
        if (isLocal && isUnsafeMethod) {
            options.headers = options.headers || {};
            options.headers['X-CSRFToken'] = getCsrfToken();
        }

        return originalFetch.apply(this, [resource, options]);
    };

    /**
     * Exposar getCsrfToken globalmente para uso manual
     */
    window.getCsrfToken = getCsrfToken;

    console.log('✅ CSRF Protection for AJAX inicializado');
})();
