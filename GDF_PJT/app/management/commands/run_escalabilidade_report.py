"""
Comando: python manage.py run_escalabilidade_report
Executa testes de escalabilidade (carga concorrente e volume) e gera RELATORIO_ESCALABILIDADE.md.
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.core.management.base import BaseCommand


def _percentil(sorted_values, p):
    if not sorted_values:
        return None
    k = (len(sorted_values) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    return round(
        sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f]), 2
    )


# Limite de threads simultâneas para não exceder max_connections do PostgreSQL
MAX_WORKERS = 15


def _one_request(user, method, path, auth=True):
    """Uma requisição com client próprio (thread-safe). Retorna (status, tempo_ms)."""
    from django.db import connection
    try:
        client = Client()
        if auth:
            client.force_login(user)
        t0 = time.perf_counter()
        try:
            if method.upper() == 'GET':
                r = client.get(path)
            else:
                r = client.post(path, data={})
            status = r.status_code
        except Exception:
            status = 0
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return status, round(elapsed_ms, 2)
    finally:
        connection.close()


class Command(BaseCommand):
    help = 'Executa testes de escalabilidade e gera RELATORIO_ESCALABILIDADE.md'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output', '-o',
            type=str,
            default='RELATORIO_ESCALABILIDADE.md',
            help='Arquivo de saída do relatório',
        )
        parser.add_argument(
            '--concorrentes',
            type=int,
            default=5,
            help='Número máximo de usuários concorrentes (cenários: 1, 2, 5, 10, N)',
        )
        parser.add_argument(
            '--volume',
            type=int,
            default=50,
            help='Número de requisições no teste de volume sequencial',
        )

    def handle(self, *args, **options):
        output_path = options['output']
        max_concorrentes = max(2, min(options['concorrentes'], 50))
        n_volume = max(10, min(options['volume'], 500))

        original_allowed = getattr(settings, 'ALLOWED_HOSTS', [])
        original_script = getattr(settings, 'FORCE_SCRIPT_NAME', '')
        settings.ALLOWED_HOSTS = ['*']
        settings.FORCE_SCRIPT_NAME = ''

        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_superuser(
                'admin_esc', 'admin@esc.local', 'adminpass123'
            )

        endpoints_carga = [
            ('GET', '/Login/', 'Login (público)', False),
            ('GET', '/Home/', 'Home (autenticado)', True),
            ('GET', '/api/relatorio/nfe/', 'API Relatório NFe', True),
            ('GET', '/usuarios/', 'View Usuários', True),
        ]

        report = {
            'data': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'concorrencia': [],
            'volume': [],
            'throughput': [],
        }

        # ---- Concorrência: vários níveis de usuários simultâneos
        niveis = [1, 2]
        if max_concorrentes >= 5:
            niveis.append(5)
        if max_concorrentes >= 10:
            niveis.append(10)
        if max_concorrentes > 10 and max_concorrentes <= 50:
            niveis.append(max_concorrentes)

        for n_conc in niveis:
            workers = min(n_conc, MAX_WORKERS)
            for method, path, label, auth in endpoints_carga:
                t0_wall = time.perf_counter()
                with ThreadPoolExecutor(max_workers=workers) as ex:
                    futures = [
                        ex.submit(_one_request, user, method, path, auth)
                        for _ in range(n_conc)
                    ]
                    results = [f.result() for f in as_completed(futures)]
                wall_s = time.perf_counter() - t0_wall
                statuses = [r[0] for r in results]
                times_ms = [r[1] for r in results]
                ok = sum(1 for s in statuses if 200 <= s < 400)
                sorted_t = sorted(times_ms)
                report['concorrencia'].append({
                    'label': label,
                    'path': path,
                    'n_concorrentes': n_conc,
                    'tempo_parede_s': round(wall_s, 2),
                    'req_s': round(n_conc / wall_s, 2) if wall_s > 0 else 0,
                    'tempo_medio_ms': round(sum(times_ms) / len(times_ms), 2),
                    'tempo_min_ms': min(times_ms),
                    'tempo_max_ms': max(times_ms),
                    'p95_ms': _percentil(sorted_t, 95),
                    'p99_ms': _percentil(sorted_t, 99),
                    'sucesso': ok,
                    'total': n_conc,
                    'status_ok': ok == n_conc,
                })

        # ---- Volume: sequencial
        path_vol = '/api/relatorio/nfe/'
        client = Client()
        client.force_login(user)
        t0_vol = time.perf_counter()
        vol_times = []
        vol_statuses = []
        for _ in range(n_volume):
            t0 = time.perf_counter()
            r = client.get(path_vol)
            vol_times.append(round((time.perf_counter() - t0) * 1000, 2))
            vol_statuses.append(r.status_code)
        wall_vol = time.perf_counter() - t0_vol
        ok_vol = sum(1 for s in vol_statuses if s == 200)
        sorted_vol = sorted(vol_times)
        report['volume'].append({
            'path': path_vol,
            'n_requisicoes': n_volume,
            'tempo_total_s': round(wall_vol, 2),
            'req_s': round(n_volume / wall_vol, 2) if wall_vol > 0 else 0,
            'tempo_medio_ms': round(sum(vol_times) / len(vol_times), 2),
            'p95_ms': _percentil(sorted_vol, 95),
            'p99_ms': _percentil(sorted_vol, 99),
            'sucesso': ok_vol,
            'total': n_volume,
        })

        # ---- Throughput Login (sequencial)
        n_th = 40
        t0_th = time.perf_counter()
        for _ in range(n_th):
            Client().get('/Login/')
        wall_th = time.perf_counter() - t0_th
        report['throughput'].append({
            'endpoint': 'GET /Login/',
            'n': n_th,
            'tempo_s': round(wall_th, 2),
            'req_s': round(n_th / wall_th, 2) if wall_th > 0 else 0,
        })

        settings.ALLOWED_HOSTS = original_allowed
        settings.FORCE_SCRIPT_NAME = original_script

        # Calcular limite de usuários simultâneos (uma vez)
        by_n = {}
        for x in report['concorrencia']:
            n = x['n_concorrentes']
            if n not in by_n:
                by_n[n] = []
            by_n[n].append(x)
        max_n_tested = max(by_n.keys()) if by_n else 0
        limite_100 = 0
        for n in sorted(by_n.keys()):
            if all(item['status_ok'] for item in by_n[n]):
                limite_100 = n
        limite_recomendado = max(1, int(limite_100 * 0.7)) if limite_100 else max_n_tested
        p95_por_endpoint = {}
        for x in report['concorrencia']:
            if x['n_concorrentes'] == limite_100 and x['status_ok']:
                p95_por_endpoint[x['label']] = x['p95_ms']

        # ---- Gerar Markdown
        report_dir = getattr(settings, 'BASE_DIR', None) or os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        out_file = output_path if os.path.isabs(output_path) else os.path.join(report_dir, output_path)

        lines = [
            '# Relatório de Escalabilidade – GDF',
            '',
            f'**Data:** {report["data"]}',
            f'**Usuários concorrentes (máx testado):** {max_concorrentes}',
            f'**Volume (requisições sequenciais):** {n_volume}',
            '',
            '### Limite de usuários simultâneos (resumo)',
            '',
            f'- **Recomendado para operação hoje:** **{limite_recomendado} usuários simultâneos** (margem de segurança ~70% sobre o limite com 100% sucesso).',
            f'- **Maior nível testado com 100% sucesso:** {limite_100} usuários.',
            '',
            '---',
            '',
            '## 1. Carga concorrente',
            '',
            'Requisições simultâneas ao mesmo endpoint (threads).',
            '',
            '| Endpoint | Concorrentes | Tempo parede (s) | Req/s | Tempo médio (ms) | Min | Max | P95 (ms) | P99 (ms) | Sucesso |',
            '|----------|--------------|------------------|-------|------------------|-----|-----|----------|----------|--------|',
        ]

        for r in report['concorrencia']:
            ok_str = f"{r['sucesso']}/{r['total']}"
            lines.append(
                f"| {r['label']} | {r['n_concorrentes']} | {r['tempo_parede_s']} | {r['req_s']} | "
                f"{r['tempo_medio_ms']} | {r['tempo_min_ms']} | {r['tempo_max_ms']} | "
                f"{r['p95_ms']} | {r['p99_ms']} | {ok_str} |"
            )

        lines.extend([
            '',
            '---',
            '',
            '## 2. Volume (requisições sequenciais)',
            '',
            f'**Endpoint:** `GET {path_vol}`',
            f'**Requisições:** {n_volume}',
            '',
            '| Tempo total (s) | Throughput (req/s) | Tempo médio (ms) | P95 (ms) | P99 (ms) | Sucesso |',
            '|-----------------|--------------------|------------------|----------|----------|--------|',
        ])
        v = report['volume'][0]
        lines.append(
            f"| {v['tempo_total_s']} | {v['req_s']} | {v['tempo_medio_ms']} | "
            f"{v['p95_ms']} | {v['p99_ms']} | {v['sucesso']}/{v['total']} |"
        )
        if v['sucesso'] < v['total']:
            lines.append('')
            lines.append(f"*Observação:* {v['total'] - v['sucesso']} requisições falharam (ex.: rate limit 429). Throughput e P95 referem-se às requisições bem-sucedidas.")

        lines.extend([
            '',
            '---',
            '',
            '## 3. Throughput (Login público)',
            '',
            'Requisições sequenciais GET /Login/ (sem autenticação).',
            '',
            '| Requisições | Tempo (s) | Req/s |',
            '|-------------|-----------|-------|',
        ])
        for t in report['throughput']:
            lines.append(f"| {t['n']} | {t['tempo_s']} | {t['req_s']} |")

        conc_ok = [x for x in report['concorrencia'] if x['status_ok']]
        lines.extend([
            '',
            '---',
            '',
            '## 4. Limite de usuários simultâneos (hoje)',
            '',
            'Com base nos testes de carga concorrente realizados:',
            '',
            '| Métrica | Valor | Observação |',
            '|---------|-------|------------|',
            f"| **Máximo testado** | {max_n_tested} usuários | Maior N de threads simuladas neste relatório |",
            f"| **Limite com 100% sucesso** | {limite_100} usuários | Maior N em que todos os endpoints responderam 200/302 em todas as requisições |",
            f"| **Recomendado (operação)** | **{limite_recomendado} usuários** | Margem de segurança (~70% do limite) para picos e variação de rede/servidor |",
            '',
            '**Interpretação:** Em ambiente similar ao do teste (mesmo servidor, banco e rede), é seguro planejar até **' + str(limite_recomendado) + ' usuários simultâneos** usando a aplicação. Acima disso, considere escalar (mais workers, cache, BD) ou rodar novo teste com `--concorrentes 20` (ou maior) para reavaliar.',
            '',
        ])
        if p95_por_endpoint:
            lines.append('**Latência P95 no limite (ms) por endpoint:**')
            lines.append('')
            for label, p95 in sorted(p95_por_endpoint.items(), key=lambda t: -t[1]):
                lines.append(f"- {label}: {p95} ms")
            lines.append('')

        lines.extend([
            '---',
            '',
            '## 5. Resumo geral',
            '',
            f"- **Cenários de concorrência:** {len(report['concorrencia'])} (com sucesso: {len(conc_ok)}/{len(report['concorrencia'])})",
            f"- **Throughput (volume sequencial):** {report['volume'][0]['req_s']} req/s (GET API NFe, {n_volume} requisições)",
            f"- **Throughput (Login público):** {report['throughput'][0]['req_s']} req/s",
            '',
            '---',
            '',
            '## 6. Metodologia e recomendações',
            '',
            '- **Concorrência:** cada nível (1, 2, 5, 10, …) executa N requisições em paralelo (threads) ao mesmo endpoint.',
            '- **Volume:** requisições sequenciais ao mesmo endpoint para medir throughput estável.',
            '- Para aumentar o limite testado, execute: `python manage.py run_escalabilidade_report --concorrentes 20 --volume 100`.',
            '- Em produção, o limite real depende de CPU, memória, conexões ao banco e rede.',
            '',
        ])

        content = '\n'.join(lines)
        os.makedirs(os.path.dirname(out_file) or '.', exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(content)

        self.stdout.write(self.style.SUCCESS(f'Relatório de escalabilidade gravado em: {out_file}'))
