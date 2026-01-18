from pydantic import BaseModel
from typing import Optional, List

class CardMetadata(BaseModel):
    """Metadados extraídos da carta"""
    colecao_code: str
    idioma: str
    numero: str
    numero_carta: str
    total_colecao: str

class CardIdentification(BaseModel):
    """Resultado da identificação da carta"""
    card_id: str
    nome: str
    numero: str
    numero_carta: str
    total_colecao: str
    colecao: str
    colecao_code: str
    idioma: str
    confianca_ocr: str
    metodo: str = "OCR"
