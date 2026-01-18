import base64
import json
from PIL import Image
import numpy as np
import cv2
import io

try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ pytesseract não disponível")

def analyze_card_corner(image_b64):
    """Analisa o canto inferior esquerdo de uma carta"""
    
    # Decode image
    image_bytes = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(img)
    
    print(f"📏 Imagem: {img_array.shape[1]}x{img_array.shape[0]} pixels")
    
    # Extrair canto inferior esquerdo
    height, width = img_array.shape[:2]
    
    # Diferentes regiões para testar
    regions = {
        'pequena': (0, int(height * 0.9), int(width * 0.2), height),
        'media': (0, int(height * 0.85), int(width * 0.3), height),
        'grande': (0, int(height * 0.8), int(width * 0.4), height)
    }
    
    results = {}
    
    for region_name, (x1, y1, x2, y2) in regions.items():
        print(f"\n🔍 Analisando região {region_name}: ({x1},{y1}) até ({x2},{y2})")
        
        # Extrair região
        region = img_array[y1:y2, x1:x2]
        
        # Salvar região para debug
        region_img = Image.fromarray(region)
        region_path = f"/tmp/card_region_{region_name}.png"
        region_img.save(region_path)
        print(f"💾 Região salva em: {region_path}")
        
        # OCR se disponível
        if OCR_AVAILABLE:
            try:
                # Preprocessar
                if len(region.shape) == 3:
                    gray = cv2.cvtColor(region, cv2.COLOR_RGB2GRAY)
                else:
                    gray = region
                
                # Diferentes preprocessamentos
                preprocessed = {
                    'original': gray,
                    'contrast': cv2.convertScaleAbs(gray, alpha=2.0, beta=0),
                    'threshold': cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                }
                
                for prep_name, prep_img in preprocessed.items():
                    # Redimensionar para melhor OCR
                    scale_factor = 3
                    h, w = prep_img.shape
                    resized = cv2.resize(prep_img, (w * scale_factor, h * scale_factor), interpolation=cv2.INTER_CUBIC)
                    
                    # OCR com diferentes configurações
                    configs = [
                        '--psm 6',  # Bloco de texto uniforme
                        '--psm 7',  # Linha de texto única
                        '--psm 8',  # Palavra única
                        '--psm 13'  # Linha crua - sem hacks específicos do Tesseract
                    ]
                    
                    for config in configs:
                        try:
                            text = pytesseract.image_to_string(resized, config=config).strip()
                            if text:
                                print(f"  📝 {prep_name} + {config}: '{text}'")
                        except:
                            pass
            except Exception as e:
                print(f"  ❌ Erro OCR: {e}")
        
        results[region_name] = {
            'coordinates': (x1, y1, x2, y2),
            'size': f"{x2-x1}x{y2-y1}",
            'saved_path': region_path
        }
    
    return results

# Endpoint para análise
def analyze_endpoint():
    """Endpoint para receber imagem e analisar"""
    return """
    POST /analyze com:
    {
        "image": "base64_da_imagem"
    }
    """

if __name__ == "__main__":
    print("🔍 Analisador de canto inferior esquerdo")
    print("Envie uma imagem base64 para análise")
