#!/usr/bin/env python
"""
Simple job scheduler for ParametroCargaXml - doesn't require Redis/Celery
Monitors database for scheduled loads and executes them when time arrives
"""
import os
import sys
import django
import time
from datetime import datetime
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GDF_PJT.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from app.db_GDF.Public.models import ParametroCargaXml
from app.tasks import process_cargaxml_param
from django.utils import timezone

def run_scheduler():
    """Monitor and execute scheduled jobs"""
    print("[SCHEDULER] Iniciando monitor de cargas agendadas...")
    print(f"[SCHEDULER] Verificando a cada 30 segundos\n")
    
    executed_ids = set()
    
    while True:
        try:
            now = timezone.now()
            current_time = now.time()
            
            # Buscar todos os parâmetros agendados
            params = ParametroCargaXml.objects.filter(ativo=True)
            
            for param in params:
                if param.id in executed_ids:
                    continue
                
                # Verificar se é hora de executar
                # param.horario é um TimeField (HH:MM)
                if param.horario and current_time >= param.horario:
                    # Verificar se já não foi executado hoje
                    last_execution = param.ultima_execucao
                    
                    if last_execution is None or last_execution.date() != now.date():
                        print(f"\n{'='*60}")
                        print(f"[SCHEDULER] ✓ EXECUTANDO")
                        print(f"[SCHEDULER] Cliente: {param.cliente.razao if param.cliente else 'N/A'}")
                        print(f"[SCHEDULER] Horário: {current_time.strftime('%H:%M:%S')}")
                        print(f"[SCHEDULER] Diretório: {param.diretorio}")
                        print(f"{'='*60}")
                        
                        try:
                            # Executar a tarefa
                            result = process_cargaxml_param(param.id)
                            
                            # Atualizar data de execução
                            param.ultima_execucao = now
                            param.save(update_fields=['ultima_execucao'])
                            
                            executed_ids.add(param.id)
                            
                            print(f"[SCHEDULER] Status: SUCESSO")
                            print(f"[SCHEDULER] Próxima execução: amanhã às {param.horario}\n")
                            
                        except Exception as e:
                            print(f"[SCHEDULER] ✗ ERRO: {str(e)}\n")
            
            # Limpar IDs já executados (apenas manter os do dia atual)
            if datetime.now().hour == 23 and datetime.now().minute == 59:
                executed_ids.clear()
            
            # Aguardar 30 segundos para próxima verificação
            time.sleep(30)
            
        except Exception as e:
            print(f"[SCHEDULER] ERRO GERAL: {str(e)}")
            time.sleep(30)

if __name__ == '__main__':
    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("\n[SCHEDULER] Encerrando...")
        sys.exit(0)
