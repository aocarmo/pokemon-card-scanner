.PHONY: help install train backend frontend clean

help:
	@echo "Pokemon Card Scanner - Comandos disponíveis:"
	@echo ""
	@echo "  make install     - Instala todas as dependências"
	@echo "  make train       - Treina o modelo de ML"
	@echo "  make backend     - Inicia API Flask"
	@echo "  make frontend    - Inicia React app"
	@echo "  make dev         - Inicia backend + frontend"
	@echo "  make clean       - Remove arquivos temporários"
	@echo ""

install:
	@echo "📦 Instalando dependências..."
	cd backend && python3 -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	brew install tesseract tesseract-lang || true
	@echo "✅ Instalação completa!"

train:
	@echo "🎯 Treinando modelo..."
	cd machine-learning && . venv/bin/activate && python train_model.py
	@echo "✅ Modelo treinado!"

backend:
	@echo "🚀 Iniciando backend..."
	cd backend && . venv/bin/activate && python app.py

frontend:
	@echo "🚀 Iniciando frontend..."
	cd frontend && npm start

dev:
	@echo "🚀 Iniciando ambiente de desenvolvimento..."
	@make -j2 backend frontend

clean:
	@echo "🧹 Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Limpeza completa!"
