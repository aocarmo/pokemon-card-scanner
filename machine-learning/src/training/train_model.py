#!/usr/bin/env python3
"""Train Pokemon card classifier"""

import json
import yaml
from pathlib import Path
from datetime import datetime

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2

def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)

def create_dataset(data_dir, config):
    img_size = config["training"]["image_size"]
    batch_size = config["training"]["batch_size"]
    
    # Load images from directory structure
    train_ds = keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=config["training"]["validation_split"],
        subset="training",
        seed=123,
        image_size=(img_size, img_size),
        batch_size=batch_size
    )
    
    val_ds = keras.utils.image_dataset_from_directory(
        data_dir,
        validation_split=config["training"]["validation_split"],
        subset="validation",
        seed=123,
        image_size=(img_size, img_size),
        batch_size=batch_size
    )
    
    # Data augmentation
    aug = config["training"]["augmentation"]
    data_augmentation = keras.Sequential([
        layers.RandomRotation(aug["rotation_range"] / 360),
        layers.RandomTranslation(aug["height_shift_range"], aug["width_shift_range"]),
        layers.RandomZoom(aug["zoom_range"]),
    ])
    
    # Optimize performance
    train_ds = train_ds.map(lambda x, y: (data_augmentation(x, training=True), y))
    train_ds = train_ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    val_ds = val_ds.prefetch(buffer_size=tf.data.AUTOTUNE)
    
    return train_ds, val_ds

def create_model(num_classes, config):
    img_size = config["training"]["image_size"]
    
    # Base model
    base_model = MobileNetV2(
        input_shape=(img_size, img_size, 3),
        include_top=False,
        weights="imagenet"
    )
    
    # Freeze base model
    base_model.trainable = False
    
    # Add classification head
    inputs = keras.Input(shape=(img_size, img_size, 3))
    x = keras.applications.mobilenet_v2.preprocess_input(inputs)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    
    model = keras.Model(inputs, outputs)
    
    return model

def train_model():
    print("🚀 Starting training...")
    
    config = load_config()
    data_dir = Path("data/collections")
    
    if not data_dir.exists():
        print("❌ No data found. Run prepare_data.py first.")
        return
    
    # Count classes (subdirectories in collections)
    num_classes = len([d for d in data_dir.rglob("*") if d.is_dir() and d.parent.name != "collections"])
    print(f"📊 Training with {num_classes} classes")
    
    # Create datasets
    print("📁 Loading dataset...")
    train_ds, val_ds = create_dataset(data_dir, config)
    
    # Create model
    print("🏗️  Building model...")
    model = create_model(num_classes, config)
    
    model.compile(
        optimizer=keras.optimizers.Adam(config["training"]["learning_rate"]),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    
    print(f"\n📋 Model summary:")
    model.summary()
    
    # Callbacks
    callbacks = [
        keras.callbacks.ModelCheckpoint(
            "models/best_model.keras",
            save_best_only=True,
            monitor="val_accuracy"
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=5,
            restore_best_weights=True
        )
    ]
    
    # Train
    print(f"\n🎯 Training for {config['training']['epochs']} epochs...")
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config["training"]["epochs"],
        callbacks=callbacks
    )
    
    # Save final model
    model_dir = Path("models/v1")
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model.save(model_dir / "model.keras")
    
    # Save metadata
    metadata = {
        "version": "v1",
        "created_at": datetime.now().isoformat(),
        "collections": [c["name"] for c in config["active_collections"] if c["enabled"]],
        "num_classes": num_classes,
        "accuracy": float(max(history.history["val_accuracy"])),
        "config": config["training"]
    }
    
    with open(model_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ Training complete!")
    print(f"   📊 Best accuracy: {metadata['accuracy']:.2%}")
    print(f"   💾 Model saved: {model_dir.absolute()}")

if __name__ == "__main__":
    train_model()
