# Teste Local - Mac + Celular

## Arquitetura Local

```
┌─────────────┐         ┌──────────────┐
│   Celular   │────────▶│  Mac (WiFi)  │
│   (PWA)     │  HTTP   │  Flask API   │
└─────────────┘         └──────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │ Modelo TFLite│
                        └──────────────┘
```

## Setup

### 1. Treinar modelo (se ainda não fez)

```bash
cd training
source venv/bin/activate
./setup.sh
python train_model.py
python export_model.py --version v1
```

### 2. Copiar modelo para Lambda

```bash
# Criar diretório
mkdir -p lambda/model/current

# Copiar modelo e labels
cp training/models/v1/model.tflite lambda/model/current/
cp training/data/labels.json lambda/model/current/
```

### 3. Instalar dependências da API

```bash
cd lambda
pip install -r requirements-local.txt
```

### 4. Descobrir IP do Mac

```bash
# macOS
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Exemplo de output: `inet 192.168.1.100`

### 5. Iniciar servidor Flask

```bash
cd lambda
python local_server.py
```

Output esperado:
```
 * Running on http://0.0.0.0:5000
 * Running on http://192.168.1.100:5000
```

### 6. Servir PWA

Em outro terminal:

```bash
cd pwa
python3 -m http.server 8000
```

## Acessar do Celular

### 1. Conectar na mesma rede WiFi

Celular e Mac devem estar na **mesma rede WiFi**.

### 2. Abrir PWA no celular

No navegador do celular, acesse:
```
http://192.168.1.100:8000
```

(Troque pelo IP do seu Mac)

### 3. Configurar API URL

No PWA:
1. Role até "⚙️ Configurações"
2. Troque API URL para: `http://192.168.1.100:5000`
3. Clique em "Salvar"

### 4. Testar

1. Clique em "📷 Abrir Câmera"
2. Aponte para uma carta Pokemon
3. Clique em "📸 Capturar"
4. Aguarde o resultado!

## Troubleshooting

### Celular não acessa PWA

**Problema**: "Site não encontrado"

**Solução**:
1. Verifique se estão na mesma WiFi
2. Ping do celular para o Mac:
   ```bash
   # No Mac, veja o IP
   ifconfig | grep "inet "
   
   # No celular (app de terminal ou navegador)
   ping 192.168.1.100
   ```
3. Desabilite firewall temporariamente:
   ```bash
   # macOS
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
   ```

### API não responde

**Problema**: "API error" no PWA

**Solução**:
1. Verifique se Flask está rodando:
   ```bash
   curl http://localhost:5000/health
   ```
2. Teste do celular:
   ```
   http://192.168.1.100:5000/health
   ```
3. Verifique logs do Flask no terminal

### Câmera não funciona

**Problema**: "Erro ao acessar câmera"

**Solução**:
- iOS Safari: Precisa de HTTPS (use ngrok ou certbot)
- Android Chrome: HTTP funciona em rede local
- Alternativa: Use botão "📁 Upload" para testar

### Modelo não carregado

**Problema**: "Model not loaded"

**Solução**:
```bash
# Verificar se modelo existe
ls -lh lambda/model/current/

# Deve ter:
# - model.tflite
# - labels.json

# Se não tiver, copie:
cp training/models/v1/model.tflite lambda/model/current/
cp training/data/labels.json lambda/model/current/
```

## HTTPS para iOS (opcional)

iOS Safari requer HTTPS para câmera. Use ngrok:

```bash
# Instalar ngrok
brew install ngrok

# Expor Flask
ngrok http 5000

# Expor PWA
ngrok http 8000
```

Use as URLs HTTPS fornecidas pelo ngrok.

## Performance

### Latência esperada
- **Rede local**: 200-500ms
- **Com ngrok**: 500-1000ms

### Otimizações
1. Comprimir imagem no PWA (já implementado - 80% quality)
2. Reduzir tamanho da imagem (max 800px)
3. Usar WiFi 5GHz se disponível

## Comandos úteis

```bash
# Ver IP do Mac
ifconfig | grep "inet " | grep -v 127.0.0.1

# Testar API localmente
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"image": "base64..."}'

# Ver logs Flask em tempo real
# (já aparece no terminal onde rodou local_server.py)

# Parar servidores
# Ctrl+C nos terminais
```

## Próximos passos

Após validar localmente:
1. Deploy Lambda na AWS
2. Deploy PWA no S3 + CloudFront
3. Usar URLs de produção
