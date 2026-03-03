# 🔐 Guia de Deployment HTTPS - GDF_V2

## 1. Configurar HTTPS em Produção

### Opção A: Com Let's Encrypt (RECOMENDADO)

```bash
# Instalar Certbot (client only)
sudo apt-get install certbot

# Gerar certificado (substitua com seu domínio). O método de validação
# e instalação do certificado depende do servidor web que estivesse a correr
# no host (Nginx/Apache/LoadBalancer). Aqui usamos o modo standalone como exemplo:
sudo certbot certonly --standalone -d seu-dominio.com -d www.seu-dominio.com

# Certificado fica em: /etc/letsencrypt/live/seu-dominio.com/
```

### Opção B: Com AWS Certificate Manager (se usar AWS)

1. Acesse AWS Console → Certificate Manager
2. Request a certificate
3. Valide o domínio via DNS/email
4. Configure no Load Balancer

---

## 2. Atualizar `.env` para Produção

```bash
# .env - Production
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# HTTPS obrigatório
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# CSP Report Only (False = enforce, True = report only)
CSP_REPORT_ONLY=False
```

---

## 3. TLS termination / web server configuration

TLS termination and HTTP->HTTPS redirection are the responsibility of the host
web server or load balancer (for example, Nginx, Apache, a cloud LB, or a
managed reverse proxy). The repository no longer includes a full web server
configuration; below are general guidelines:

- Obtain certificates (Let's Encrypt is recommended) and place them under
  `/etc/letsencrypt/live/<your-domain>/` or `/etc/ssl/...`.
- Configure your host web server to terminate TLS and proxy requests to the
  local Gunicorn instance (e.g. `http://127.0.0.1:8500`). Ensure `X-Forwarded-*`
  headers are passed through and `X-Forwarded-Proto` is set to `https`.
- Serve `static/` and `media/` directly from the host filesystem for performance
  (e.g. `alias /var/www/gdf_v2/staticfiles/`).

If you still want an example Nginx snippet to adapt to your host, request it
and it will be provided separately — it's intentionally omitted from the
repository to avoid duplicating host configuration.

---

## 4. Renovação Automática de Certificado

```bash
# Cron job - renovar certificado automaticamente
# Adicione ao crontab: crontab -e

0 3 * * * certbot renew --quiet --post-hook "sudo systemctl reload nginx"
```

---

## 5. Testar Configuração HTTPS

```bash
# Verificar SSL/TLS
curl -I https://seu-dominio.com
# Deve retornar 200 e headers de segurança

# Verificar certificado
openssl s_client -connect seu-dominio.com:443

# SSL Labs test
# Visite: https://www.ssllabs.com/ssltest/analyze.html?d=seu-dominio.com
```

---

## 6. Checklist de Segurança

- [ ] HTTPS habilitado (porta 443)
- [ ] HTTP redireciona para HTTPS (porta 80)
- [ ] Certificado SSL válido
- [ ] HSTS habilitado
- [ ] CSP headers configurados
- [ ] X-Frame-Options = DENY
- [ ] X-Content-Type-Options = nosniff
- [ ] SESSION_COOKIE_SECURE = True
- [ ] CSRF_COOKIE_SECURE = True
- [ ] DEBUG = False
- [ ] SECRET_KEY em variável de ambiente
- [ ] Database password em variável de ambiente
- [ ] Logs armazenados em arquivo

---

## 7. Monitorar HTTPS

```bash
# Ver logs de erro
sudo tail -f /var/log/nginx/error.log

# Ver acesso
sudo tail -f /var/log/nginx/access.log

# Verificar certificado expirando
sudo certbot certificates
```

---

## ⚠️ Problemas Comuns

### "SSL certificate problem"
```bash
# Regenerar certificado
sudo certbot delete --cert-name seu-dominio.com
sudo certbot certonly --standalone -d seu-dominio.com
```

### "Mixed content warning"
- Garantir todos os recursos (CSS, JS, imagens) usem HTTPS
- Atualizar links hardcoded em templates

### "Too many redirects"
- Verificar proxy headers no nginx
- Certificar que X-Forwarded-Proto está configurado

---

## 📈 Performance HTTPS

```nginx
# Enable SPDY/HTTP2 (melhor performance)
listen 443 ssl http2;

# SSL session caching
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# OCSP Stapling (verificação mais rápida)
ssl_stapling on;
ssl_stapling_verify on;
```

---

**Pronto! Seu site está seguro com HTTPS.** 🔒
