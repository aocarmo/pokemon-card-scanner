import json
import io
from pathlib import Path
import numpy as np
from PIL import Image
import tensorflow as tf
import re
import cv2

# Load model and labels at startup
MODEL_PATH = Path(__file__).parent / "model" / "current" / "model.tflite"
LABELS_PATH = Path(__file__).parent / "model" / "current" / "labels.json"

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Check if model exists
if not MODEL_PATH.exists():
    interpreter = None
    labels = {}
else:
    interpreter = tf.lite.Interpreter(model_path=str(MODEL_PATH))
    interpreter.allocate_tensors()
    
    with open(LABELS_PATH) as f:
        labels = json.load(f)

input_details = interpreter.get_input_details() if interpreter else None
output_details = interpreter.get_output_details() if interpreter else None

def extract_card_number_ocr(image_bytes):
    """Extrai número da carta usando OCR"""
    if not OCR_AVAILABLE:
        return None
    
    try:
        # Abrir imagem
        img = Image.open(io.BytesIO(image_bytes))
        img_array = np.array(img)
        
        # Região do canto inferior esquerdo (onde fica o número)
        height, width = img_array.shape[:2]
        x1, y1 = 0, int(height * 0.85)
        x2, y2 = int(width * 0.3), height
        
        info_region = img_array[y1:y2, x1:x2]
        
        # Preprocessar para OCR
        if len(info_region.shape) == 3:
            gray = cv2.cvtColor(info_region, cv2.COLOR_RGB2GRAY)
        else:
            gray = info_region
        
        # Aumentar contraste
        gray = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)
        
        # Threshold
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        # Redimensionar
        scale_factor = 3
        height, width = binary.shape
        resized = cv2.resize(binary, (width * scale_factor, height * scale_factor), 
                            interpolation=cv2.INTER_CUBIC)
        
        # OCR
        config = '--psm 6 -c tessedit_char_whitelist=0123456789/'
        text = pytesseract.image_to_string(resized, config=config)
        
        # Extrair número (formato: 102/180)
        match = re.search(r'(\d{1,3})/\d{1,3}', text)
        if match:
            return int(match.group(1))
        
        # Tentar só números
        numbers = re.findall(r'\d{1,3}', text)
        if numbers:
            return int(numbers[0])
            
        return None
        
    except Exception as e:
        print(f"Erro OCR: {e}")
        return None

def find_card_by_number(card_number):
    """Busca carta pelo número extraído via OCR"""
    if not card_number:
        return None
    
    # Buscar carta com número correspondente
    for class_id, card_info in labels.items():
        card_name = card_info.get('nome', '')
        
        # Extrair número do nome da carta (formato: en_102_std)
        if '_' in card_name:
            parts = card_name.split('_')
            if len(parts) >= 2:
                try:
                    model_number = int(parts[1])
                    if model_number == card_number:
                        return {
                            'class_id': int(class_id),
                            'card_info': card_info,
                            'confidence': 0.95  # Alta confiança para match OCR
                        }
                except ValueError:
                    continue
    
    return None

def preprocess_image(image_bytes):
    """Preprocess image for model input"""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert('RGB')
    img = img.resize((224, 224))
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = (img_array / 127.5) - 1.0  # MobileNetV2 preprocessing
    return img_array

def predict_card_with_ocr(image_bytes):
    """Predição híbrida: OCR + Visão"""
    if not interpreter:
        return {
            'error': 'Model not loaded',
            'nome': 'Unknown',
            'colecao': 'Unknown',
            'numero': 'Unknown',
            'confianca': 0.0
        }
    
    # 1. Tentar OCR primeiro
    ocr_number = extract_card_number_ocr(image_bytes)
    ocr_match = find_card_by_number(ocr_number) if ocr_number else None
    
    # 2. Predição visual
    input_data = preprocess_image(image_bytes)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    
    # Top 3 predições visuais
    top_indices = np.argsort(output_data[0])[-3:][::-1]
    visual_predictions = []
    
    for i, idx in enumerate(top_indices):
        card_info = labels.get(str(idx), {})
        confidence = float(output_data[0][idx])
        visual_predictions.append({
            'rank': i + 1,
            'nome': card_info.get('nome', 'Unknown'),
            'confianca': round(confidence, 4)
        })
    
    # 3. Decidir resultado final
    if ocr_match and ocr_match['confidence'] > 0.8:
        # OCR encontrou match - usar ele
        card_info = ocr_match['card_info']
        final_confidence = ocr_match['confidence']
        method = f'OCR (número {ocr_number})'
    else:
        # Usar predição visual
        class_id = int(top_indices[0])
        final_confidence = float(output_data[0][class_id])
        card_info = labels.get(str(class_id), {})
        method = 'Visual'
    
    return {
        'nome': card_info.get('nome', 'Unknown'),
        'colecao': card_info.get('colecao', 'Unknown'),
        'numero': card_info.get('numero', 'Unknown'),
        'confianca': round(final_confidence, 4),
        'method': method,
        'ocr_number': ocr_number,
        'ocr_available': OCR_AVAILABLE,
        'visual_predictions': visual_predictions
    }
