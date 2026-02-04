"""
Load Test para GDF_V2
Simula 100+ usuários simultâneos usando Locust
"""

from locust import HttpUser, task, between
import random


class GDFUser(HttpUser):
    """Simula comportamento de um usuário GDF"""
    
    wait_time = between(1, 3)  # Esperar entre 1-3 segundos entre requests
    
    def on_start(self):
        """Executado quando um usuário começa"""
        self.login()
    
    def login(self):
        """Fazer login"""
        # Dados de teste (ajustar conforme necessário)
        response = self.client.post('/Login/', {
            'Username': 'usuario_teste',
            'password': 'senha_teste'
        })
        
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
    
    @task(3)
    def view_home(self):
        """Acessar home - 3x mais frequente"""
        self.client.get('/home/')
    
    @task(2)
    def list_usuarios(self):
        """Listar usuários"""
        page = random.randint(1, 5)
        self.client.get(f'/Usuarios/?page={page}')
    
    @task(2)
    def list_empresas(self):
        """Listar empresas"""
        page = random.randint(1, 3)
        self.client.get(f'/Empresas/?page={page}')
    
    @task(1)
    def list_clientes(self):
        """Listar clientes"""
        self.client.get('/Clientes/?page=1')
    
    @task(1)
    def view_dashboard(self):
        """Ver dashboard"""
        self.client.get('/Dashboard/')


class GDFUserHighActivity(GDFUser):
    """Usuário com atividade alta"""
    
    wait_time = between(0.5, 2)  # Mais agressivo
    
    @task(10)
    def rapid_navigation(self):
        """Navegação rápida"""
        endpoints = ['/home/', '/Usuarios/', '/Empresas/', '/Clientes/']
        self.client.get(random.choice(endpoints))


class GDFUserLowActivity(GDFUser):
    """Usuário com atividade baixa"""
    
    wait_time = between(3, 10)  # Menos requisições
    
    @task(1)
    def check_home(self):
        """Apenas verifica a home"""
        self.client.get('/home/')


# Configuração de teste
# Para rodar:
# locust -f locustfile.py -u 100 -r 10 -t 5m --headless --csv=results
# -u: 100 usuários
# -r: 10 spawn rate (usuários por segundo)
# -t: 5 minutos
# --headless: sem UI (modo linha de comando)
# --csv: salvar resultados em CSV
