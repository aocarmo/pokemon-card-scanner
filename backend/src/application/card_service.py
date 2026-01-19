from typing import Optional
from ..domain.models import CardIdentification
from ..infrastructure.cv.card_detector import CardDetector
from ..infrastructure.ocr.ocr_parser import OCRParser

class CardService:
    """Serviço de identificação de cartas"""
    
    def __init__(self):
        self.detector = CardDetector()
        self.ocr = OCRParser()
    
    def identify_card(self, image_bytes: bytes) -> Optional[CardIdentification]:
        """Identifica carta a partir da imagem"""
        
        print("🔍 Iniciando identificação...")
        
        # 1. Detect and crop card
        cropped_bytes = self.detector.detect_and_crop(image_bytes)
        print(f"✂️ Carta cortada: {len(cropped_bytes)} bytes")
        
        # 2. Extract metadata via OCR
        metadata = self.ocr.extract_metadata(cropped_bytes)
        
        if metadata is None:
            print("❌ OCR falhou - não conseguiu ler metadados")
            return None
        
        print(f"📝 OCR leu: {metadata.colecao_code} {metadata.idioma} {metadata.numero}")
        
        # 3. Get collection name
        colecao = self.ocr.get_collection_name(metadata.colecao_code)
        
        # 4. Build card ID
        card_id = f"{metadata.colecao_code.lower()}_{metadata.idioma.lower()}_{metadata.numero_carta}"
        
        # 5. Get card name (TODO: from dataset or ML)
        nome = self._get_card_name(metadata.colecao_code, metadata.numero_carta)
        
        return CardIdentification(
            card_id=card_id,
            nome=nome,
            numero=metadata.numero,
            numero_carta=metadata.numero_carta,
            total_colecao=metadata.total_colecao,
            colecao=colecao,
            colecao_code=metadata.colecao_code,
            idioma=metadata.idioma,
            confianca_ocr="high",
            metodo="OCR"
        )
    
    def _get_card_name(self, colecao_code: str, numero_carta: str) -> str:
        """Busca nome da carta no dataset (TODO: implementar)"""
        # Por enquanto retorna placeholder
        return f"Card #{numero_carta}"
