#!/usr/bin/env python3
import http.server
import socketserver
import json
import base64
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class APIHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = json.dumps({'status': 'ok', 'analyze_endpoint': '/analyze'})
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/predict':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                image_b64 = data.get('image')
                if not image_b64:
                    self.send_error(400, 'Missing image field')
                    return
                
                # Decode image
                image_bytes = base64.b64decode(image_b64)
                
                # Análise de canto para debug
                if self.path == '/analyze':
                    from analyze_corner import analyze_card_corner
                    result = analyze_card_corner(image_b64)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    response = json.dumps(result)
                    self.wfile.write(response.encode())
                    return
                
                # Import and predict with OCR
                from inference_ocr import predict_card_with_ocr
                result = predict_card_with_ocr(image_bytes)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = json.dumps(result)
                self.wfile.write(response.encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = json.dumps({'error': str(e)})
                self.wfile.write(error_response.encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    PORT = 5003
    with socketserver.TCPServer(("0.0.0.0", PORT), APIHandler) as httpd:
        print(f"🚀 API HTTP básica rodando na porta {PORT}")
        httpd.serve_forever()
