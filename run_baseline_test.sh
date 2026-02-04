#!/bin/bash
# run_baseline_test.sh
# Script para rodar teste de baseline em GDF_V2
# Uso: bash run_baseline_test.sh

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   🧪 TESTE DE BASELINE - GDF_V2                              ║"
echo "║   Performance ANTES de otimizações                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar pré-requisitos
echo "📋 Verificando pré-requisitos..."

# Verificar se está no diretório correto
if [ ! -f "baseline_performance_test.py" ]; then
    echo -e "${RED}❌ Erro: baseline_performance_test.py não encontrado${NC}"
    echo "Execute este script do diretório GDF_V2:"
    echo "  cd GDF_V2 && bash run_baseline_test.sh"
    exit 1
fi

# Verificar PostgreSQL
if ! sudo -u postgres psql -c "SELECT 1;" &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL não está rodando${NC}"
    echo "Inicie com: sudo systemctl start postgresql"
    exit 1
fi
echo -e "${GREEN}  ✓ PostgreSQL OK${NC}"

# Verificar Redis
if ! redis-cli ping &> /dev/null | grep -q PONG; then
    echo -e "${RED}❌ Redis não está rodando${NC}"
    echo "Inicie com: redis-server ou sudo systemctl start redis-server"
    exit 1
fi
echo -e "${GREEN}  ✓ Redis OK${NC}"

# Verificar Django
if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${RED}❌ Django não está respondendo em localhost:8000${NC}"
    echo "Inicie com:"
    echo "  cd GDF_PJT && python manage.py runserver 0.0.0.0:8000"
    exit 1
fi
echo -e "${GREEN}  ✓ Django OK${NC}"

# Verificar Locust
if ! python -c "import locust" 2> /dev/null; then
    echo -e "${YELLOW}⚠️  Locust não está instalado${NC}"
    echo "Instalando Locust..."
    pip install locust psutil tabulate
fi
echo -e "${GREEN}  ✓ Locust OK${NC}"

# Verificar psutil
if ! python -c "import psutil" 2> /dev/null; then
    echo -e "${YELLOW}⚠️  psutil não está instalado${NC}"
    pip install psutil
fi
echo -e "${GREEN}  ✓ psutil OK${NC}"

# Limpar testes anteriores
echo ""
echo "🧹 Limpando testes anteriores..."
rm -f baseline_results*.csv
rm -f baseline_report_*.json
echo -e "${GREEN}  ✓ Limpeza concluída${NC}"

# Informações do servidor
echo ""
echo "📊 Informações do Servidor:"
echo "  CPU cores: $(nproc)"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  Disco: $(df -h / | tail -1 | awk '{print $4}' ) disponível"

# Informações de banco
PG_CONN=$(sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | grep -oE '[0-9]+' | head -1)
echo "  PostgreSQL conexões: $PG_CONN ativas"

REDIS_MEM=$(redis-cli INFO memory | grep used_memory_human | cut -d: -f2)
echo "  Redis memória: $REDIS_MEM"

# Escolher cenário
echo ""
echo "📋 Escolha o cenário de teste:"
echo ""
echo "  1) Leve (100 usuários, 5 min)      - RECOMENDADO PARA COMEÇAR"
echo "  2) Médio (300 usuários, 5 min)"
echo "  3) Pesado (500 usuários, 10 min)"
echo "  4) Custom (configurar manualmente)"
echo ""
read -p "Opção (1-4): " scenario

# Mapear cenários
case $scenario in
    1|2|3)
        echo ""
        echo -e "${GREEN}✓ Cenário escolhido: $scenario${NC}"
        ;;
    4)
        echo ""
        read -p "Número de usuários: " users
        read -p "Taxa de spawn (usuários/s): " spawn_rate
        read -p "Duração (segundos): " duration
        echo -e "${GREEN}✓ Cenário customizado: $users usuários${NC}"
        ;;
    *)
        echo -e "${RED}❌ Opção inválida!${NC}"
        exit 1
        ;;
esac

# Iniciar teste
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   ▶️  INICIANDO TESTE                                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

python baseline_performance_test.py <<EOF
$scenario
EOF

# Depois do teste
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   ✅ TESTE CONCLUÍDO                                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Encontrar relatório mais recente
REPORT=$(ls -t baseline_report_*.json 2>/dev/null | head -1)

if [ ! -z "$REPORT" ]; then
    echo "📂 Relatório: $REPORT"
    echo ""
    
    # Salvar como BEFORE
    read -p "Salvar como baseline_report_BEFORE.json? (s/n): " save_before
    if [[ $save_before == "s" || $save_before == "S" ]]; then
        cp "$REPORT" baseline_report_BEFORE.json
        echo -e "${GREEN}✓ Salvo em: baseline_report_BEFORE.json${NC}"
    fi
    
    echo ""
    echo "📊 Próximos passos:"
    echo ""
    echo "1. Guardar este resultado como baseline:"
    echo "   cp $REPORT baseline_report_BEFORE.json"
    echo ""
    echo "2. Fazer upgrades (1 semana):"
    echo "   cat UPGRADE_1000_USUARIOS_SERVIDOR.md"
    echo ""
    echo "3. Rodar teste NOVAMENTE:"
    echo "   bash run_baseline_test.sh"
    echo "   # Escolher MESMA opção"
    echo ""
    echo "4. Comparar resultados:"
    echo "   python compare_baseline_results.py baseline_report_BEFORE.json baseline_report_AFTER.json"
    echo ""
else
    echo -e "${RED}❌ Não foi possível encontrar relatório${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Tudo pronto!${NC}"
echo ""
