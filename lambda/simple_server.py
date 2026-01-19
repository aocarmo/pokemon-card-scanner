from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import base64

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'ocr': 'enabled'})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        image_b64 = data.get('image')
        
        if not image_b64:
            return jsonify({'error': 'Missing image field'}), 400
        
        # Decode image
        image_bytes = base64.b64decode(image_b64)
        
        # Import here to avoid startup delay
        from inference import predict_card
        result = predict_card(image_bytes)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando API com OCR...")
    app.run(host='0.0.0.0', port=5001, debug=False)  # debug=False para evitar reload
