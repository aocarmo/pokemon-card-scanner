from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ..application.card_service import CardService

app = FastAPI(title="Pokemon Card Scanner API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service
card_service = CardService()

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}

@app.post("/api/cards/identify")
async def identify_card(file: UploadFile = File(...)):
    """Identifica carta a partir de imagem"""
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    # Read image
    image_bytes = await file.read()
    
    print(f"📸 Recebeu imagem: {len(image_bytes)} bytes")
    
    # Identify
    result = card_service.identify_card(image_bytes)
    
    if result is None:
        print("❌ OCR não conseguiu ler a carta")
        raise HTTPException(400, "Could not read card metadata. Make sure the bottom-left corner is visible and clear.")
    
    print(f"✅ Carta identificada: {result.nome} - {result.numero}")
    
    return result

@app.post("/api/cards/detect")
async def detect_card(file: UploadFile = File(...)):
    """Detecta posição da carta na imagem"""
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    image_bytes = await file.read()
    
    # Detect contour
    contour = card_service.detector.find_card_contour_raw(image_bytes)
    
    if contour is None:
        return {"detected": False}
    
    # Convert contour to JSON-friendly format
    points = [{"x": int(pt[0]), "y": int(pt[1])} for pt in contour.reshape(-1, 2)]
    
    return {
        "detected": True,
        "contour": points
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pokemon Card Scanner API",
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/api/cards/confirm")
async def confirm_card(data: dict):
    """Confirma identificação da carta"""
    print(f"✅ Carta confirmada: {data.get('name')} - {data.get('number')}")
    return {"status": "confirmed"}
