"""
Testes de performance: tempo de resposta e número de queries por endpoint.
Gera métricas para relatório (usado por run_performance_report).
"""
import time
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.db import connection, reset_queries


# Habilitar captura de queries para contagem (apenas durante o teste)
@override_settings(DEBUG=True)
class PerformanceTestCase(TestCase):
    """Mede tempo de resposta e quantidade de queries dos principais endpoints."""

    def setUp(self):
        self.client = Client()
        # Usuário para requisições autenticadas
        self.user = User.objects.create_user(
            username='perftest',
            email='perftest@test.local',
            password='testpass123',
            is_staff=False,
            is_superuser=False,
        )
        # Script name para URLs (ex.: /gdf)
        self.prefix = getattr(settings, 'FORCE_SCRIPT_NAME', '') or ''

    def _url(self, name_or_path):
        if name_or_path.startswith('/'):
            return self.prefix + name_or_path if self.prefix else name_or_path
        return self.prefix + reverse(name_or_path) if self.prefix else reverse(name_or_path)

    def _measure(self, method, path, **kwargs):
        """Faz a requisição e retorna (status_code, tempo_ms, num_queries)."""
        reset_queries()
        t0 = time.perf_counter()
        if method.upper() == 'GET':
            r = self.client.get(path, **kwargs)
        else:
            r = self.client.post(path, **kwargs)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        num_queries = len(connection.queries) if settings.DEBUG else 0
        return r.status_code, round(elapsed_ms, 2), num_queries

    def _measure_n(self, method, path, n=3, **kwargs):
        """Executa n vezes e retorna médias e máximo."""
        times = []
        queries_list = []
        status = None
        for _ in range(n):
            status, t, q = self._measure(method, path, **kwargs)
            times.append(t)
            queries_list.append(q)
        return {
            'status': status,
            'tempo_medio_ms': round(sum(times) / len(times), 2),
            'tempo_min_ms': min(times),
            'tempo_max_ms': max(times),
            'queries_medio': round(sum(queries_list) / len(queries_list), 1) if queries_list else 0,
            'queries_max': max(queries_list) if queries_list else 0,
        }

    def test_login_get(self):
        """GET na tela de login (público)."""
        path = self._url('Login')
        result = self._measure_n('GET', path, n=3)
        self.result_login_get = result

    def test_home_authenticated(self):
        """GET Home com usuário autenticado."""
        self.client.force_login(self.user)
        path = self._url('Home')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_home = result

    def test_api_sessao_cliente(self):
        """API sessão cliente (requer login)."""
        self.client.force_login(self.user)
        path = self._url('API_SessaoCliente')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_api_sessao = result

    def test_api_relatorio_nfe(self):
        """API relatório NFe (lista, requer login)."""
        self.client.force_login(self.user)
        path = self._url('API_RelatorioNFe')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_api_relatorio_nfe = result

    def test_api_relatorio_cte(self):
        """API relatório CTe."""
        self.client.force_login(self.user)
        path = self._url('API_RelatorioCTe')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_api_relatorio_cte = result

    def test_api_relatorio_nfse(self):
        """API relatório NFSe."""
        self.client.force_login(self.user)
        path = self._url('API_RelatorioNFSe')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_api_relatorio_nfse = result

    def test_api_relatorio_sped(self):
        """API relatório SPED."""
        self.client.force_login(self.user)
        path = self._url('API_RelatorioSped')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_api_relatorio_sped = result

    def test_api_cargaxml_jobs(self):
        """API lista jobs CargaXml."""
        self.client.force_login(self.user)
        path = self._url('API_CargaXmlJobs')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_api_cargaxml_jobs = result

    def test_api_cargaxml_resumo(self):
        """API resumo CargaXml."""
        self.client.force_login(self.user)
        path = self._url('API_CargaXmlResumo')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_api_cargaxml_resumo = result

    def test_api_reprocessamento_lotes(self):
        """API lotes reprocessamento."""
        self.client.force_login(self.user)
        path = self._url('API_ReprocessamentoLotes')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_api_reprocessamento_lotes = result

    def test_view_listar_usuarios(self):
        """View listar usuários (página)."""
        self.client.force_login(self.user)
        path = self._url('Dm_Usuarios')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_view_usuarios = result

    def test_view_listar_empresas(self):
        """View listar empresas (página)."""
        self.client.force_login(self.user)
        path = self._url('Dm_Empresas')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_view_empresas = result

    def test_view_carga_xml(self):
        """View Carga XML (página, inclui painel de relatórios NFe/CTe/NFS)."""
        self.client.force_login(self.user)
        path = self._url('Pro_CargaXml')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_view_carga_xml = result

    def test_view_reprocessamento_painel(self):
        """View painel reprocessamento."""
        self.client.force_login(self.user)
        path = self._url('Reproc_Painel')
        result = self._measure_n('GET', path, n=3)
        self.client.logout()
        self.result_view_reprocessamento = result
