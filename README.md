# Pokemon Card Scanner

Sistema de reconhecimento de cartas Pokémon usando OCR + Machine Learning.

## Stack
- **Backend**: Flask + OpenCV + TensorFlow Lite
- **Frontend**: React + Axios  
- **ML**: MobileNetV2 (180 cartas Prismatic Evolutions)

## Setup Rápido

```bash
# Backend
cd backend && source venv/bin/activate && python app.py

# Frontend (novo terminal)
cd frontend && npm start

# Acessar: http://localhost:3000
```

## Status Atual
- ✅ **Modelo ML treinado** (100% acurácia, 2.6MB)
- ✅ **Backend estruturado** (Flask + arquitetura limpa)
- ✅ **Frontend básico** (React + upload)
- 🔄 **Integração ML ↔ Backend** (em progresso)

## Para Desenvolvedores

📋 **Guia de Sessão**: Veja `SESSION_GUIDE.md` para estado detalhado do projeto e próximos passos.
