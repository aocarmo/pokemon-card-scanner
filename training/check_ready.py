#!/usr/bin/env python3
"""Verificar se está tudo pronto para treinar"""

import sys
from pathlib import Path

def check_environment():
    print("🔍 Verificando ambiente...\n")
    
    checks = []
    
    # 1. Python packages
    try:
        import tensorflow as tf
        import keras
        import kagglehub
        import yaml
        print(f"✅ TensorFlow {tf.__version__}")
        print(f"✅ Keras {keras.__version__}")
        print(f"✅ kagglehub {kagglehub.__version__}")
        
        # Check GPU
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            print(f"✅ GPU disponível: {gpus[0].name}")
        else:
            print("⚠️  Sem GPU (vai usar CPU)")
        
        checks.append(True)
    except ImportError as e:
        print(f"❌ Faltam pacotes: {e}")
        checks.append(False)
    
    # 2. Config file
    print()
    config_path = Path("config.yaml")
    if config_path.exists():
        print(f"✅ config.yaml encontrado")
        checks.append(True)
    else:
        print(f"❌ config.yaml não encontrado")
        checks.append(False)
    
    # 3. Scripts
    print()
    scripts = ["download_dataset.py", "prepare_data.py", "train_model.py", "export_model.py"]
    for script in scripts:
        if Path(script).exists():
            print(f"✅ {script}")
        else:
            print(f"❌ {script} não encontrado")
            checks.append(False)
    
    # 4. Data directory
    print()
    data_dir = Path("data/collections")
    if data_dir.exists():
        collections = list(data_dir.iterdir())
        if collections:
            print(f"✅ Dataset preparado: {len(collections)} coleção(ões)")
            for col in collections:
                cards = list(col.iterdir())
                print(f"   - {col.name}: {len(cards)} cartas")
            checks.append(True)
        else:
            print(f"⚠️  data/collections existe mas está vazio")
            print(f"   Execute: ./setup.sh")
            checks.append(False)
    else:
        print(f"⚠️  data/collections não existe")
        print(f"   Execute: ./setup.sh")
        checks.append(False)
    
    # 5. Models directory
    print()
    models_dir = Path("models")
    if models_dir.exists():
        print(f"✅ Diretório models/ existe")
    else:
        print(f"ℹ️  Diretório models/ será criado no treinamento")
    
    # Summary
    print("\n" + "="*50)
    if all(checks):
        print("✅ TUDO PRONTO PARA TREINAR!")
        print("\nPróximos passos:")
        if not data_dir.exists() or not list(data_dir.iterdir()):
            print("1. Execute: ./setup.sh")
            print("2. Execute: python train_model.py")
        else:
            print("Execute: python train_model.py")
        return 0
    else:
        print("❌ FALTAM ALGUMAS COISAS")
        print("\nResolva os problemas acima antes de treinar")
        return 1

if __name__ == "__main__":
    sys.exit(check_environment())
