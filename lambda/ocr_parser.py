import re
import cv2
import numpy as np
from PIL import Image
import io

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️  pytesseract não instalado. OCR desabilitado.")

def extract_card_info_region(image_bytes):
    """Extrai região do canto inferior esquerdo onde ficam as informações da carta"""
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img)
    
    # Região do canto inferior esquerdo (aproximadamente 20% da largura, 15% da altura)
    height, width = img_array.shape[:2]
    x1, y1 = 0, int(height * 0.85)
    x2, y2 = int(width * 0.3), height
    
    info_region = img_array[y1:y2, x1:x2]
    return info_region

def preprocess_for_ocr(image_region):
    """Preprocessa região para melhor OCR"""
    # Converter para grayscale
    if len(image_region.shape) == 3:
        gray = cv2.cvtColor(image_region, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_region
    
    # Aumentar contraste
    gray = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)
    
    # Threshold adaptivo
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Redimensionar para melhor OCR
    scale_factor = 3
    height, width = binary.shape
    resized = cv2.resize(binary, (width * scale_factor, height * scale_factor), 
                        interpolation=cv2.INTER_CUBIC)
    
    return resized

def extract_text_from_region(image_region):
    """Extrai texto da região usando OCR"""
    if not OCR_AVAILABLE:
        return ""
    
    try:
        processed = preprocess_for_ocr(image_region)
        
        # Configuração do Tesseract para texto pequeno
        config = '--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-/'
        
        text = pytesseract.image_to_string(processed, config=config)
        return text.strip()
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return ""

def parse_card_number(text):
    """Extrai número da carta do texto OCR"""
    patterns = [
        r'(\d{1,3})/\d{1,3}',  # Formato: 118/180
        r'sv\d+-(\d{1,3})',    # Formato: sv8-5 (extrai o 5)
        r'(\d{1,3})\s*$',      # Número no final
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def parse_set_code(text):
    """Extrai código da coleção do texto OCR"""
    patterns = [
        r'(sv\d+)',           # Formato: sv8, sv4.5
        r'(PAL\d+)',          # Formato: PAL001
        r'(SV\d+)',           # Formato maiúsculo
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    
    return None

def extract_card_metadata(image_bytes):
    """Extrai metadados da carta usando OCR"""
    try:
        # Extrair região de informações
        info_region = extract_card_info_region(image_bytes)
        
        # Extrair texto
        text = extract_text_from_region(info_region)
        
        # Parse das informações
        card_number = parse_card_number(text)
        set_code = parse_set_code(text)
        
        return {
            'raw_text': text,
            'card_number': card_number,
            'set_code': set_code,
            'ocr_success': bool(text)
        }
        
    except Exception as e:
        return {
            'raw_text': '',
            'card_number': None,
            'set_code': None,
            'ocr_success': False,
            'error': str(e)
        }
