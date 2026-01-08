# Projeto: Pokemon Card Scanner

## Objetivo
Criar um sistema de reconhecimento de cartas Pokémon TCG usando câmera do celular para catalogar estoque automaticamente.

## Requisitos
- **Dataset**: Incremental - começar com 1 coleção, expandir gradualmente
- **Identificação**: Nome da carta, coleção, número
- **Interface**: PWA com câmera
- **Armazenamento**: CSV com contador de cartas
- **Infraestrutura**: AWS Lambda (custo mínimo)
- **Treinamento**: Local, re-treinar ao adicionar coleções

---

## Arquitetura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   PWA       │─────▶│ API Gateway  │─────▶│   Lambda    │
│  (Camera)   │      │              │      │  (Modelo)   │
└─────────────┘      └──────────────┘      └─────────────┘
      │                                            │
      │                                            ▼
      │                                     ┌─────────────┐
      └────────────────────────────────────▶│   S3 CSV    │
                                            └─────────────┘
```

### Componentes

1. **Modelo ML** (MobileNetV2 - Incremental)
   - Leve para Lambda (< 50MB)
   - Classificação dinâmica (começa com ~200 cartas, expande)
   - Formato: TensorFlow Lite
   - **Versionamento**: model_v1.tflite, model_v2.tflite...

2. **Lambda Function** (Python 3.11)
   - Runtime: < 512MB RAM
   - Timeout: 30s
   - Recebe imagem base64
   - Retorna: {nome, colecao, numero, confianca, versao_modelo}

3. **PWA**
   - Captura foto via Camera API
   - Comprime imagem (max 800px)
   - Envia para Lambda
   - Atualiza CSV local/S3
   - Contador de cartas
   - **Indicador de versão do modelo**

4. **Armazenamento**
   - CSV: nome,colecao,numero,quantidade,ultima_atualizacao
   - S3: modelos versionados + datasets

---

## Estrutura do Projeto (Modular)

```
pokemon-card-scanner/
├── README.md
├── PLAN.md (este arquivo)
│
├── training/                      # Treinamento incremental
│   ├── requirements.txt
│   ├── download_dataset.py        # Baixa dataset do Kaggle
│   ├── prepare_data.py            # Organiza imagens por classe
│   ├── train_model.py             # Treina/Re-treina modelo
│   ├── export_model.py            # Exporta para TFLite
│   ├── test_model.py              # Testa acurácia
│   ├── add_collection.py          # ⭐ Adiciona nova coleção
│   ├── config.yaml                # ⭐ Configuração de coleções
│   │
│   ├── data/
│   │   ├── collections/           # ⭐ Organizado por coleção
│   │   │   ├── base_set/
│   │   │   ├── jungle/
│   │   │   └── fossil/
│   │   └── labels.json            # Mapeamento global
│   │
│   └── models/                    # ⭐ Modelos versionados
│       ├── v1_base_set/
│       │   ├── model.tflite
│       │   ├── labels.json
│       │   └── metadata.json
│       ├── v2_base_jungle/
│       └── v3_all/
│
├── lambda/                        # AWS Lambda
│   ├── requirements.txt
│   ├── handler.py                 # Lambda handler
│   ├── inference.py               # Lógica de inferência
│   ├── model/
│   │   ├── current/               # ⭐ Modelo ativo
│   │   │   ├── model.tflite
│   │   │   └── labels.json
│   │   └── versions/              # ⭐ Histórico
│   ├── Dockerfile
│   └── deploy.sh
│
├── pwa/                           # Progressive Web App
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   ├── manifest.json
│   ├── service-worker.js
│   └── icons/
│
├── infrastructure/
│   ├── template.yaml
│   └── deploy.sh
│
└── docs/
    ├── API.md
    ├── USAGE.md
    └── ADD_COLLECTION.md          # ⭐ Como adicionar coleções
```

---

## Estratégia Incremental

### Fase 0: MVP - 1 Coleção (Base Set)

**Objetivo**: Validar pipeline completo com dataset pequeno

**Escopo**:
- 1 coleção (~200-300 cartas)
- Modelo v1
- PWA básica
- Lambda funcional

**Vantagens**:
- Treinamento rápido (~30min)
- Deploy rápido
- Feedback imediato
- Baixo custo de iteração

---

### Fase 1+: Expansão Gradual

**Processo de Adicionar Coleção**:

1. **Preparar Dataset**
   ```bash
   cd training
   python add_collection.py --collection "Jungle"
   ```

2. **Re-treinar Modelo**
   ```bash
   python train_model.py --incremental --base-model v1
   ```
   - Transfer learning do modelo anterior
   - Apenas fine-tuning (mais rápido)
   - Preserva conhecimento anterior

3. **Exportar Nova Versão**
   ```bash
   python export_model.py --version v2 --collections "Base Set,Jungle"
   ```

4. **Deploy Lambda**
   ```bash
   cd lambda
   ./deploy.sh --model v2
   ```

5. **Testar PWA**
   - Verificar reconhecimento de ambas coleções
   - Validar acurácia

---

## Etapas de Desenvolvimento

### Fase 0: MVP - 1 Coleção ✓ (Começar aqui)

#### 0.1 Setup do Projeto
- [ ] Criar estrutura de diretórios
- [ ] Configurar ambiente Python
- [ ] Instalar dependências

#### 0.2 Dataset - Base Set
- [ ] Baixar dataset Kaggle
- [ ] Filtrar apenas Base Set
- [ ] Organizar em `data/collections/base_set/`
- [ ] Gerar `labels.json` para Base Set
- [ ] Validar: ~200-300 cartas

#### 0.3 Treinamento v1
- [ ] Configurar MobileNetV2
- [ ] Treinar com Base Set
- [ ] Validar acurácia > 85%
- [ ] Exportar `model_v1.tflite`
- [ ] Salvar metadata (coleções, data, acurácia)

#### 0.4 Lambda v1
- [ ] Criar handler básico
- [ ] Integrar modelo v1
- [ ] Testar localmente
- [ ] Deploy AWS
- [ ] Testar endpoint

#### 0.5 PWA v1
- [ ] Interface de câmera
- [ ] Upload e predição
- [ ] Exibir resultado
- [ ] CSV básico
- [ ] Testar em mobile

**Validação MVP**:
- [ ] Reconhece cartas do Base Set com >85% acurácia
- [ ] PWA funciona em mobile
- [ ] CSV atualiza corretamente
- [ ] Custo < $1/mês

---

### Fase 1: Adicionar 2ª Coleção (Jungle)

#### 1.1 Preparar Dataset
- [ ] Executar `add_collection.py --collection Jungle`
- [ ] Validar organização em `data/collections/jungle/`
- [ ] Atualizar `labels.json` global

#### 1.2 Re-treinar v2
- [ ] Transfer learning de v1
- [ ] Treinar com Base Set + Jungle
- [ ] Validar acurácia > 85% em ambas
- [ ] Exportar `model_v2.tflite`

#### 1.3 Deploy v2
- [ ] Atualizar Lambda com v2
- [ ] Testar reconhecimento de ambas coleções
- [ ] Validar backward compatibility (Base Set ainda funciona)

---

### Fase 2+: Expansão Contínua

**Repetir processo**:
1. Adicionar coleção
2. Re-treinar
3. Deploy
4. Validar

**Coleções Planejadas** (exemplo):
- v1: Base Set
- v2: Base Set + Jungle
- v3: Base Set + Jungle + Fossil
- v4: Base Set + Jungle + Fossil + Team Rocket
- v5: Todas as 5 coleções iniciais

---

## Configuração Incremental

### config.yaml (Training)

```yaml
# Configuração de coleções ativas
version: 2
collections:
  - name: "Base Set"
    enabled: true
    path: "data/collections/base_set"
    cards: 102
  - name: "Jungle"
    enabled: true
    path: "data/collections/jungle"
    cards: 64
  - name: "Fossil"
    enabled: false  # Ainda não adicionada
    path: "data/collections/fossil"
    cards: 62

# Configuração de treinamento
training:
  base_model: "mobilenet_v2"
  image_size: 224
  batch_size: 32
  epochs: 20
  learning_rate: 0.001
  
  # Transfer learning
  incremental: true
  freeze_layers: 100  # Congelar primeiras N camadas

# Exportação
export:
  format: "tflite"
  quantization: true
  optimize_for: "size"  # ou "latency"
```

### metadata.json (Modelo)

```json
{
  "version": "v2",
  "created_at": "2026-01-07T22:45:00Z",
  "collections": ["Base Set", "Jungle"],
  "total_classes": 166,
  "accuracy": {
    "overall": 0.92,
    "per_collection": {
      "Base Set": 0.94,
      "Jungle": 0.89
    }
  },
  "model_size_mb": 12.5,
  "base_model": "v1"
}
```

---

## Script: add_collection.py

```python
#!/usr/bin/env python3
"""
Adiciona nova coleção ao dataset de treinamento
"""

import argparse
import yaml
from pathlib import Path

def add_collection(collection_name: str, source_path: str):
    """
    1. Copia imagens para data/collections/{collection}/
    2. Atualiza config.yaml
    3. Atualiza labels.json
    4. Valida estrutura
    """
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    
    add_collection(args.collection, args.source)
```

---

## Script: train_model.py (Incremental)

```python
#!/usr/bin/env python3
"""
Treina modelo com suporte a transfer learning
"""

import argparse
import yaml

def train_model(config_path: str, incremental: bool, base_model: str):
    """
    1. Carrega config.yaml
    2. Carrega coleções ativas
    3. Se incremental: carrega base_model e congela camadas
    4. Treina apenas com novas classes ou fine-tuning
    5. Salva novo modelo versionado
    """
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--base-model", default=None)
    args = parser.parse_args()
    
    train_model(args.config, args.incremental, args.base_model)
```

---

## Versionamento de Modelos

### Estratégia

1. **Semantic Versioning**: v{major}.{minor}
   - Major: Mudança de arquitetura
   - Minor: Adição de coleções

2. **Armazenamento**:
   ```
   models/
   ├── v1/
   │   ├── model.tflite
   │   ├── labels.json
   │   └── metadata.json
   ├── v2/
   └── current -> v2/  # Symlink
   ```

3. **Lambda**:
   - Sempre usa `current/`
   - Deploy atualiza symlink
   - Rollback = mudar symlink

4. **PWA**:
   - Exibe versão do modelo
   - Alerta se modelo desatualizado

---

## Workflow de Expansão

```bash
# 1. Adicionar nova coleção
cd training
python add_collection.py \
  --collection "Jungle" \
  --source ~/Downloads/jungle_cards/

# 2. Verificar config
cat config.yaml

# 3. Re-treinar (incremental)
python train_model.py \
  --incremental \
  --base-model v1

# 4. Testar novo modelo
python test_model.py --model models/v2/

# 5. Exportar
python export_model.py --version v2

# 6. Deploy Lambda
cd ../lambda
./deploy.sh --model ../training/models/v2/

# 7. Testar endpoint
curl -X POST https://api.../predict \
  -H "Content-Type: application/json" \
  -d '{"image": "base64..."}'

# 8. Validar PWA
# Abrir app e testar cartas de ambas coleções
```

---

## Estimativa de Tempo

### MVP (1 coleção)
- Setup: 30min
- Dataset: 1h
- Treinamento: 1-2h (depende do hardware)
- Lambda: 1h
- PWA: 2h
- **Total: ~6h**

### Adicionar Coleção
- Preparar dataset: 30min
- Re-treinar: 30min-1h (transfer learning é rápido)
- Deploy: 15min
- Testes: 30min
- **Total: ~2h por coleção**

---

## Tecnologias

### Treinamento
- Python 3.11
- TensorFlow 2.15
- Keras
- NumPy, Pillow
- PyYAML (config)
- Kaggle CLI

### Lambda
- Python 3.11
- TensorFlow Lite
- AWS Lambda (Container)
- API Gateway

### PWA
- HTML5 + CSS3
- JavaScript (Vanilla)
- Camera API
- Service Worker
- LocalStorage

### Infraestrutura (IaC)
- **AWS SAM** (Serverless Application Model)
- CloudFormation
- ECR (Container Registry)

---

## Estimativa de Custos (AWS)

**MVP (1 coleção, 500 predições/mês)**:
- Lambda: $0.10
- API Gateway: $0.01
- S3: $0.03
- **Total: ~$0.14/mês**

**5 coleções (2000 predições/mês)**:
- Lambda: $0.40
- API Gateway: $0.02
- S3: $0.05
- **Total: ~$0.47/mês**

---

## Próximos Passos

### Agora (MVP)
1. ✅ Criar estrutura do projeto
2. ⏳ Baixar dataset Kaggle
3. ⏳ Filtrar apenas Base Set
4. ⏳ Treinar modelo v1
5. ⏳ Criar Lambda
6. ⏳ Desenvolver PWA

### Depois (Expansão)
7. Adicionar Jungle
8. Re-treinar v2
9. Adicionar Fossil
10. Re-treinar v3
11. ...

---

## Comandos Úteis

### Deploy AWS (SAM)
```bash
# Build e deploy
cd infrastructure
sam build
sam deploy --guided  # Primeira vez
./deploy.sh v1       # Deploys subsequentes

# Logs
sam logs -n PokemonCardFunction --tail

# Deletar stack
sam delete --stack-name pokemon-card-scanner
```

### Setup Inicial
```bash
# Criar projeto
mkdir pokemon-card-scanner && cd pokemon-card-scanner

# Criar estrutura
mkdir -p training/{data/collections,models}
mkdir -p lambda/model/current
mkdir -p pwa

# Instalar dependências
cd training
python -m venv venv
source venv/bin/activate
pip install tensorflow pillow pyyaml kaggle
```

### MVP - Base Set
```bash
# Baixar dataset
cd training
kaggle datasets download -d ellimaaac/pokemon-tcg-all-image-cards
unzip pokemon-tcg-all-image-cards.zip -d data/raw/

# Preparar Base Set
python prepare_data.py --collection "Base Set"

# Treinar v1
python train_model.py --config config.yaml

# Exportar
python export_model.py --version v1

# Testar
python test_model.py --model models/v1/
```

### Adicionar Coleção
```bash
# Adicionar Jungle
python add_collection.py --collection "Jungle" --source data/raw/jungle/

# Re-treinar
python train_model.py --incremental --base-model v1

# Exportar v2
python export_model.py --version v2

# Deploy
cd ../lambda
./deploy.sh --model ../training/models/v2/
```

---

## Notas Importantes

### Transfer Learning
- **Vantagem**: Re-treinar é 5-10x mais rápido
- **Técnica**: Congelar primeiras camadas, treinar apenas últimas
- **Cuidado**: Validar que coleções antigas não perderam acurácia

### Versionamento
- Sempre manter modelos anteriores
- Facilita rollback se v2 tiver problemas
- Permite comparar acurácia entre versões

### Dataset Incremental
- Organizar por coleção desde o início
- Facilita adicionar/remover coleções
- Permite treinar subconjuntos

### Testes
- Sempre testar coleções antigas após adicionar novas
- Validar que acurácia não caiu
- Testar casos edge (cartas similares de coleções diferentes)

---

## Referências

- [Kaggle Dataset](https://www.kaggle.com/datasets/ellimaaac/pokemon-tcg-all-image-cards)
- [TensorFlow Transfer Learning](https://www.tensorflow.org/tutorials/images/transfer_learning)
- [TensorFlow Lite](https://www.tensorflow.org/lite)
- [AWS Lambda Container](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
- [PWA Camera API](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia)

---

## Changelog

- **2026-01-07 22:45**: Ajustado para estratégia incremental
  - Começar com 1 coleção (MVP)
  - Adicionar coleções gradualmente
  - Transfer learning para re-treinar
  - Versionamento de modelos
- **2026-01-07 22:37**: Planejamento inicial
