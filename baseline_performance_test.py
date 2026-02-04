#!/usr/bin/env python3
"""
baseline_performance_test.py

Script para coletar métricas de baseline ANTES das otimizações.
Monitora: CPU, Memória, Conexões DB, Redis, Nginx durante teste de carga.
"""

import time
import os
import sys
import json
import psutil
import subprocess
from datetime import datetime
from pathlib import Path

# Adicionar path do projeto
sys.path.insert(0, str(Path(__file__).parent / 'GDF_PJT'))

class BaselineMonitor:
    """Monitora recursos do sistema durante testes."""
    
    def __init__(self, test_name="baseline", duration_seconds=300):
        self.test_name = test_name
        self.duration = duration_seconds
        self.start_time = None
        self.metrics = {
            'cpu': [],
            'memory': [],
            'postgres_connections': [],
            'redis_memory': [],
            'nginx_connections': [],
            'disk_io': [],
            'timestamps': []
        }
        
    def get_cpu_percent(self):
        """CPU usage %"""
        return psutil.cpu_percent(interval=0.5)
    
    def get_memory_info(self):
        """Memória em uso %"""
        return psutil.virtual_memory().percent
    
    def get_postgres_connections(self):
        """Conexões ativas PostgreSQL"""
        try:
            result = subprocess.run(
                ['sudo', '-u', 'postgres', 'psql', '-c', 
                 'SELECT count(*) FROM pg_stat_activity;'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Parse resultado
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip().isdigit():
                        return int(line.strip())
        except Exception as e:
            print(f"Erro ao obter conexões PostgreSQL: {e}")
        return 0
    
    def get_redis_memory(self):
        """Memória Redis em uso (MB)"""
        try:
            result = subprocess.run(
                ['redis-cli', 'INFO', 'memory'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'used_memory_human' in line:
                        return line.split(':')[1].strip()
        except Exception as e:
            print(f"Erro ao obter memória Redis: {e}")
        return "N/A"
    
    def get_nginx_connections(self):
        """Conexões Nginx ativas"""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Contar processos nginx
            nginx_count = result.stdout.count('nginx: worker')
            return nginx_count
        except Exception as e:
            print(f"Erro ao obter conexões Nginx: {e}")
        return 0
    
    def get_disk_io(self):
        """Leitura/Escrita disco em MB/s"""
        try:
            io_counters = psutil.disk_io_counters()
            return {
                'read_bytes': io_counters.read_bytes,
                'write_bytes': io_counters.write_bytes
            }
        except Exception as e:
            print(f"Erro ao obter I/O disco: {e}")
        return {'read_bytes': 0, 'write_bytes': 0}
    
    def collect_metrics(self):
        """Coleta um snapshot de métricas."""
        timestamp = datetime.now().isoformat()
        
        metrics_snapshot = {
            'timestamp': timestamp,
            'cpu_percent': self.get_cpu_percent(),
            'memory_percent': self.get_memory_info(),
            'postgres_connections': self.get_postgres_connections(),
            'redis_memory': self.get_redis_memory(),
            'nginx_workers': self.get_nginx_connections(),
            'disk_io': self.get_disk_io()
        }
        
        return metrics_snapshot
    
    def start(self):
        """Inicia monitoramento."""
        self.start_time = time.time()
        print(f"\n{'='*70}")
        print(f"  BASELINE PERFORMANCE TEST - {self.test_name.upper()}")
        print(f"  Duração: {self.duration} segundos")
        print(f"  Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}\n")
        
        interval = 5  # Coletar a cada 5 segundos
        
        while time.time() - self.start_time < self.duration:
            metrics = self.collect_metrics()
            self.metrics['cpu'].append(metrics['cpu_percent'])
            self.metrics['memory'].append(metrics['memory_percent'])
            self.metrics['postgres_connections'].append(metrics['postgres_connections'])
            self.metrics['redis_memory'].append(metrics['redis_memory'])
            self.metrics['nginx_connections'].append(metrics['nginx_workers'])
            self.metrics['timestamps'].append(metrics['timestamp'])
            
            elapsed = time.time() - self.start_time
            print(f"[{elapsed:.0f}s] CPU: {metrics['cpu_percent']:5.1f}% | "
                  f"MEM: {metrics['memory_percent']:5.1f}% | "
                  f"PG: {metrics['postgres_connections']:3d} | "
                  f"Redis: {metrics['redis_memory']:>6s} | "
                  f"Nginx: {metrics['nginx_workers']:2d}")
            
            time.sleep(interval)
    
    def generate_report(self, locust_results=None):
        """Gera relatório de baseline."""
        report = {
            'test_name': self.test_name,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': self.duration,
            'locust_results': locust_results,
            'system_metrics': {
                'cpu': {
                    'avg': sum(self.metrics['cpu']) / len(self.metrics['cpu']) if self.metrics['cpu'] else 0,
                    'max': max(self.metrics['cpu']) if self.metrics['cpu'] else 0,
                    'min': min(self.metrics['cpu']) if self.metrics['cpu'] else 0,
                },
                'memory': {
                    'avg': sum(self.metrics['memory']) / len(self.metrics['memory']) if self.metrics['memory'] else 0,
                    'max': max(self.metrics['memory']) if self.metrics['memory'] else 0,
                    'min': min(self.metrics['memory']) if self.metrics['memory'] else 0,
                },
                'postgres_connections': {
                    'avg': sum(self.metrics['postgres_connections']) / len(self.metrics['postgres_connections']) if self.metrics['postgres_connections'] else 0,
                    'max': max(self.metrics['postgres_connections']) if self.metrics['postgres_connections'] else 0,
                    'min': min(self.metrics['postgres_connections']) if self.metrics['postgres_connections'] else 0,
                }
            }
        }
        return report


def run_baseline_test():
    """Executa teste de baseline completo."""
    
    print("\n🔍 TESTE DE BASELINE - PERFORMANCE ANTES DAS OTIMIZAÇÕES\n")
    
    # Verificações pré-teste
    print("✓ Verificando pré-requisitos...")
    
    # 1. Verificar se Locust está instalado
    try:
        import locust
        print("  ✓ Locust instalado")
    except ImportError:
        print("  ✗ Locust não está instalado!")
        print("  Execute: pip install locust")
        return
    
    # 2. Verificar se servidor Django está rodando
    print("  ✓ Verificando se aplicação está respondendo...")
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost:8000/'],
            capture_output=True,
            timeout=5
        )
        if result.stdout.decode() in ['200', '301', '302']:
            print("  ✓ Aplicação respondendo (HTTP OK)")
        else:
            print(f"  ⚠ Aplicação retornou {result.stdout.decode()}")
    except Exception as e:
        print(f"  ✗ Não conseguiu conectar à aplicação: {e}")
        print("  Execute: cd GDF_PJT && python manage.py runserver 0.0.0.0:8000")
        return
    
    # 3. Verificar PostgreSQL
    try:
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-c', 'SELECT 1;'],
            capture_output=True,
            timeout=5
        )
        print("  ✓ PostgreSQL conectável")
    except Exception as e:
        print(f"  ⚠ PostgreSQL: {e}")
    
    # 4. Verificar Redis
    try:
        result = subprocess.run(
            ['redis-cli', 'ping'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'PONG' in result.stdout:
            print("  ✓ Redis conectável")
    except Exception as e:
        print(f"  ⚠ Redis: {e}")
    
    # Escolher cenário de teste
    print("\n📊 Escolha o cenário de teste:\n")
    print("  1. Leve (100 usuários, 5 min)")
    print("  2. Médio (300 usuários, 5 min)")
    print("  3. Pesado (500 usuários, 10 min)")
    print("  4. Customizado")
    
    choice = input("\nOpção (1-4): ").strip()
    
    scenarios = {
        '1': {'users': 100, 'spawn_rate': 10, 'duration': 300, 'name': 'Leve'},
        '2': {'users': 300, 'spawn_rate': 15, 'duration': 300, 'name': 'Médio'},
        '3': {'users': 500, 'spawn_rate': 20, 'duration': 600, 'name': 'Pesado'},
    }
    
    if choice in scenarios:
        config = scenarios[choice]
    elif choice == '4':
        users = int(input("Número de usuários: "))
        spawn_rate = int(input("Taxa de spawn (usuários/s): "))
        duration = int(input("Duração (segundos): "))
        config = {'users': users, 'spawn_rate': spawn_rate, 'duration': duration, 'name': 'Customizado'}
    else:
        print("Opção inválida!")
        return
    
    # Iniciar monitoramento
    monitor = BaselineMonitor(
        test_name=f"baseline_{config['name'].lower()}_{config['users']}_users",
        duration_seconds=config['duration'] + 30  # +30s para cleanup
    )
    
    # Executar teste com Locust
    print(f"\n▶ Iniciando teste Locust com {config['users']} usuários...")
    print(f"  Taxa de spawn: {config['spawn_rate']} usuários/s")
    print(f"  Duração: {config['duration']}s\n")
    
    # Rodar Locust em background
    locust_cmd = [
        'locust',
        '-f', 'locustfile.py',
        '-u', str(config['users']),
        '-r', str(config['spawn_rate']),
        '-t', f"{config['duration']}s",
        '--headless',
        '--csv=baseline_results'
    ]
    
    try:
        # Iniciar Locust
        locust_process = subprocess.Popen(
            locust_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Esperar 5s para Locust iniciar
        time.sleep(5)
        
        # Rodar monitoramento durante o teste
        monitor.start()
        
        # Aguardar Locust terminar
        locust_process.wait(timeout=config['duration'] + 60)
        
    except subprocess.TimeoutExpired:
        locust_process.kill()
        print("\n⚠ Teste expirou")
    except KeyboardInterrupt:
        print("\n⚠ Teste interrompido pelo usuário")
        locust_process.kill()
    except Exception as e:
        print(f"\n✗ Erro ao executar teste: {e}")
        return
    
    # Ler resultados Locust
    locust_results = None
    try:
        # Locust gera CSV com resultados
        import csv
        stats = {}
        
        # Tentar ler arquivo de stats
        try:
            with open('baseline_results_stats.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats[row['Name']] = {
                        'num_requests': int(row.get('Number of requests', 0) or 0),
                        'num_failures': int(row.get('Number of failures', 0) or 0),
                        'median_response': float(row.get('Median response time', 0) or 0),
                        'avg_response': float(row.get('Average response time', 0) or 0),
                        'min_response': float(row.get('Min response time', 0) or 0),
                        'max_response': float(row.get('Max response time', 0) or 0),
                        'avg_content_size': int(row.get('Average Content Size', 0) or 0),
                        'requests_per_sec': float(row.get('Requests/s', 0) or 0),
                    }
        except FileNotFoundError:
            pass
        
        locust_results = stats
        
    except Exception as e:
        print(f"⚠ Erro ao ler resultados Locust: {e}")
    
    # Gerar relatório
    report = monitor.generate_report(locust_results=locust_results)
    
    # Salvar relatório
    report_file = f"baseline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print("📋 RELATÓRIO DE BASELINE")
    print(f"{'='*70}\n")
    
    print(f"Teste: {report['test_name']}")
    print(f"Data: {report['timestamp']}")
    print(f"Duração: {report['duration_seconds']}s\n")
    
    print("📊 Métricas de Sistema:")
    print(f"  CPU:")
    print(f"    Média:  {report['system_metrics']['cpu']['avg']:.1f}%")
    print(f"    Máxima: {report['system_metrics']['cpu']['max']:.1f}%")
    print(f"    Mínima: {report['system_metrics']['cpu']['min']:.1f}%")
    
    print(f"\n  Memória:")
    print(f"    Média:  {report['system_metrics']['memory']['avg']:.1f}%")
    print(f"    Máxima: {report['system_metrics']['memory']['max']:.1f}%")
    print(f"    Mínima: {report['system_metrics']['memory']['min']:.1f}%")
    
    print(f"\n  Conexões PostgreSQL:")
    print(f"    Média:  {report['system_metrics']['postgres_connections']['avg']:.0f}")
    print(f"    Máxima: {report['system_metrics']['postgres_connections']['max']:.0f}")
    print(f"    Mínima: {report['system_metrics']['postgres_connections']['min']:.0f}")
    
    if locust_results:
        print(f"\n📈 Resultados Locust:")
        for endpoint, stats in locust_results.items():
            if endpoint != 'Aggregated':
                print(f"\n  {endpoint}:")
                print(f"    Requisições: {stats['num_requests']}")
                print(f"    Falhas: {stats['num_failures']}")
                print(f"    Tempo médio: {stats['avg_response']:.0f}ms")
                print(f"    Tempo máximo: {stats['max_response']:.0f}ms")
                print(f"    Req/s: {stats['requests_per_sec']:.1f}")
        
        if 'Aggregated' in locust_results:
            agg = locust_results['Aggregated']
            print(f"\n  TOTAL:")
            print(f"    Requisições: {agg['num_requests']}")
            print(f"    Falhas: {agg['num_failures']} ({100*agg['num_failures']/max(agg['num_requests'], 1):.2f}%)")
            print(f"    Tempo médio: {agg['avg_response']:.0f}ms")
            print(f"    Req/s: {agg['requests_per_sec']:.1f}")
    
    print(f"\n✅ Relatório salvo em: {report_file}")
    print(f"\n{'='*70}\n")


if __name__ == '__main__':
    run_baseline_test()
