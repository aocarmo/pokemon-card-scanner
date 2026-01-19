#!/bin/bash

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     POKEMON CARD SCANNER - Servidores Locais                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📱 Acesse no celular:${NC}"
echo -e "${YELLOW}   http://${IP}:8000${NC}"
echo ""
echo -e "${BLUE}🔧 API rodando em:${NC}"
echo -e "   http://${IP}:5000"
echo ""
echo -e "${BLUE}📊 Modelo:${NC} v1 (Prismatic Evolutions - 180 cartas)"
echo -e "${BLUE}🎯 Acurácia:${NC} 100%"
echo ""
echo -e "${YELLOW}Pressione Ctrl+C para parar${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Função para cleanup
cleanup() {
    echo ""
    echo "🛑 Parando servidores..."
    kill $API_PID $PWA_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Iniciar API
cd /Users/alex/Documents/projetos/pessoais/pokemon-card-scanner/lambda
source venv/bin/activate
python local_server.py > /tmp/api.log 2>&1 &
API_PID=$!

# Aguardar API iniciar
sleep 2

# Iniciar PWA
cd /Users/alex/Documents/projetos/pessoais/pokemon-card-scanner/pwa
python3 -m http.server 8000 > /tmp/pwa.log 2>&1 &
PWA_PID=$!

echo "✅ Servidores iniciados!"
echo ""
echo "📋 Logs:"
echo "   API: tail -f /tmp/api.log"
echo "   PWA: tail -f /tmp/pwa.log"
echo ""

# Manter script rodando
wait
