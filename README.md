# Pokemon Card Scanner

Sistema de reconhecimento de cartas Pokémon TCG usando ML e PWA.

## Status: MVP em desenvolvimento

**Versão atual**: v0 (setup)  
**Coleções**: 0  
**Próximo**: Treinar modelo v1 com Base Set

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
