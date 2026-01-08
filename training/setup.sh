#!/bin/bash
# Setup script - download and prepare dataset

set -e

export KAGGLE_API_TOKEN=KGAT_7067eaac8267216345a44fbd1c17e433

echo "🚀 Starting dataset setup..."

# Download dataset
echo "📥 Downloading dataset..."
DATASET_PATH=$(python download_dataset.py | grep "Path to dataset files:" | cut -d: -f2- | xargs)

if [ -z "$DATASET_PATH" ]; then
    echo "❌ Failed to get dataset path"
    exit 1
fi

echo "✅ Dataset downloaded to: $DATASET_PATH"

# Prepare prismatic-evolutions
echo ""
echo "📦 Preparing prismatic-evolutions collection..."
python prepare_data.py --source "$DATASET_PATH" --collection prismatic-evolutions

echo ""
echo "✅ Setup complete! Ready to train."
echo "   Run: python train_model.py"
