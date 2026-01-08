#!/usr/bin/env python3
"""Prepare dataset for training - organize by collection"""

import argparse
import json
import shutil
from pathlib import Path
from collections import defaultdict

def prepare_data(collection_name: str = None):
    raw_dir = Path("data/raw")
    collections_dir = Path("data/collections")
    collections_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Scanning dataset...")
    
    # Find all card images
    image_files = list(raw_dir.rglob("*.png")) + list(raw_dir.rglob("*.jpg"))
    
    if not image_files:
        print("❌ No images found. Run download_dataset.py first.")
        return
    
    print(f"📊 Found {len(image_files)} images")
    
    # Group by collection
    cards_by_collection = defaultdict(list)
    labels = {}
    class_id = 0
    
    for img_path in image_files:
        # Parse filename: "Base_Set_1_Alakazam.png"
        parts = img_path.stem.split("_")
        
        if len(parts) < 3:
            continue
            
        # Extract collection and card info
        collection = " ".join(parts[:-2]).replace("_", " ")
        number = parts[-2]
        name = parts[-1]
        
        # Filter by collection if specified
        if collection_name and collection.lower() != collection_name.lower():
            continue
        
        card_key = f"{collection}_{number}_{name}"
        cards_by_collection[collection].append({
            "path": img_path,
            "name": name,
            "number": number,
            "key": card_key
        })
    
    if not cards_by_collection:
        print(f"❌ No cards found for collection: {collection_name}")
        return
    
    # Organize files
    print(f"\n📁 Organizing {len(cards_by_collection)} collection(s)...")
    
    for collection, cards in cards_by_collection.items():
        collection_slug = collection.lower().replace(" ", "_")
        collection_path = collections_dir / collection_slug
        
        print(f"\n  📦 {collection}: {len(cards)} cards")
        
        for card in cards:
            # Create directory per card
            card_dir = collection_path / card["key"]
            card_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy image
            dest = card_dir / card["path"].name
            if not dest.exists():
                shutil.copy2(card["path"], dest)
            
            # Add to labels
            labels[class_id] = {
                "nome": card["name"],
                "colecao": collection,
                "numero": card["number"]
            }
            class_id += 1
    
    # Save labels
    labels_path = Path("data/labels.json")
    with open(labels_path, "w") as f:
        json.dump(labels, f, indent=2)
    
    print(f"\n✅ Dataset prepared!")
    print(f"   📊 Total classes: {class_id}")
    print(f"   📁 Collections: {collections_dir.absolute()}")
    print(f"   🏷️  Labels: {labels_path.absolute()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection", help="Filter by collection name (e.g., 'Base Set')")
    args = parser.parse_args()
    
    prepare_data(args.collection)
