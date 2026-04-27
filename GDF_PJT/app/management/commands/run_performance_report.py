"""
Comando: python manage.py run_performance_report
Executa testes de performance nos principais endpoints e gera RELATORIO_PERFORMANCE.md.
"""
import time
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client, override_settings
from django.db import connection, reset_queries
from django.core.management.base import BaseCommand


@override_settings(DEBUG=True, ALLOWED_HOSTS=['*'], FORCE_SCRIPT_NAME='')
def _measure_n(client, method, path, n=3, **kwargs):
    """Executa n requisições e retorna status, tempo (média/min/max) e queries."""
    times = []
    queries_list = []
    status = None
    for _ in range(n):
        reset_queries()
        t0 = time.perf_counter()
        if method.upper() == 'GET':
            r = client.get(path, **kwargs)
        else:
            r = client.post(path, **kwargs)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        times.append(elapsed_ms)
        queries_list.append(len(connection.queries))
        status = r.status_code
    return {
        'status': status,
        'tempo_medio_ms': round(sum(times) / len(times), 2),
        'tempo_min_ms': round(min(times), 2),
        'tempo_max_ms': round(max(times), 2),
        'queries_medio': round(sum(queries_list) / len(queries_list), 1),
        'queries_max': max(queries_list),
    }


class Command(BaseCommand):
    help = 'Executa testes de performance e gera RELATORIO_PERFORMANCE.md'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            type=str,
            default='RELATORIO_PERFORMANCE.md',
            help='Caminho do arquivo de relatório (default: RELATORIO_PERFORMANCE.md)',
        )
        parser.add_argument(
            '--runs', '-n',
            type=int,
            default=3,
            help='Número de execuções por endpoint para média (default: 3)',
        )

    def handle(self, *args, **options):
        # Test client usa paths na raiz; evitar FORCE_SCRIPT_NAME para não 404
        output_path = options['output']
        n_runs = max(1, options['runs'])
        original_allowed = getattr(settings, 'ALLOWED_HOSTS', [])
        original_script = getattr(settings, 'FORCE_SCRIPT_NAME', '')
        settings.ALLOWED_HOSTS = ['*']
        settings.FORCE_SCRIPT_NAME = ''

        # Paths literais (urlpatterns na raiz) para o test client
        client = Client()
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_superuser('admin_perf', 'admin@test.local', 'adminpass123')
        client.force_login(user)

        endpoints = [
            ('GET', '/Login/', 'Tela de login (GET)', False),
            ('GET', '/Home/', 'Home (autenticado)', True),
            ('GET', '/api/sessao/cliente/', 'API Sessão Cliente', True),
            ('GET', '/api/relatorio/nfe/', 'API Relatório NFe', True),
            ('GET', '/api/relatorio/cte/', 'API Relatório CTe', True),
            ('GET', '/api/relatorio/nfse/', 'API Relatório NFSe', True),
            ('GET', '/api/relatorio/sped/', 'API Relatório SPED', True),
            ('GET', '/api/cargaxml/jobs/', 'API CargaXml Jobs', True),
            ('GET', '/api/cargaxml/resumo/', 'API CargaXml Resumo', True),
            ('GET', '/api/reprocessamento/lotes/', 'API Reprocessamento Lotes', True),
            ('GET', '/usuarios/', 'View Listar Usuários', True),
            ('GET', '/empresas/', 'View Listar Empresas', True),
            ('GET', '/Relatorio/', 'View Relatório Fiscal', True),
            ('GET', '/Reprocessamento/Painel/', 'View Painel Reprocessamento', True),
        ]

        results = []
        for method, path, label, auth in endpoints:
            if auth:
                client.force_login(user)
            try:
                r = _measure_n(client, method, path, n=n_runs)
                r['label'] = label
                r['path'] = path
                r['method'] = method
                results.append(r)
            except Exception as e:
                results.append({
                    'label': label,
                    'path': path,
                    'method': method,
                    'status': 'ERRO',
                    'tempo_medio_ms': None,
                    'tempo_min_ms': None,
                    'tempo_max_ms': None,
                    'queries_medio': None,
                    'queries_max': None,
                    'erro': str(e),
                })
            if auth:
                client.logout()

        client.logout()
        settings.ALLOWED_HOSTS = original_allowed
        settings.FORCE_SCRIPT_NAME = original_script

        # Gerar relatório Markdown
        import os
        from datetime import datetime
        report_dir = getattr(settings, 'BASE_DIR', None) or os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        out_file = output_path if os.path.isabs(output_path) else os.path.join(report_dir, output_path)

        data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        lines = [
            '# Relatório de Performance – GDF',
            '',
            f'**Data e hora:** {data_hora}',
            f'**Execuções por endpoint:** {n_runs}',
            f'**DEBUG (contagem de queries):** {settings.DEBUG}',
            '',
            '---',
            '',
            '## 1. Metodologia',
            '',
            '- Cada endpoint foi chamado **' + str(n_runs) + ' vezes** em sequência.',
            '- Métricas: tempo de resposta (ms), quantidade de queries SQL (com DEBUG=True).',
            '- Ambiente: Django test client (sem rede real). Em produção, latência pode ser maior.',
            '',
            '---',
            '',
            '## 2. Resumo executivo',
            '',
            '| Endpoint | Status | Tempo médio (ms) | Min | Max | Queries (média) | Queries (máx) |',
            '|----------|--------|------------------|-----|-----|-----------------|--------------|',
        ]

        for r in results:
            if r.get('erro'):
                lines.append(
                    f"| {r['label']} | ERRO | - | - | - | - | - |"
                )
            else:
                status = r.get('status', '-')
                t_med = r.get('tempo_medio_ms', '-')
                t_min = r.get('tempo_min_ms', '-')
                t_max = r.get('tempo_max_ms', '-')
                q_med = r.get('queries_medio', '-')
                q_max = r.get('queries_max', '-')
                lines.append(f"| {r['label']} | {status} | {t_med} | {t_min} | {t_max} | {q_med} | {q_max} |")

        lines.extend([
            '',
            '---',
            '',
            '## 3. Detalhes por endpoint',
            '',
        ])

        for r in results:
            lines.append(f"### {r['label']}")
            lines.append('')
            lines.append(f"- **URL:** `{r['method']} {r['path']}`")
            if r.get('erro'):
                lines.append(f"- **Erro:** {r['erro']}")
            else:
                lines.append(f"- **Status HTTP:** {r.get('status')}")
                lines.append(f"- **Tempo médio:** {r.get('tempo_medio_ms')} ms")
                lines.append(f"- **Tempo min/max:** {r.get('tempo_min_ms')} / {r.get('tempo_max_ms')} ms")
                lines.append(f"- **Queries SQL (média/máx):** {r.get('queries_medio')} / {r.get('queries_max')}")
            lines.append('')

        # Métricas agregadas e classificação
        ok_results = [r for r in results if not r.get('erro') and r.get('tempo_medio_ms') is not None]
        if ok_results:
            media_geral = round(sum(r['tempo_medio_ms'] for r in ok_results) / len(ok_results), 2)
            mais_lento = max(ok_results, key=lambda x: x['tempo_medio_ms'])
            mais_rapido = min(ok_results, key=lambda x: x['tempo_medio_ms'])
            # Classificação: < 50ms rápido, 50–150 ms médio, > 150 ms lento
            rapidos = [r for r in ok_results if r['tempo_medio_ms'] < 50]
            medios = [r for r in ok_results if 50 <= r['tempo_medio_ms'] < 150]
            lentos = [r for r in ok_results if r['tempo_medio_ms'] >= 150]
            lines.extend([
                '---',
                '',
                '## 4. Métricas agregadas',
                '',
                f"- **Endpoints medidos:** {len(ok_results)}",
                f"- **Tempo médio geral:** {media_geral} ms",
                f"- **Endpoint mais lento:** {mais_lento['label']} ({mais_lento['tempo_medio_ms']} ms)",
                f"- **Endpoint mais rápido:** {mais_rapido['label']} ({mais_rapido['tempo_medio_ms']} ms)",
                '',
                '---',
                '',
                '## 5. Classificação por faixa de tempo',
                '',
                '| Faixa | Quantidade | Endpoints (exemplos) |',
                '|-------|------------|----------------------|',
                f"| **Rápido** (< 50 ms) | {len(rapidos)} | " + (', '.join(r['label'][:25] for r in rapidos[:5]) or '-') + ('...' if len(rapidos) > 5 else '') + ' |',
                f"| **Médio** (50–150 ms) | {len(medios)} | " + (', '.join(r['label'][:25] for r in medios[:5]) or '-') + ('...' if len(medios) > 5 else '') + ' |',
                f"| **Lento** (≥ 150 ms) | {len(lentos)} | " + (', '.join(r['label'][:25] for r in lentos[:5]) or '-') + ('...' if len(lentos) > 5 else '') + ' |',
                '',
                '---',
                '',
                '## 6. Recomendações',
                '',
                '- Endpoints com **muitas queries** (máx > 20): considerar `select_related()`/`prefetch_related()` ou cache.',
                '- Endpoints **lentos** (≥ 150 ms): revisar consultas ao banco e tamanho de payload.',
                '- Em produção, medir novamente com carga real e com DEBUG=False.',
                '',
            ])

        content = '\n'.join(lines)
        os.makedirs(os.path.dirname(out_file) or '.', exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f'Relatório gravado em: {out_file}'))
        return
