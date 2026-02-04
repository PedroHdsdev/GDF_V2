#!/usr/bin/env python3
"""
compare_baseline_results.py

Compara resultados ANTES/DEPOIS das otimizações.
Gera relatório visual com melhorias.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from tabulate import tabulate


def load_report(filepath):
    """Carrega relatório JSON."""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Erro ao parsear JSON: {filepath}")
        return None


def calculate_improvement(before, after):
    """Calcula melhoria em percentual."""
    if before == 0:
        return 0
    return ((before - after) / before) * 100


def format_improvement(before, after, higher_is_better=False):
    """Formata melhoria com cor/emoji."""
    if before == 0 or after == 0:
        return "N/A"
    
    improvement = calculate_improvement(before, after)
    
    # Para métricas onde maior é melhor (como req/s), inverter
    if higher_is_better and improvement < 0:
        improvement = -improvement
    elif not higher_is_better and improvement < 0:
        improvement = -improvement
    
    if improvement > 0:
        return f"✅ {improvement:.1f}% ↓"
    elif improvement < 0:
        return f"❌ {-improvement:.1f}% ↑"
    else:
        return f"⚪ 0%"


def print_header(text, char="="):
    """Imprime header com formato."""
    print(f"\n{char*70}")
    print(f"  {text}")
    print(f"{char*70}\n")


def compare_metrics(before_report, after_report):
    """Compara métricas sistema."""
    print_header("📊 COMPARAÇÃO DE MÉTRICAS DO SISTEMA", "═")
    
    metrics = [
        ('CPU (Média)', 
         before_report['system_metrics']['cpu']['avg'],
         after_report['system_metrics']['cpu']['avg'],
         '%', False),
        
        ('CPU (Máxima)',
         before_report['system_metrics']['cpu']['max'],
         after_report['system_metrics']['cpu']['max'],
         '%', False),
        
        ('Memória (Média)',
         before_report['system_metrics']['memory']['avg'],
         after_report['system_metrics']['memory']['avg'],
         '%', False),
        
        ('Memória (Máxima)',
         before_report['system_metrics']['memory']['max'],
         after_report['system_metrics']['memory']['max'],
         '%', False),
        
        ('Conexões PG (Média)',
         before_report['system_metrics']['postgres_connections']['avg'],
         after_report['system_metrics']['postgres_connections']['avg'],
         '', False),
        
        ('Conexões PG (Máxima)',
         before_report['system_metrics']['postgres_connections']['max'],
         after_report['system_metrics']['postgres_connections']['max'],
         '', False),
    ]
    
    table_data = []
    for name, before, after, unit, higher_better in metrics:
        improvement = format_improvement(before, after, higher_better)
        table_data.append([
            name,
            f"{before:.1f}{unit}",
            f"{after:.1f}{unit}",
            improvement
        ])
    
    print(tabulate(table_data, headers=['Métrica', 'ANTES', 'DEPOIS', 'Melhoria'],
                   tablefmt='grid'))
    
    return metrics


def compare_locust_results(before_report, after_report):
    """Compara resultados Locust."""
    print_header("📈 COMPARAÇÃO DE RESULTADOS LOCUST", "═")
    
    if not before_report.get('locust_results') or not after_report.get('locust_results'):
        print("⚠️ Resultados Locust não disponíveis em um ou ambos os relatórios")
        return
    
    before_agg = before_report['locust_results'].get('Aggregated', {})
    after_agg = after_report['locust_results'].get('Aggregated', {})
    
    if not before_agg or not after_agg:
        print("⚠️ Dados agregados não encontrados")
        return
    
    metrics = [
        ('Total Requisições',
         before_agg.get('num_requests', 0),
         after_agg.get('num_requests', 0),
         '', True),
        
        ('Falhas',
         before_agg.get('num_failures', 0),
         after_agg.get('num_failures', 0),
         '', False),
        
        ('Tempo Resposta Médio',
         before_agg.get('avg_response', 0),
         after_agg.get('avg_response', 0),
         'ms', False),
        
        ('Tempo Resposta Máximo',
         before_agg.get('max_response', 0),
         after_agg.get('max_response', 0),
         'ms', False),
        
        ('Tempo Resposta Mínimo',
         before_agg.get('min_response', 0),
         after_agg.get('min_response', 0),
         'ms', False),
        
        ('Req/s',
         before_agg.get('requests_per_sec', 0),
         after_agg.get('requests_per_sec', 0),
         '', True),
    ]
    
    table_data = []
    for name, before, after, unit, higher_better in metrics:
        improvement = format_improvement(before, after, higher_better)
        table_data.append([
            name,
            f"{before:.1f}{unit}",
            f"{after:.1f}{unit}",
            improvement
        ])
    
    print(tabulate(table_data, headers=['Métrica', 'ANTES', 'DEPOIS', 'Melhoria'],
                   tablefmt='grid'))
    
    # Taxa de erro
    if before_agg.get('num_requests', 0) > 0:
        before_error_rate = 100 * before_agg.get('num_failures', 0) / before_agg.get('num_requests', 1)
    else:
        before_error_rate = 0
    
    if after_agg.get('num_requests', 0) > 0:
        after_error_rate = 100 * after_agg.get('num_failures', 0) / after_agg.get('num_requests', 1)
    else:
        after_error_rate = 0
    
    print(f"\n  Taxa de Erro: {before_error_rate:.2f}% → {after_error_rate:.2f}% " +
          format_improvement(before_error_rate, after_error_rate, False))


def generate_summary_score(before_report, after_report):
    """Gera score geral de melhoria."""
    print_header("🏆 SCORE GERAL DE MELHORIA", "═")
    
    improvements = []
    
    # CPU
    cpu_improvement = calculate_improvement(
        before_report['system_metrics']['cpu']['avg'],
        after_report['system_metrics']['cpu']['avg']
    )
    improvements.append(cpu_improvement)
    
    # Memory
    mem_improvement = calculate_improvement(
        before_report['system_metrics']['memory']['avg'],
        after_report['system_metrics']['memory']['avg']
    )
    improvements.append(mem_improvement)
    
    # Locust results
    if before_report.get('locust_results') and after_report.get('locust_results'):
        before_agg = before_report['locust_results'].get('Aggregated', {})
        after_agg = after_report['locust_results'].get('Aggregated', {})
        
        if before_agg and after_agg:
            # Tempo de resposta (quanto menor melhor)
            resp_improvement = calculate_improvement(
                before_agg.get('avg_response', 0),
                after_agg.get('avg_response', 0)
            )
            improvements.append(resp_improvement)
            
            # Req/s (quanto maior melhor)
            req_improvement = -calculate_improvement(
                before_agg.get('requests_per_sec', 0),
                after_agg.get('requests_per_sec', 0)
            )
            improvements.append(req_improvement)
    
    # Calcular score médio
    if improvements:
        avg_improvement = sum(improvements) / len(improvements)
        
        # Classificar
        if avg_improvement >= 30:
            emoji = "🏅"
            classification = "EXCELENTE"
            color = "✅"
        elif avg_improvement >= 15:
            emoji = "🥈"
            classification = "BOM"
            color = "✅"
        elif avg_improvement >= 5:
            emoji = "🥉"
            classification = "ACEITÁVEL"
            color = "⚠️"
        else:
            emoji = "📉"
            classification = "INSUFICIENTE"
            color = "❌"
        
        print(f"{emoji} Score Geral: {avg_improvement:.1f}% {color} {classification}\n")
        
        print("Detalhes:")
        print(f"  • CPU:           {cpu_improvement:+.1f}%")
        print(f"  • Memória:       {mem_improvement:+.1f}%")
        if 'resp_improvement' in locals():
            print(f"  • Tempo Resposta: {resp_improvement:+.1f}%")
            print(f"  • Throughput:    {req_improvement:+.1f}%")
    
    return avg_improvement if improvements else 0


def main():
    """Main function."""
    print("\n" + "🔄 COMPARADOR DE BASELINE DE PERFORMANCE".center(70))
    print("(ANTES vs DEPOIS DE OTIMIZAÇÕES)".center(70))
    
    # Verificar argumentos
    if len(sys.argv) < 3:
        print("\n📋 Uso:")
        print("  python compare_baseline_results.py <arquivo_antes> <arquivo_depois>")
        print("\nExemplo:")
        print("  python compare_baseline_results.py baseline_report_BEFORE.json baseline_report_AFTER.json")
        print("\nOu encontrar automaticamente:")
        print("  python compare_baseline_results.py --auto")
        return
    
    if sys.argv[1] == '--auto':
        # Procurar automaticamente
        before_file = None
        after_file = None
        
        for f in sorted(Path('.').glob('baseline_report_*.json')):
            if 'BEFORE' in f.name:
                before_file = f
            elif 'AFTER' in f.name:
                after_file = f
        
        if not before_file or not after_file:
            print("❌ Não foi possível encontrar baseline_report_BEFORE.json ou baseline_report_AFTER.json")
            return
    else:
        before_file = Path(sys.argv[1])
        after_file = Path(sys.argv[2])
    
    # Carregar relatórios
    print(f"\n📂 Carregando relatórios...")
    print(f"   ANTES:  {before_file}")
    print(f"   DEPOIS: {after_file}")
    
    before_report = load_report(before_file)
    after_report = load_report(after_file)
    
    if not before_report or not after_report:
        print("\n❌ Erro ao carregar um ou ambos os relatórios")
        return
    
    # Imprimir informações dos testes
    print_header("ℹ️  INFORMAÇÕES DOS TESTES", "─")
    
    test_info = [
        ['Teste ANTES', before_report['test_name']],
        ['Data/Hora ANTES', before_report['timestamp']],
        ['Duração ANTES', f"{before_report['duration_seconds']}s"],
        ['', ''],
        ['Teste DEPOIS', after_report['test_name']],
        ['Data/Hora DEPOIS', after_report['timestamp']],
        ['Duração DEPOIS', f"{after_report['duration_seconds']}s"],
    ]
    
    print(tabulate(test_info, tablefmt='plain'))
    
    # Comparar
    compare_metrics(before_report, after_report)
    compare_locust_results(before_report, after_report)
    overall_score = generate_summary_score(before_report, after_report)
    
    # Recomendações
    print_header("💡 RECOMENDAÇÕES", "─")
    
    if overall_score >= 30:
        print("✅ Excelente melhoria! Otimizações foram muito efetivas.")
        print("   Considere fazer testes com carga ainda maior (próximo nível).")
    elif overall_score >= 15:
        print("✅ Boa melhoria. Aplicação está respondendo melhor.")
        print("   Considere revisar se todas as otimizações foram aplicadas.")
    elif overall_score >= 5:
        print("⚠️  Melhoria modesta. Verifique se todas as mudanças foram aplicadas.")
        print("   Pode haver outras otimizações necessárias.")
    else:
        print("❌ Pouca ou nenhuma melhoria. Revisar implementação das otimizações.")
    
    print_header("✅ ANÁLISE CONCLUÍDA", "═")
    print(f"\nRelatório gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == '__main__':
    main()
