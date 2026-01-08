# Otimizações para Apple Silicon (M4 Pro)

## Performance

O M4 Pro tem excelente performance para ML:
- **GPU**: 20-core (M4 Pro)
- **Neural Engine**: 16-core
- **RAM unificada**: Compartilhada entre CPU/GPU

## Configurações otimizadas

### 1. TensorFlow com Metal

```bash
pip install tensorflow-macos tensorflow-metal
```

Isso habilita aceleração GPU automática.

### 2. Batch size aumentado

Em `config.yaml`:
```yaml
batch_size: 64  # M4 Pro aguenta tranquilo
```

### 3. Mixed precision (opcional)

Para treinar ainda mais rápido, adicione em `train_model.py`:

```python
from tensorflow.keras import mixed_precision
mixed_precision.set_global_policy('mixed_float16')
```

Isso pode acelerar 2-3x com mínima perda de acurácia.

## Benchmarks esperados (M4 Pro)

### Treinamento (Prismatic Evolutions ~200 cartas)
- **Sem GPU**: ~2h
- **Com Metal**: ~30-45min
- **Com mixed precision**: ~20-30min

### Inferência
- **Por imagem**: 50-100ms
- **Batch de 32**: ~1s

## Monitoramento

```bash
# Ver uso de GPU durante treinamento
sudo powermetrics --samplers gpu_power -i 1000

# Ver uso de memória
activity monitor -> GPU History
```

## Dicas

1. **Feche apps pesados** durante treinamento (Chrome, etc)
2. **Conecte na tomada** (performance throttle em bateria)
3. **Ventilação**: Deixe espaço para ventilação
4. **Primeira época é lenta**: TensorFlow compila o grafo

## Troubleshooting

### GPU não detectada
```bash
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

Se vazio, reinstale:
```bash
pip uninstall tensorflow tensorflow-macos tensorflow-metal
pip install tensorflow-macos tensorflow-metal
```

### Out of memory
Reduza batch_size para 32 ou 16.

### Muito lento
Verifique se Metal está instalado:
```bash
pip show tensorflow-metal
```
