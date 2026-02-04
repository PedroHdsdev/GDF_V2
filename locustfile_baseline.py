"""
locustfile_baseline.py

Cenários de teste de carga para GDF_V2.
Simula usuários reais com comportamentos variados.
"""

from locust import HttpUser, task, between, TaskSet, events
import random
from datetime import datetime
import json

# Configurações
TARGET_URL = "http://localhost:8000"
LOGIN_URL = f"{TARGET_URL}/Login/"
HOME_URL = f"{TARGET_URL}/home/"

# Dados de teste
TEST_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123',
}


class GDFTasks(TaskSet):
    """Tasks dos usuários."""
    
    def on_start(self):
        """Executado quando usuário inicia."""
        self.login()
    
    def login(self):
        """Realiza login."""
        response = self.client.get(LOGIN_URL)
        
        # Extrair CSRF token
        csrf_token = self._extract_csrf_token(response.text)
        
        # Enviar login
        self.client.post(
            LOGIN_URL,
            data={
                'username': TEST_CREDENTIALS['username'],
                'password': TEST_CREDENTIALS['password'],
                'csrfmiddlewaretoken': csrf_token,
            },
            allow_redirects=True,
            name="POST /Login/ (login)"
        )
    
    @staticmethod
    def _extract_csrf_token(html):
        """Extrai CSRF token do HTML."""
        import re
        match = re.search(r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        return ""
    
    @task(3)
    def view_home(self):
        """Acessar home - 30% das requisições."""
        self.client.get(HOME_URL, name="GET /home/ (home page)")
    
    @task(2)
    def list_usuarios(self):
        """Listar usuários - 20% das requisições."""
        self.client.get(
            f"{TARGET_URL}/Usuarios/",
            name="GET /Usuarios/ (list users)"
        )
    
    @task(2)
    def list_empresas(self):
        """Listar empresas - 20% das requisições."""
        self.client.get(
            f"{TARGET_URL}/Empresas/",
            name="GET /Empresas/ (list companies)"
        )
    
    @task(1)
    def list_clientes(self):
        """Listar clientes - 10% das requisições."""
        self.client.get(
            f"{TARGET_URL}/Clientes/",
            name="GET /Clientes/ (list clients)"
        )
    
    @task(1)
    def dashboard(self):
        """Acessar dashboard - 10% das requisições."""
        self.client.get(
            f"{TARGET_URL}/Dashboard/",
            name="GET /Dashboard/ (dashboard)"
        )
    
    @task(1)
    def search_usuarios(self):
        """Buscar usuário - 10% das requisições."""
        search_term = random.choice(['admin', 'test', 'user', 'a'])
        self.client.get(
            f"{TARGET_URL}/Usuarios/?Buscar={search_term}",
            name="GET /Usuarios/ (search)"
        )


class HighActivityUser(HttpUser):
    """Usuário com alta atividade (40% dos usuários)."""
    tasks = [GDFTasks]
    wait_time = between(1, 3)  # Espera 1-3s entre requisições
    weight = 40


class NormalActivityUser(HttpUser):
    """Usuário normal (40% dos usuários)."""
    tasks = [GDFTasks]
    wait_time = between(3, 8)  # Espera 3-8s entre requisições
    weight = 40


class LowActivityUser(HttpUser):
    """Usuário com baixa atividade (20% dos usuários)."""
    tasks = [GDFTasks]
    wait_time = between(8, 15)  # Espera 8-15s entre requisições
    weight = 20


# Handlers para capturar eventos
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n" + "="*70)
    print("🔴 TESTE DE PERFORMANCE INICIADO")
    print("="*70)
    print(f"  Alvo: {TARGET_URL}")
    print(f"  Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("\n" + "="*70)
    print("🟢 TESTE DE PERFORMANCE FINALIZADO")
    print("="*70)
    
    # Imprimir estatísticas
    stats = environment.stats
    
    print(f"\n📊 RESULTADOS:")
    print(f"\n  Total de requisições: {stats.total.num_requests}")
    print(f"  Total de falhas: {stats.total.num_failures}")
    
    if stats.total.num_requests > 0:
        failure_rate = 100 * stats.total.num_failures / stats.total.num_requests
        print(f"  Taxa de erro: {failure_rate:.2f}%")
        
        print(f"\n  Tempo de resposta (ms):")
        print(f"    Mínimo:    {stats.total.min_response_time:.0f}")
        print(f"    Máximo:    {stats.total.max_response_time:.0f}")
        print(f"    Médio:     {stats.total.avg_response_time:.0f}")
        print(f"    Mediana:   {stats.total.get_median_response_time():.0f}")
        print(f"    95th %ile: {stats.total.get_percentile(0.95):.0f}")
        print(f"    99th %ile: {stats.total.get_percentile(0.99):.0f}")
        
        print(f"\n  Requisições por segundo: {stats.total.total_rps:.1f}")
    
    print(f"\n  Tempo total: {environment.runner.greenlet.get_elapsed_time():.0f}s")
    print("="*70 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, error, user, **kwargs):
    """Captura cada requisição individual."""
    # Pode ser usado para logging detalhado se necessário
    pass
