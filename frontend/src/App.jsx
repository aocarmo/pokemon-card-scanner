// FILE: src/App.jsx
import { useState, useCallback } from 'react';
import CameraScanner from './components/CameraScanner';
import ConfirmModal from './components/ConfirmModal';
import ImageUpload from './components/ImageUpload';
import ScanResult from './components/ScanResult';
import './App.css';

const API_URL = 'http://localhost:8000';
const CONFIDENCE_THRESHOLD = 0.5;

export default function App() {
  const [mode, setMode] = useState('camera');
  const [scanResult, setScanResult] = useState(null);
  const [boxes, setBoxes] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [scanning, setScanning] = useState(true);
  const [error, setError] = useState(null);

  const handleScanResult = useCallback((result) => {
    console.log('[APP] Scan result received:', result);
    
    if (result.error) {
      console.log('[APP] Scan error, continuing...');
      setBoxes([]);
      return;
    }
    
    // Always update boxes for live overlay
    if (result.boxes && result.boxes.length > 0) {
      console.log(`[APP] Updating ${result.boxes.length} boxes`);
      setBoxes(result.boxes);
    } else {
      setBoxes([]);
    }
    
    setScanResult(result);
    
    const hasRequiredFields = result.name && result.number;
    const isConfident = result.confidence >= CONFIDENCE_THRESHOLD;
    
    console.log(`[APP] Check: name="${result.name}", number="${result.number}", conf=${result.confidence}, threshold=${CONFIDENCE_THRESHOLD}`);
    console.log(`[APP] hasRequiredFields=${hasRequiredFields}, isConfident=${isConfident}`);
    
    if (hasRequiredFields && isConfident) {
      console.log('[APP] Card identified! Pausing scan and showing modal');
      setScanning(false);
      setShowModal(true);
    }
  }, []);

  const handleConfirm = async () => {
    console.log('[APP] Confirming card:', scanResult);
    try {
      const response = await fetch(`${API_URL}/cards/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: scanResult.name,
          collection: scanResult.set || 'unknown',
          number: scanResult.number,
          language: scanResult.language || 'unknown'
        })
      });
      const data = await response.json();
      console.log('[APP] Confirm response:', data);
    } catch (e) {
      console.error('[APP] Confirm error:', e);
    }
    setShowModal(false);
    setScanResult(null);
    setBoxes([]);
    setScanning(true);
    console.log('[APP] Resuming scanning');
  };

  const handleCancel = () => {
    console.log('[APP] Cancel clicked, resuming scanning');
    setShowModal(false);
    setScanResult(null);
    setBoxes([]);
    setScanning(true);
  };

  const handleUpload = async (file, debug) => {
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`${API_URL}/scan${debug ? '?debug=true' : ''}`, { method: 'POST', body: formData });
      const data = await res.json();
      if (data.error) setError(data.error);
      else {
        setScanResult(data);
        if (data.name && data.number && data.confidence >= CONFIDENCE_THRESHOLD) setShowModal(true);
      }
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="app">
      <h1>Pokemon Card Scanner</h1>
      <div className="mode-toggle">
        <button className={mode === 'camera' ? 'active' : ''} onClick={() => setMode('camera')}>📷 Camera</button>
        <button className={mode === 'upload' ? 'active' : ''} onClick={() => setMode('upload')}>📁 Upload</button>
      </div>
      {mode === 'camera' ? (
        <CameraScanner 
          apiUrl={API_URL} 
          scanning={scanning} 
          onResult={handleScanResult} 
          boxes={boxes} 
        />
      ) : (
        <>
          <ImageUpload onUpload={handleUpload} loading={false} />
          {error && <p className="error">{error}</p>}
          {scanResult && <ScanResult result={scanResult} />}
        </>
      )}
      {showModal && scanResult && <ConfirmModal result={scanResult} onConfirm={handleConfirm} onCancel={handleCancel} />}
    </div>
  );
}
