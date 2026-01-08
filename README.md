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

# Configurar Kaggle
mkdir ~/.kaggle
# Copiar kaggle.json para ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Baixar e preparar Base Set
python download_dataset.py
python prepare_data.py --collection "Base Set"

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
- [docs/API.md](docs/API.md) - Documentação da API
- [docs/ADD_COLLECTION.md](docs/ADD_COLLECTION.md) - Como adicionar coleções

## Roadmap

- [ ] MVP: Modelo v1 com Base Set
- [ ] Lambda deployment
- [ ] PWA básica
- [ ] Adicionar Jungle (v2)
- [ ] Adicionar Fossil (v3)

## Licença

Uso pessoal
