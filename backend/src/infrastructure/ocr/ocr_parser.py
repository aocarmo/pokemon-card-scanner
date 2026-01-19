import cv2
import numpy as np
import pytesseract
from PIL import Image
import io
import re
from typing import Optional
from ...domain.models import CardMetadata

class OCRParser:
    """Extrai metadados da carta via OCR"""
    
    COLLECTION_CODES = {
        "PRE": "Prismatic Evolutions",
        "SVI": "Scarlet & Violet",
        "PAL": "Paldea Evolved",
    }
    
    def extract_metadata(self, image_bytes: bytes) -> Optional[CardMetadata]:
        """Extrai código, idioma e número do canto inferior esquerdo"""
        
        # Extract bottom-left corner
        corner_img = self._extract_bottom_left_corner(image_bytes)
        
        if corner_img is None:
            print("❌ Não conseguiu extrair canto da imagem")
            return None
        
        # Save debug image
        cv2.imwrite('/tmp/ocr_region.jpg', corner_img)
        print("💾 Região OCR salva em /tmp/ocr_region.jpg")
        
        # OCR
        text = pytesseract.image_to_string(corner_img, config='--psm 7')
        text = text.strip().upper()
        
        print(f"📝 OCR leu: '{text}'")
        
        # Parse: "PRE PT 122/131"
        metadata = self._parse_text(text)
        
        if metadata:
            print(f"✅ Parsed: {metadata.colecao_code} {metadata.idioma} {metadata.numero}")
        else:
            print(f"❌ Não conseguiu fazer parse do texto: '{text}'")
        
        return metadata
    
    def _extract_bottom_left_corner(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Extrai região do canto inferior esquerdo (10% altura, 30% largura)"""
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
        
        h, w = img.shape[:2]
        
        # Bottom 10%, left 30%
        y_start = int(h * 0.9)
        x_end = int(w * 0.3)
        
        corner = img[y_start:h, 0:x_end]
        
        # Preprocessing for better OCR
        gray = cv2.cvtColor(corner, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        
        return gray
    
    def _parse_text(self, text: str) -> Optional[CardMetadata]:
        """Parse: PRE PT 122/131"""
        
        # Pattern: XXX XX NNN/NNN
        pattern = r'([A-Z]{3})\s+([A-Z]{2})\s+(\d+)/(\d+)'
        match = re.search(pattern, text)
        
        if not match:
            return None
        
        colecao_code = match.group(1)
        idioma = match.group(2)
        numero_carta = match.group(3)
        total_colecao = match.group(4)
        numero = f"{numero_carta}/{total_colecao}"
        
        # Validate
        if idioma not in ['PT', 'EN', 'ES', 'JP']:
            return None
        
        return CardMetadata(
            colecao_code=colecao_code,
            idioma=idioma,
            numero=numero,
            numero_carta=numero_carta,
            total_colecao=total_colecao
        )
    
    def get_collection_name(self, code: str) -> str:
        """Retorna nome da coleção pelo código"""
        return self.COLLECTION_CODES.get(code, "Unknown")
