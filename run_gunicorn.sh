#!/bin/bash
# Script para iniciar múltiplos workers Gunicorn para GDF_V2
# Uso: bash run_gunicorn.sh [numero_workers]

NUM_WORKERS=${1:-3}
BASE_PORT=8000

echo "🚀 Iniciando $NUM_WORKERS workers Gunicorn para GDF_V2..."

# Criar diretório de logs se não existir
mkdir -p logs

# Limpar processos Gunicorn anteriores
pkill -f "gunicorn.*GDF_PJT" || true
sleep 1

# Iniciar múltiplos workers
for i in $(seq 0 $((NUM_WORKERS - 1))); do
    PORT=$((BASE_PORT + i))
    LOG_FILE="logs/gunicorn_${PORT}.log"
    
    echo "📍 Iniciando worker $i na porta $PORT (log: $LOG_FILE)"
    
    cd GDF_PJT
    gunicorn \
        --bind 127.0.0.1:$PORT \
        --workers 2 \
        --worker-class sync \
        --timeout 30 \
        --access-logfile "$LOG_FILE" \
        --error-logfile "$LOG_FILE" \
        --log-level info \
        GDF_PJT.wsgi &
    
    cd ..
    
    sleep 0.5
done

echo "✅ Todos os $NUM_WORKERS workers iniciados!"
echo ""
echo "📊 URLs dos workers:"
for i in $(seq 0 $((NUM_WORKERS - 1))); do
    PORT=$((BASE_PORT + i))
    echo "   - http://127.0.0.1:$PORT"
done

echo ""
echo "⚙️  Configure Nginx para fazer load balance entre:"
for i in $(seq 0 $((NUM_WORKERS - 1))); do
    PORT=$((BASE_PORT + i))
    echo "   server 127.0.0.1:$PORT;"
done

echo ""
echo "🛑 Para parar todos os workers: pkill -f 'gunicorn.*GDF_PJT'"
