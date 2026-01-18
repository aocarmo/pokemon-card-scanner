from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import base64
from pathlib import Path
from inference import predict_card

app = Flask(__name__)
CORS(app)  # Permite acesso do celular

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        image_b64 = data.get('image')
        
        if not image_b64:
            return jsonify({'error': 'Missing image field'}), 400
        
        # Decode and predict
        image_bytes = base64.b64decode(image_b64)
        result = predict_card(image_bytes)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Escuta em todas as interfaces (0.0.0.0) para aceitar conexões do celular
    app.run(host='0.0.0.0', port=5001, debug=True)
