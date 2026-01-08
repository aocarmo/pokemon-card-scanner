#!/usr/bin/env python3
"""Download Pokemon TCG dataset from Kaggle"""

import os
import subprocess
from pathlib import Path

def download_dataset():
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("📥 Downloading Pokemon TCG dataset from Kaggle...")
    
    try:
        subprocess.run([
            "kaggle", "datasets", "download", 
            "-d", "ellimaaac/pokemon-tcg-all-image-cards",
            "-p", str(data_dir)
        ], check=True)
        
        print("📦 Extracting dataset...")
        subprocess.run([
            "unzip", "-q", 
            str(data_dir / "pokemon-tcg-all-image-cards.zip"),
            "-d", str(data_dir)
        ], check=True)
        
        print("✅ Dataset downloaded successfully!")
        print(f"📁 Location: {data_dir.absolute()}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("   1. Kaggle CLI installed: pip install kaggle")
        print("   2. Kaggle credentials in ~/.kaggle/kaggle.json")
        print("   3. Accepted dataset terms on Kaggle website")

if __name__ == "__main__":
    download_dataset()
