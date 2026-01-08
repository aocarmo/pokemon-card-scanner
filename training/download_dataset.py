#!/usr/bin/env python3
"""Download Pokemon TCG dataset from Kaggle"""

import kagglehub
from pathlib import Path

def download_dataset():
    print("📥 Downloading Pokemon TCG dataset from Kaggle...")
    
    try:
        # Download using kagglehub
        path = kagglehub.dataset_download("ellimaaac/pokemon-tcg-all-image-cards")
        
        print(f"✅ Dataset downloaded successfully!")
        print(f"📁 Path to dataset files: {path}")
        
        # List available collections
        dataset_path = Path(path)
        collections = [d.name for d in dataset_path.iterdir() if d.is_dir()]
        
        print(f"\n📦 Available collections ({len(collections)}):")
        for col in sorted(collections):
            print(f"   - {col}")
        
        return path
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Make sure you have:")
        print("   1. kagglehub installed: pip install kagglehub")
        print("   2. Kaggle credentials configured")

if __name__ == "__main__":
    download_dataset()
