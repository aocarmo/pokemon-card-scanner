import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [detected, setDetected] = useState(false);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const scanIntervalRef = useRef(null);

  const startScanner = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment',
          width: { ideal: 1080 },
          height: { ideal: 1920 }
        } 
      });
      
      streamRef.current = stream;
      setScanning(true);
      setError(null);
      setResult(null);
      
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          startContinuousDetection();
        }
      }, 100);
      
    } catch (err) {
      setError('Erro ao acessar câmera');
    }
  };

  const startContinuousDetection = () => {
    scanIntervalRef.current = setInterval(async () => {
      if (!videoRef.current || loading) return;
      
      const canvas = canvasRef.current;
      const video = videoRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      
      canvas.toBlob(async (blob) => {
        if (!blob || loading) return;
        
        try {
          // Detect card position
          const formData = new FormData();
          formData.append('file', blob);
          
          const response = await axios.post(`${API_URL}/api/cards/detect`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 1000
          });
          
          if (response.data.detected && response.data.contour) {
            setDetected(true);
            drawCardFrame(response.data.contour, video);
          } else {
            setDetected(false);
            clearOverlay();
          }
          
        } catch (err) {
          setDetected(false);
          clearOverlay();
        }
      }, 'image/jpeg', 0.7);
      
    }, 300); // Check every 300ms for smooth tracking
  };

  const drawCardFrame = (contour, video) => {
    const overlay = document.getElementById('overlayCanvas');
    if (!overlay || !video) return;
    
    const ctx = overlay.getContext('2d');
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 4;
    ctx.shadowBlur = 15;
    ctx.shadowColor = '#00ff00';
    
    ctx.beginPath();
    ctx.moveTo(contour[0].x, contour[0].y);
    for (let i = 1; i < contour.length; i++) {
      ctx.lineTo(contour[i].x, contour[i].y);
    }
    ctx.closePath();
    ctx.stroke();
  };

  const clearOverlay = () => {
    const overlay = document.getElementById('overlayCanvas');
    if (overlay) {
      const ctx = overlay.getContext('2d');
      ctx.clearRect(0, 0, overlay.width, overlay.height);
    }
  };

  const identifyCard = async (blob) => {
    if (loading) return;
    
    setLoading(true);
    stopScanner();
    
    const formData = new FormData();
    formData.append('file', blob);
    
    try {
      const response = await axios.post(`${API_URL}/api/cards/identify`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setResult(response.data);
    } catch (err) {
      setError('Erro ao identificar carta');
    } finally {
      setLoading(false);
    }
  };

  const stopScanner = () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    setScanning(false);
    setDetected(false);
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setLoading(true);
    setError(null);
    
    const formData = new FormData();
    formData.append('file', file);
    
    axios.post(`${API_URL}/api/cards/identify`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    .then(response => {
      setResult(response.data);
    })
    .catch(err => {
      setError(err.response?.data?.detail || 'Erro ao processar imagem');
    })
    .finally(() => {
      setLoading(false);
    });
  };

  const reset = () => {
    setResult(null);
    setError(null);
  };

  useEffect(() => {
    return () => {
      stopScanner();
    };
  }, []);

  return (
    <div className="App">
      <header>
        <h1>🎴 Pokemon Card Scanner</h1>
        <p>Identifique suas cartas instantaneamente</p>
      </header>

      <main>
        {!scanning && !result && (
          <div className="controls">
            <button onClick={startScanner} className="scanner-btn">
              📷 Iniciar Scanner
            </button>
            
            <div className="divider">ou</div>
            
            <input
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              id="fileInput"
              style={{ display: 'none' }}
            />
            <label htmlFor="fileInput" className="upload-btn">
              📸 Enviar Foto
            </label>
          </div>
        )}

        {scanning && (
          <div className="scanner-container">
            <video ref={videoRef} autoPlay playsInline className="video" />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            <canvas id="overlayCanvas" className="overlay-canvas" />
            <div className="scanner-status">
              {detected ? '✅ Carta detectada!' : '🔍 Procurando carta...'}
            </div>
            <button onClick={stopScanner} className="stop-btn">
              ❌ Cancelar
            </button>
          </div>
        )}

        {loading && (
          <div className="loading">
            ⏳ Processando...
          </div>
        )}

        {error && (
          <div className="error">
            ❌ {error}
          </div>
        )}

        {result && (
          <div className="result">
            <h2>✅ Carta Identificada</h2>
            <div className="card-info">
              <p><strong>Nome:</strong> {result.nome}</p>
              <p><strong>Número:</strong> {result.numero}</p>
              <p><strong>Coleção:</strong> {result.colecao} ({result.colecao_code})</p>
              <p><strong>Idioma:</strong> {result.idioma}</p>
              <p><strong>Confiança OCR:</strong> {result.confianca_ocr}</p>
            </div>
            <button onClick={reset} className="reset-btn">
              🔄 Escanear Outra
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
