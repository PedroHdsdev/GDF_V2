"""
Testes de escalabilidade: carga concorrente e volume.
- Concorrência: N requisições simultâneas ao mesmo endpoint.
- Volume: sequência de muitas requisições (throughput, latência p95/p99).
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings


def _percentil(sorted_values, p):
    """Retorna o percentil p (0-100) de uma lista ordenada."""
    if not sorted_values:
        return None
    k = (len(sorted_values) - 1) * (p / 100)
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_values) else f
    return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])


@override_settings(DEBUG=True, ALLOWED_HOSTS=['*'], FORCE_SCRIPT_NAME='')
class EscalabilidadeTestCase(TestCase):
    """Testes de carga concorrente e volume."""

    def setUp(self):
        self.user = User.objects.filter(is_superuser=True).first()
        if not self.user:
            self.user = User.objects.create_superuser(
                'admin_esc', 'admin@esc.local', 'adminpass123'
            )
        self.endpoints = [
            ('GET', '/Login/'),
            ('GET', '/Home/'),
            ('GET', '/api/relatorio/nfe/'),
            ('GET', '/usuarios/'),
        ]

    def _one_request(self, method, path, auth=True):
        """Uma requisição com client próprio (thread-safe). Retorna (status, tempo_ms)."""
        client = Client()
        if auth:
            client.force_login(self.user)
        t0 = time.perf_counter()
        if method.upper() == 'GET':
            r = client.get(path)
        else:
            r = client.post(path, data={})
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return r.status_code, round(elapsed_ms, 2)

    def test_concorrencia_5_usuarios(self):
        """5 requisições simultâneas ao mesmo endpoint (Home)."""
        n = 5
        with ThreadPoolExecutor(max_workers=n) as ex:
            futures = [
                ex.submit(self._one_request, 'GET', '/Home/', True)
                for _ in range(n)
            ]
            results = [f.result() for f in as_completed(futures)]
        statuses = [r[0] for r in results]
        times_ms = [r[1] for r in results]
        self.assertTrue(all(s in (200, 302) for s in statuses), f"Statuses: {statuses}")
        self.assertEqual(len(times_ms), n)
        # Guardar para inspeção
        self.conc_5_times = times_ms
        self.conc_5_media = sum(times_ms) / len(times_ms)

    def test_concorrencia_10_usuarios(self):
        """10 requisições simultâneas ao endpoint Home."""
        n = 10
        with ThreadPoolExecutor(max_workers=n) as ex:
            futures = [
                ex.submit(self._one_request, 'GET', '/Home/', True)
                for _ in range(n)
            ]
            results = [f.result() for f in as_completed(futures)]
        statuses = [r[0] for r in results]
        times_ms = [r[1] for r in results]
        self.assertTrue(all(s in (200, 302) for s in statuses), f"Statuses: {statuses}")
        self.assertEqual(len(times_ms), n)
        self.conc_10_times = times_ms
        self.conc_10_media = sum(times_ms) / len(times_ms)

    def test_volume_50_requisicoes_sequenciais(self):
        """50 requisições sequenciais (burst) para medir estabilidade."""
        path = '/api/relatorio/nfe/'
        n = 50
        times = []
        client = Client()
        client.force_login(self.user)
        for _ in range(n):
            t0 = time.perf_counter()
            r = client.get(path)
            times.append((r.status_code, (time.perf_counter() - t0) * 1000))
        statuses = [t[0] for t in times]
        times_ms = [round(t[1], 2) for t in times]
        ok = sum(1 for s in statuses if s == 200)
        self.assertGreaterEqual(ok, n * 0.95, f"Sucesso: {ok}/{n}, statuses: {statuses[:10]}...")
        sorted_t = sorted(times_ms)
        self.vol_50_media = sum(times_ms) / len(times_ms)
        self.vol_50_p95 = _percentil(sorted_t, 95)
        self.vol_50_p99 = _percentil(sorted_t, 99)
        self.vol_50_times = times_ms

    def test_throughput_login(self):
        """Throughput: quantas requisições GET /Login/ por segundo (sequencial)."""
        n = 30
        client = Client()
        t0 = time.perf_counter()
        for _ in range(n):
            client.get('/Login/')
        elapsed = time.perf_counter() - t0
        req_per_sec = n / elapsed if elapsed > 0 else 0
        self.assertGreater(elapsed, 0)
        self.throughput_login = round(req_per_sec, 2)
        self.throughput_login_elapsed = round(elapsed, 2)
