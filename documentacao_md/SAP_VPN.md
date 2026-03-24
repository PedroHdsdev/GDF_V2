# SAP e VPN – Guia de conectividade

A integração SAP via RFC (PyRFC) exige que o **servidor** onde o Django roda consiga alcançar o sistema SAP. Se o SAP estiver em uma rede interna acessível apenas por VPN, o servidor precisa estar conectado à VPN.

---

## 1. Onde a conexão é feita

| Componente | Função |
|------------|--------|
| **Navegador do usuário** | Acessa o Django (HTTP/HTTPS). Não conecta diretamente ao SAP. |
| **Servidor Django** | Recebe as requisições e chama PyRFC para conectar ao SAP. A conexão RFC sai **do servidor**. |

Portanto: a VPN deve estar ativa **no servidor** que executa o Django/Gunicorn, não na máquina do usuário.

---

## 2. Opções para servidor com acesso ao SAP

### 2.1 Servidor na rede interna

Colocar o servidor Django na mesma rede do SAP (ex.: datacenter, DMZ interna) elimina a necessidade de VPN para esse ambiente.

### 2.2 VPN no servidor

Instalar e configurar o cliente VPN no servidor (ex.: OpenVPN, WireGuard, Cisco AnyConnect, etc.) e garantir que o túnel esteja ativo antes de subir o Django:

```bash
# Exemplo: OpenVPN com arquivo de config
sudo openvpn --config /etc/openvpn/client.conf --daemon
```

Configurar o VPN para iniciar automaticamente (systemd, init script, etc.).

### 2.3 Servidor com VPN sempre ativa

Alguns provedores ou infraestruturas permitem VPN site-to-site. Se o servidor já estiver na rede interna via VPN, o acesso ao SAP funciona normalmente.

---

## 3. Testar conectividade

Antes de testar pelo Django:

```bash
# Testar se o host SAP está acessível (substitua HOST_SAP pela ashost do ConexaoSap)
ping HOST_SAP

# Testar porta do SAP (geralmente 33xx para system number)
nc -zv HOST_SAP 3300
```

Se `ping` ou `nc` falharem, o servidor não está alcançando o SAP (rede/VPN ou firewall).

---

## 4. Mensagens de erro no sistema

Quando a conexão falha por rede (timeout, host unreachable, etc.), o sistema exibe uma mensagem indicando o uso de VPN:

> *"Se o SAP exige VPN, o servidor onde o Django roda deve estar conectado à VPN corporativa."*

---

## 5. Clientes com SAP em redes diferentes

| Cenário | Solução |
|---------|---------|
| 1 cliente exige VPN, outros não | Servidor com VPN ativa; VPN deve permitir acesso à rede do SAP desse cliente. |
| Vários clientes com SAP em redes diferentes | Cada rede pode exigir VPN própria ou rota específica. Avaliar VPN multi-site ou múltiplos túneis. |

---

## 6. Checklist de troubleshooting

- [ ] O servidor está na mesma rede do SAP ou com VPN ativa?
- [ ] `ping` e `nc` para o host SAP funcionam no servidor?
- [ ] Credenciais em `ConexaoSap` (ashost, sysnr, client, user, passwd) estão corretas?
- [ ] Firewall permite tráfego entre servidor e SAP (porta 33xx)?
- [ ] RFC SDK está instalado e `LD_LIBRARY_PATH` configurado corretamente?
