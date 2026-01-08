# Setup Guide - macOS

## Pré-requisitos

- macOS 11+
- Python 3.11+ (recomendado usar Homebrew)
- Git

## Instalação

### 1. Instalar Python (se necessário)

```bash
# Instalar Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar Python
brew install python@3.11
```

### 2. Clonar repositório

```bash
git clone git@github.com:aocarmo/pokemon-card-scanner.git
cd pokemon-card-scanner
```

### 3. Setup do ambiente de treinamento

```bash
cd training

# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar Kaggle token

```bash
export KAGGLE_API_TOKEN=KGAT_7067eaac8267216345a44fbd1c17e433
```

Ou adicione ao seu `~/.zshrc` ou `~/.bash_profile`:
```bash
echo 'export KAGGLE_API_TOKEN=KGAT_7067eaac8267216345a44fbd1c17e433' >> ~/.zshrc
source ~/.zshrc
```

### 5. Baixar e preparar dataset

```bash
# Automático (recomendado)
./setup.sh

# Ou manual
python download_dataset.py
# Copie o path retornado
python prepare_data.py --source /path/retornado --collection prismatic-evolutions
```

### 6. Treinar modelo

```bash
python train_model.py
```

Isso vai:
- Treinar MobileNetV2 com Prismatic Evolutions
- Salvar modelo em `models/v1/`
- Levar ~1-2h dependendo do hardware

### 7. Exportar para Lambda

```bash
python export_model.py --version v1
```

Isso cria `models/v1/model.tflite` (~10-15MB)

## Deploy AWS (opcional)

### Pré-requisitos
```bash
# Instalar AWS CLI
brew install awscli

# Instalar SAM CLI
brew tap aws/tap
brew install aws-sam-cli

# Configurar credenciais
aws configure
```

### Deploy
```bash
cd ../infrastructure

# Copiar modelo para Lambda
cp ../training/models/v1/model.tflite ../lambda/model/current/
cp ../training/models/v1/labels.json ../lambda/model/current/

# Build e deploy
sam build
sam deploy --guided
```

## Estrutura de pastas

```
pokemon-card-scanner/
├── training/
│   ├── venv/              # Ambiente virtual (não commitado)
│   ├── data/
│   │   ├── collections/   # Dados organizados
│   │   └── labels.json    # Mapeamento de classes
│   └── models/
│       └── v1/            # Modelo treinado
│           ├── model.keras
│           ├── model.tflite
│           └── metadata.json
├── lambda/                # AWS Lambda
└── pwa/                   # Progressive Web App (próximo)
```

## Troubleshooting

### Erro: "No module named tensorflow"
```bash
# Certifique-se que o venv está ativado
source venv/bin/activate
pip install -r requirements.txt
```

### Erro: "KAGGLE_API_TOKEN not set"
```bash
export KAGGLE_API_TOKEN=KGAT_7067eaac8267216345a44fbd1c17e433
```

### Erro: "Out of memory" durante treinamento
Reduza o batch_size em `config.yaml`:
```yaml
training:
  batch_size: 16  # ou 8
```

### Apple Silicon (M1/M2/M3/M4)
TensorFlow funciona nativamente com aceleração GPU. Para melhor performance:

```bash
# Instalar TensorFlow otimizado para Apple Silicon
pip install tensorflow-macos
pip install tensorflow-metal

# Verificar GPU disponível
python3 -c "import tensorflow as tf; print('GPUs:', tf.config.list_physical_devices('GPU'))"
```

**Performance esperada no M4 Pro**:
- Treinamento: ~30-45min (vs 1-2h em CPU)
- Inferência: ~50-100ms por imagem
- Batch size recomendado: 64 (você tem RAM suficiente)

## Próximos passos

Após treinar o modelo v1:
1. Testar acurácia localmente
2. Deploy Lambda na AWS
3. Desenvolver PWA
4. Adicionar mais coleções (v2, v3...)

## Comandos úteis

```bash
# Ver logs de treinamento
tail -f training.log

# Testar modelo
python test_model.py --model models/v1/

# Adicionar nova coleção
python add_collection.py --collection "jungle" --source /path/to/dataset

# Re-treinar com transfer learning
python train_model.py --incremental --base-model v1
```
