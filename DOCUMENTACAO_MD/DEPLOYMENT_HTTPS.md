# 🔐 Guia de Deployment HTTPS - GDF_V2

## 1. Configurar HTTPS em Produção

### Opção A: Com Let's Encrypt (RECOMENDADO)

```bash
# Instalar Certbot
sudo apt-get install certbot python3-certbot-nginx

# Gerar certificado (replace com seu domínio)
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

## 3. Configurar Nginx com HTTPS

```nginx
# /etc/nginx/sites-available/gdf_v2

upstream django_gdf {
    server 127.0.0.1:8000;
}

# Redirecionar HTTP para HTTPS
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # SSL Certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    
    # SSL Configuration (Mozilla Intermediate)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Cliente Upload Limit
    client_max_body_size 100M;
    
    # Proxy para Django
    location / {
        proxy_pass http://django_gdf;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static/ {
        alias /var/www/gdf_v2/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/gdf_v2/media/;
        expires 7d;
    }
}
```

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
