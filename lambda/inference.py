import json
import io
from pathlib import Path
import numpy as np
from PIL import Image
import tensorflow as tf

# Load model and labels at cold start
MODEL_PATH = Path(__file__).parent / "model" / "model.tflite"
LABELS_PATH = Path(__file__).parent / "model" / "labels.json"

interpreter = tf.lite.Interpreter(model_path=str(MODEL_PATH))
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

with open(LABELS_PATH) as f:
    labels = json.load(f)

def preprocess_image(image_bytes):
    """Preprocess image for model input"""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert('RGB')
    img = img.resize((224, 224))
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = (img_array / 127.5) - 1.0  # MobileNetV2 preprocessing
    return img_array

def predict_card(image_bytes):
    """Run inference on image"""
    # Preprocess
    input_data = preprocess_image(image_bytes)
    
    # Inference
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    
    # Get top prediction
    class_id = int(np.argmax(output_data[0]))
    confidence = float(output_data[0][class_id])
    
    # Get card info
    card_info = labels.get(str(class_id), {})
    
    return {
        'nome': card_info.get('nome', 'Unknown'),
        'colecao': card_info.get('colecao', 'Unknown'),
        'numero': card_info.get('numero', 'Unknown'),
        'confianca': round(confidence, 4)
    }
