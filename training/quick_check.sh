#!/bin/bash
# Quick check - verifica se está tudo pronto

cd "$(dirname "$0")"

echo "🔍 Verificação Rápida"
echo "===================="
echo ""

# Ativar venv
source venv/bin/activate 2>/dev/null || {
    echo "❌ Virtual environment não encontrado"
    echo "   Execute: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
}

# Executar verificação
python check_ready.py
EXIT_CODE=$?

echo ""
echo "===================="

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Pronto para treinar!"
    echo ""
    echo "Execute: python train_model.py"
else
    echo "⚠️  Execute primeiro: ./setup.sh"
fi

exit $EXIT_CODE
