#!/usr/bin/env python3
"""
Script de diagnóstico: Testar conectividade e segurança do iframe Streamlit
Uso: python test_streamlit_connection.py
"""

import socket
import requests
import sys
from datetime import datetime

# ============================================================
# Configurações
# ============================================================
STREAMLIT_HOST = "10.0.1.158"
STREAMLIT_PORT = 8901
DJANGO_HOST = "127.0.0.1"
DJANGO_PORT = 8000

print("=" * 70)
print("📊 DIAGNÓSTICO: Conexão Django → Streamlit")
print("=" * 70)
print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")

# ============================================================
# 1. Teste de Conectividade
# ============================================================
print("🔍 1. TESTE DE CONECTIVIDADE")
print("-" * 70)

def test_host_port(host, port, name):
    """Testa se host:port está acessível"""
    try:
        socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_obj.settimeout(3)
        resultado = socket_obj.connect_ex((host, port))
        socket_obj.close()
        
        if resultado == 0:
            print(f"✅ {name}: {host}:{port} - ACESSÍVEL")
            return True
        else:
            print(f"❌ {name}: {host}:{port} - INACESSÍVEL (erro: {resultado})")
            return False
    except Exception as fn_e:
        print(f"❌ {name}: {host}:{port} - ERRO: {str(fn_e)}")
        return False

l_b_django_ok = test_host_port(DJANGO_HOST, DJANGO_PORT, "Django")
l_b_streamlit_ok = test_host_port(STREAMLIT_HOST, STREAMLIT_PORT, "Streamlit")

# ============================================================
# 2. Teste HTTP
# ============================================================
print("\n🌐 2. TESTE HTTP/HTTPS")
print("-" * 70)

# Testar Django
try:
    r_django = requests.get(f"http://{DJANGO_HOST}:{DJANGO_PORT}/", timeout=3)
    print(f"✅ Django HTTP: Status {r_django.status_code}")
except Exception as fn_e:
    print(f"❌ Django HTTP: {str(fn_e)}")

# Testar Streamlit
try:
    r_streamlit = requests.get(f"http://{STREAMLIT_HOST}:{STREAMLIT_PORT}/", timeout=3)
    print(f"✅ Streamlit HTTP: Status {r_streamlit.status_code}")
except Exception as fn_e:
    print(f"❌ Streamlit HTTP: {str(fn_e)}")

# ============================================================
# 3. Teste JWT
# ============================================================
print("\n🔐 3. TESTE JWT")
print("-" * 70)

try:
    from jwt import encode as jwt_encode
    from django.conf import settings
    import os
    import django
    
    # Setup Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "GDF_PJT.settings")
    django.setup()
    
    # Gerar token
    import time
    g_v_iat = int(time.time())
    g_v_exp = g_v_iat + (30 * 60)
    
    payload = {
        "user_id": 1,
        "username": "test_user",
        "tipo_relatorio": "Vendas",
        "iat": g_v_iat,
        "exp": g_v_exp,
    }
    
    g_og_token = jwt_encode(payload, settings.SECRET_KEY, algorithm='HS256')
    print(f"✅ Token gerado: {g_og_token[:50]}...")
    print(f"   Comprimento: {len(g_og_token)} caracteres")
    print(f"   Expiração: em 30 minutos")
    
except Exception as fn_e:
    print(f"❌ JWT encode: {str(fn_e)}")

# ============================================================
# 4. Resumo de Segurança
# ============================================================
print("\n🛡️  4. ANÁLISE DE SEGURANÇA")
print("-" * 70)

print("Protocolo: HTTP (⚠️ Inseguro em produção)")
print("Token: Query Parameter (⚠️ Visível em logs)")
print("Duração: 30 minutos (✅ Curta)")
print("CORS: Necessário configurar SameSite (⚠️ Pendente)")

# ============================================================
# 5. Recomendações
# ============================================================
print("\n💡 RECOMENDAÇÕES")
print("-" * 70)

if "10.0.1" in STREAMLIT_HOST:
    print("✅ Ambiente INTRANET (IP privado 10.x)")
    print("   → HTTP é aceitável, mas configure SameSite")
else:
    print("⚠️  IP parece PÚBLICO")
    print("   → HTTPS OBRIGATÓRIO")

print("\nPróximos passos:")
print("1. Confirmar se 10.0.1.158 é intranet ou produção")
print("2. Se produção → implementar HTTPS + certificado SSL")
print("3. Adicionar ao settings.py:")
print("   SESSION_COOKIE_SAMESITE = 'None'")
print("4. Configurar Streamlit (.streamlit/config.toml):")
print("   enableXsrfProtection = false")

print("\n" + "=" * 70)
print("✅ Diagnóstico completo")
print("=" * 70)
