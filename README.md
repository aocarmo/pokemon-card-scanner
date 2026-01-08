# Pokemon Card Scanner

Sistema de reconhecimento de cartas Pokémon TCG usando ML e PWA.

## Status: Pronto para treinar modelo

**Versão atual**: v0 (setup completo)  
**Coleções**: 0 (Prismatic Evolutions preparado)  

### ✅ Concluído:
- [x] Estrutura do projeto
- [x] Scripts de treinamento (kagglehub)
- [x] Lambda + SAM IaC
- [x] PWA completo
- [x] Flask API local
- [x] Otimizações M4 Pro
- [x] Documentação completa

### 🎯 PRÓXIMO PASSO (no Mac):

**1. Treinar modelo v1 com Prismatic Evolutions**

```bash
cd training
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export KAGGLE_API_TOKEN=KGAT_7067eaac8267216345a44fbd1c17e433
./setup.sh  # Baixa dataset e prepara dados

python train_model.py  # ~30-45min no M4 Pro
python export_model.py --version v1
```

**2. Testar localmente (Mac + Celular)**

```bash
# Copiar modelo
mkdir -p ../lambda/model/current
cp models/v1/model.tflite ../lambda/model/current/
cp data/labels.json ../lambda/model/current/

# Terminal 1: API
cd ../lambda
pip install -r requirements-local.txt
python local_server.py

# Terminal 2: PWA
cd ../pwa
python3 -m http.server 8000

# Celular: http://SEU_IP_MAC:8000
```

### 📋 Quando voltar no Mac:

1. Clone o repo: `git clone git@github.com:aocarmo/pokemon-card-scanner.git`
2. Siga: **[docs/SETUP_MACOS.md](docs/SETUP_MACOS.md)**
3. Me diga onde parou ou se teve algum erro

## Quick Start

```bash
# Setup treinamento
cd training
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Baixar dataset (Prismatic Evolutions)
python download_dataset.py
# Copie o path retornado

# Preparar dados
python prepare_data.py --source /path/from/kagglehub --collection prismatic-evolutions

# Treinar modelo v1
python train_model.py

# Exportar para Lambda
python export_model.py --version v1
```

## Estrutura

```
pokemon-card-scanner/
├── training/          # Treinamento de modelos
├── lambda/            # AWS Lambda API
├── pwa/               # Progressive Web App
└── infrastructure/    # Deploy configs
```

## Documentação

- [PLAN.md](PLAN.md) - Planejamento completo e roadmap
- [docs/SETUP_MACOS.md](docs/SETUP_MACOS.md) - **Setup para macOS** (comece aqui!)
- [docs/API.md](docs/API.md) - Documentação da API
- [docs/ADD_COLLECTION.md](docs/ADD_COLLECTION.md) - Como adicionar coleções

## Roadmap

- [x] Estrutura do projeto
- [x] Scripts de treinamento
- [x] Lambda + SAM IaC
- [x] Download dataset com kagglehub
- [x] Script de setup automatizado
- [ ] **PRÓXIMO**: Executar setup e treinar modelo v1
- [ ] Testar modelo localmente
- [ ] Deploy Lambda
- [ ] PWA básica
- [ ] Adicionar mais coleções

## Licença

Uso pessoal
