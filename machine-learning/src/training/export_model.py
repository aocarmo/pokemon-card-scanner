#!/usr/bin/env python3
"""Export trained model to TensorFlow Lite"""

import argparse
import json
import shutil
from pathlib import Path

import tensorflow as tf

def export_model(version: str):
    model_dir = Path(f"models/{version}")
    
    if not model_dir.exists():
        print(f"❌ Model not found: {model_dir}")
        return
    
    print(f"📦 Exporting model {version} to TFLite...")
    
    # Load model
    model = tf.keras.models.load_model(model_dir / "model.keras")
    
    # Save as SavedModel first
    saved_model_dir = model_dir / "saved_model"
    model.export(saved_model_dir)
    
    # Convert from SavedModel
    converter = tf.lite.TFLiteConverter.from_saved_model(str(saved_model_dir))
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    tflite_model = converter.convert()
    
    # Save
    tflite_path = model_dir / "model.tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    
    # Copy labels
    labels_src = Path("data/labels.json")
    if labels_src.exists():
        shutil.copy2(labels_src, model_dir / "labels.json")
    
    size_mb = tflite_path.stat().st_size / (1024 * 1024)
    
    print(f"✅ Export complete!")
    print(f"   📦 TFLite model: {tflite_path.absolute()}")
    print(f"   💾 Size: {size_mb:.2f} MB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v1", help="Model version")
    args = parser.parse_args()
    
    export_model(args.version)
