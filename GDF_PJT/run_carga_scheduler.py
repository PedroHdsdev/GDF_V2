#!/usr/bin/env python
"""
Monitor simples de ParametroCargaXml / ParametroCargaSped (sem Redis/Celery).
Verifica a cada 30s se chegou o horário agendado e executa a tarefa no processo atual.
"""
import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GDF_PJT.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from app.db_GDF.Public.models import ParametroCargaXml, ParametroCargaSped
from app.api.carga_automatica import parametro_deve_executar_carga_automatica
from app.api.tasks import process_cargaxml_param, process_cargasped_param
from django.utils import timezone


def _label_cliente(param):
    gc = getattr(param, "gdfcliente", None)
    if gc is None:
        return "N/A"
    return (gc.razao or gc.cod_cliente or "N/A")


def run_scheduler():
    print("[SCHEDULER] Monitor de cargas agendadas (XML + SPED). Verificação a cada 30s.\n")

    while True:
        try:
            for param in ParametroCargaXml.objects.filter(ativo=True):
                if not parametro_deve_executar_carga_automatica(
                    param.horario, param.ultima_execucao
                ):
                    continue
                now = timezone.localtime()
                print(f"\n{'='*60}\n[SCHEDULER] XML param #{param.id} — cliente: {_label_cliente(param)}")
                print(
                    f"[SCHEDULER] Horário: {now.strftime('%H:%M:%S')} — {param.diretorio}\n{'='*60}"
                )
                try:
                    process_cargaxml_param.apply(args=(param.id,))
                    print("[SCHEDULER] XML: concluído.\n")
                except Exception as e:
                    print(f"[SCHEDULER] XML ✗ ERRO: {e}\n")

            for param in ParametroCargaSped.objects.filter(ativo=True):
                if not parametro_deve_executar_carga_automatica(
                    param.horario, param.ultima_execucao
                ):
                    continue
                now = timezone.localtime()
                print(f"\n{'='*60}\n[SCHEDULER] SPED param #{param.id} — cliente: {_label_cliente(param)}")
                print(
                    f"[SCHEDULER] Horário: {now.strftime('%H:%M:%S')} — {param.diretorio}\n{'='*60}"
                )
                try:
                    process_cargasped_param.apply(args=(param.id,))
                    print("[SCHEDULER] SPED: concluído.\n")
                except Exception as e:
                    print(f"[SCHEDULER] SPED ✗ ERRO: {e}\n")

            time.sleep(30)

        except Exception as e:
            print(f"[SCHEDULER] ERRO GERAL: {e}")
            time.sleep(30)


if __name__ == '__main__':
    try:
        run_scheduler()
    except KeyboardInterrupt:
        print("\n[SCHEDULER] Encerrando...")
        sys.exit(0)
