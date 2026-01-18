#!/usr/bin/env python3
"""Prepare dataset for training - organize by collection"""

import argparse
import json
import shutil
from pathlib import Path

def prepare_data(source_path: str, collection_name: str = "prismatic-evolutions"):
    """
    Prepare dataset from kagglehub download
    
    Args:
        source_path: Path from kagglehub.dataset_download()
        collection_name: Folder name to use (default: prismatic-evolutions)
    """
    source_dir = Path(source_path) / collection_name
    
    if not source_dir.exists():
        print(f"❌ Collection not found: {source_dir}")
        print(f"💡 Available collections in {source_path}:")
        for d in Path(source_path).iterdir():
            if d.is_dir():
                print(f"   - {d.name}")
        return
    
    collections_dir = Path("data/collections")
    collections_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Processing collection: {collection_name}")
    
    # Find all card images
    image_files = list(source_dir.glob("*.png")) + list(source_dir.glob("*.jpg"))
    
    if not image_files:
        print(f"❌ No images found in {source_dir}")
        return
    
    print(f"📊 Found {len(image_files)} images")
    
    # Organize by card
    labels = {}
    class_id = 0
    collection_path = collections_dir / collection_name.replace("-", "_")
    
    for img_path in image_files:
        # Parse filename: "001_Oddish.png" or similar
        stem = img_path.stem
        parts = stem.split("_", 1)
        
        if len(parts) == 2:
            number = parts[0]
            name = parts[1]
        else:
            number = str(class_id)
            name = stem
        
        # Create card directory
        card_key = f"{number}_{name}"
        card_dir = collection_path / card_key
        card_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy image
        dest = card_dir / img_path.name
        if not dest.exists():
            shutil.copy2(img_path, dest)
        
        # Add to labels
        labels[class_id] = {
            "nome": name,
            "colecao": collection_name.replace("-", " ").title(),
            "numero": number
        }
        class_id += 1
    
    # Save labels
    labels_path = Path("data/labels.json")
    with open(labels_path, "w") as f:
        json.dump(labels, f, indent=2)
    
    print(f"\n✅ Dataset prepared!")
    print(f"   📊 Total cards: {class_id}")
    print(f"   📁 Location: {collection_path.absolute()}")
    print(f"   🏷️  Labels: {labels_path.absolute()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path from kagglehub download")
    parser.add_argument("--collection", default="prismatic-evolutions", help="Collection folder name")
    args = parser.parse_args()
    
    prepare_data(args.source, args.collection)
