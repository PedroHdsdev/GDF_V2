"""
Comando: python manage.py run_seguranca_report
Executa verificações de segurança e gera RELATORIO_SEGURANCA.md.
"""
import os
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Executa verificações de segurança e gera RELATORIO_SEGURANCA.md'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            type=str,
            default='RELATORIO_SEGURANCA.md',
            help='Arquivo de saída do relatório',
        )

    def handle(self, *args, **options):
        output_path = options['output']
        original_allowed = getattr(settings, 'ALLOWED_HOSTS', [])
        original_script = getattr(settings, 'FORCE_SCRIPT_NAME', '')
        settings.ALLOWED_HOSTS = ['*']
        settings.FORCE_SCRIPT_NAME = ''

        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_superuser(
                'admin_seg', 'admin@seg.local', 'adminpass123',
            )

        client_anon = Client()
        client_auth = Client()
        client_auth.force_login(user)

        checks = []

        # --- 1. Rotas protegidas sem autenticação (devem redirecionar)
        protected_paths = [
            ('/Home/', 'Home'),
            ('/usuarios/', 'Usuários'),
            ('/empresas/', 'Empresas'),
            ('/Relatorio/', 'Relatório Fiscal'),
            ('/api/relatorio/nfe/', 'API Relatório NFe'),
            ('/Reprocessamento/Painel/', 'Painel Reprocessamento'),
        ]
        for path, label in protected_paths:
            r = client_anon.get(path)
            ok = r.status_code in (301, 302) and ('Login' in (r.url or '') or r.status_code == 302)
            checks.append({
                'categoria': 'Autenticação',
                'nome': f'Acesso não autenticado a {label}',
                'detalhe': f'GET {path}',
                'esperado': 'Redirect para Login (302)',
                'status': r.status_code,
                'ok': ok,
                'obs': r.url if r.status_code in (301, 302) else '-',
            })

        # --- 2. Login público acessível
        r = client_anon.get('/Login/')
        checks.append({
            'categoria': 'Autenticação',
            'nome': 'Página de login acessível (GET)',
            'detalhe': 'GET /Login/',
            'esperado': '200',
            'status': r.status_code,
            'ok': r.status_code == 200,
            'obs': '-',
        })

        # --- 3. APIs que exigem cod_cliente na sessão (403 sem cliente)
        apis_sessao = [
            ('/api/cargaxml/jobs/', 'API CargaXml Jobs'),
            ('/api/cargaxml/resumo/', 'API CargaXml Resumo'),
            ('/api/reprocessamento/lotes/', 'API Reprocessamento Lotes'),
        ]
        for path, label in apis_sessao:
            r = client_auth.get(path)
            # Sem cod_cliente na sessão esperamos 403
            ok = r.status_code == 403
            checks.append({
                'categoria': 'Sessão / Autorização',
                'nome': f'{label} sem cliente na sessão',
                'detalhe': f'GET {path} (autenticado, sem cod_cliente)',
                'esperado': '403',
                'status': r.status_code,
                'ok': ok,
                'obs': r.json().get('erro', '-')[:80] if r.get('Content-Type', '').startswith('application/json') and r.content else '-',
            })

        # --- 4. IDOR: empresa de outro cliente
        r = client_auth.get('/empresa/COD_NAO_PERTENCE/')
        checks.append({
            'categoria': 'IDOR',
            'nome': 'Acesso a empresa por cod_empresa arbitrário',
            'detalhe': 'GET /empresa/COD_NAO_PERTENCE/ (sem cliente ou outro cliente)',
            'esperado': '403',
            'status': r.status_code,
            'ok': r.status_code == 403,
            'obs': '-',
        })

        # --- 5. Validação de entrada: busca com padrão SQL
        payloads = [
            ("1' OR '1'='1", "SQL-like OR"),
            ("x; DROP TABLE auth_user;--", "SQL DROP"),
            ("a union select 1", "UNION SELECT"),
        ]
        for payload, desc in payloads:
            r = client_auth.get('/api/relatorio/nfe/', {'busca': payload})
            no_500 = r.status_code != 500
            no_traceback = b'Traceback' not in r.content and b'Exception' not in r.content
            ok = no_500 and no_traceback
            checks.append({
                'categoria': 'Validação de entrada',
                'nome': f'Busca maliciosa rejeitada/sanitizada ({desc})',
                'detalhe': f'GET /api/relatorio/nfe/?busca=...',
                'esperado': 'Não 500, sem vazamento de stack',
                'status': r.status_code,
                'ok': ok,
                'obs': '500' if r.status_code == 500 else f'{r.status_code}',
            })

        # --- 6. Headers de segurança
        r = client_anon.get('/Login/')
        h_nosniff = (r.get('X-Content-Type-Options') or '').lower() == 'nosniff'
        h_frame = (r.get('X-Frame-Options') or '').upper() in ('SAMEORIGIN', 'DENY')
        h_xss = '1' in (r.get('X-XSS-Protection') or '') or 'block' in (r.get('X-XSS-Protection') or '').lower()
        checks.append({
            'categoria': 'Headers de segurança',
            'nome': 'X-Content-Type-Options: nosniff',
            'detalhe': 'Resposta GET /Login/',
            'esperado': 'Presente',
            'status': 'OK' if h_nosniff else 'FALTA',
            'ok': h_nosniff,
            'obs': r.get('X-Content-Type-Options') or '-',
        })
        checks.append({
            'categoria': 'Headers de segurança',
            'nome': 'X-Frame-Options (SAMEORIGIN ou DENY)',
            'detalhe': 'Resposta GET /Login/',
            'esperado': 'Presente',
            'status': 'OK' if h_frame else 'FALTA',
            'ok': h_frame,
            'obs': r.get('X-Frame-Options') or '-',
        })
        checks.append({
            'categoria': 'Headers de segurança',
            'nome': 'X-XSS-Protection',
            'detalhe': 'Resposta GET /Login/',
            'esperado': 'Presente',
            'status': 'OK' if h_xss else 'FALTA',
            'ok': h_xss,
            'obs': r.get('X-XSS-Protection') or '-',
        })

        # --- 7. Logout
        client_auth.force_login(user)
        client_auth.get('/Logout/')
        r_after = client_auth.get('/Home/')
        logout_ok = r_after.status_code in (301, 302)
        checks.append({
            'categoria': 'Sessão',
            'nome': 'Logout invalida sessão',
            'detalhe': 'GET /Logout/ depois GET /Home/',
            'esperado': 'Redirect para login',
            'status': r_after.status_code,
            'ok': logout_ok,
            'obs': r_after.url if r_after.status_code in (301, 302) else '-',
        })

        settings.ALLOWED_HOSTS = original_allowed
        settings.FORCE_SCRIPT_NAME = original_script

        # ---- Gerar Markdown
        report_dir = getattr(settings, 'BASE_DIR', None) or os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        out_file = output_path if os.path.isabs(output_path) else os.path.join(report_dir, output_path)

        n_ok = sum(1 for c in checks if c['ok'])
        n_total = len(checks)

        from collections import defaultdict
        by_cat = defaultdict(list)
        for c in checks:
            by_cat[c['categoria']].append(c)

        lines = [
            '# Relatório de Segurança – GDF',
            '',
            f'**Data:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'**Resultado:** {n_ok}/{n_total} verificações passaram',
            '',
            '---',
            '',
            '## 1. Metodologia',
            '',
            'Verificações automáticas com Django test client: acesso não autenticado a rotas protegidas, APIs que exigem sessão (cod_cliente), tentativas IDOR, parâmetros de busca maliciosos (SQL-like), headers HTTP de segurança e logout. Não substitui auditoria manual nem testes de penetração.',
            '',
            '---',
            '',
            '## 2. Resumo por categoria',
            '',
            '| Categoria | Passou | Total | Descrição / impacto |',
            '|-----------|--------|-------|----------------------|',
        ]
        cat_desc = {
            'Autenticação': 'Rotas protegidas devem redirecionar para login; login público acessível.',
            'Sessão / Autorização': 'APIs que exigem cod_cliente devem retornar 403 sem sessão válida.',
            'IDOR': 'Acesso a recurso de outro cliente (empresa) deve ser negado (403).',
            'Validação de entrada': 'Inputs maliciosos (SQL, XSS) não devem causar 500 nem vazar stack.',
            'Headers de segurança': 'X-Content-Type-Options, X-Frame-Options, X-XSS-Protection.',
            'Sessão': 'Logout deve invalidar a sessão.',
        }
        for cat, items in sorted(by_cat.items()):
            ok_cat = sum(1 for x in items if x['ok'])
            desc = cat_desc.get(cat, '-')[:60]
            lines.append(f'| {cat} | {ok_cat} | {len(items)} | {desc} |')

        lines.extend([
            '',
            '---',
            '',
            '## 3. Tabela de verificações',
            '',
            '| Categoria | Verificação | Detalhe | Esperado | Resultado | OK | Observação |',
            '|-----------|-------------|---------|----------|-----------|---|------------|',
        ])

        for c in checks:
            status_str = str(c['status']) if c['status'] is not None else '-'
            obs = (c.get('obs') or '-')[:40]
            ok_str = 'Sim' if c['ok'] else 'Não'
            lines.append(
                f"| {c['categoria']} | {c['nome']} | {c['detalhe'][:50]} | {c['esperado']} | {status_str} | {ok_str} | {obs} |"
            )

        lines.extend([
            '',
            '---',
            '',
            '## 4. Detalhes por categoria',
            '',
        ])
        for cat, items in sorted(by_cat.items()):
            lines.append(f'### {cat}')
            lines.append('')
            for c in items:
                ok_str = '✅' if c['ok'] else '❌'
                lines.append(f"- **{ok_str}** {c['nome']}: esperado {c['esperado']}, obtido {c['status']}. {c.get('obs', '')}")
            lines.append('')

        lines.extend([
            '---',
            '',
            '## 5. Conclusão e recomendações',
            '',
            f'- **Total:** {n_ok}/{n_total} verificações passaram.',
        ])
        if n_ok < n_total:
            falhas = [c['nome'] for c in checks if not c['ok']]
            lines.append('- **Falhas:** ' + '; '.join(falhas[:15]) + ('...' if len(falhas) > 15 else ''))
        lines.extend([
            '',
            '- **Recomendações:** Manter CSRF habilitado em produção; não desativar validação de `busca` nas APIs; revisar periodicamente decoradores IDOR em novas views; manter headers de segurança (middleware).',
            '',
        ])

        content = '\n'.join(lines)
        os.makedirs(os.path.dirname(out_file) or '.', exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f'Relatório de segurança gravado em: {out_file}'))
