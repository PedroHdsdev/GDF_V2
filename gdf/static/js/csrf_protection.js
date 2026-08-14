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
     * Intercepta todas as chamadas fetch.
     * Aceita fetch(url, options) ou fetch(Request).
     */
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const [resource, config] = args;
        const isRequest = resource && typeof resource === 'object' && typeof resource.url !== 'undefined';

        let urlStr;
        let options;
        let method;

        if (isRequest) {
            urlStr = resource.url;
            method = (resource.method || 'GET').toUpperCase();
            options = resource;
        } else {
            urlStr = typeof resource === 'string' ? resource : String(resource);
            options = Object.assign({}, config || {});
            method = (options.method || 'GET').toUpperCase();
        }

        try {
            var url = new URL(urlStr, window.location.href);
        } catch (e) {
            return originalFetch.apply(this, args);
        }

        const isLocal = url.hostname === window.location.hostname;
        const isUnsafeMethod = /^(POST|PUT|DELETE|PATCH)$/i.test(method);

        if (isLocal && isUnsafeMethod) {
            const token = getCsrfToken();
            if (isRequest) {
                const headers = new Headers(resource.headers);
                headers.set('X-CSRFToken', token);
                return originalFetch.apply(this, [new Request(resource, { headers: headers })]);
            }
            options.headers = options.headers || {};
            if (options.headers instanceof Headers) {
                options.headers.set('X-CSRFToken', token);
            } else {
                options.headers['X-CSRFToken'] = token;
            }
        }

        return originalFetch.apply(this, [resource, options]);
    };

    /**
     * Exposar getCsrfToken globalmente para uso manual
     */
    window.getCsrfToken = getCsrfToken;

    console.log('✅ CSRF Protection for AJAX inicializado');
})();
