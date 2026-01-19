// FILE: src/App.jsx
import { useState, useCallback } from 'react';
import CameraScanner from './components/CameraScanner';
import ConfirmModal from './components/ConfirmModal';
import ImageUpload from './components/ImageUpload';
import ScanResult from './components/ScanResult';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const CONFIDENCE_THRESHOLD = 0.5;

export default function App() {
  const [mode, setMode] = useState('camera');
  const [scanResult, setScanResult] = useState(null);
  const [boxes, setBoxes] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [scanning, setScanning] = useState(true);
  const [error, setError] = useState(null);
  const [debug, setDebug] = useState(false);

  const handleScanResult = useCallback((result) => {
    console.log('[APP] Result:', result);
    
    if (result.error) {
      setBoxes([]);
      return;
    }
    
    // Always update boxes
    setBoxes(result.boxes || []);
    setScanResult(result);
    
    const hasFields = result.name && result.number;
    const confident = result.confidence >= CONFIDENCE_THRESHOLD;
    
    console.log(`[APP] name="${result.name}", number="${result.number}", conf=${result.confidence?.toFixed(2)}, pass=${hasFields && confident}`);
    
    if (hasFields && confident) {
      console.log('[APP] Card identified! Showing modal');
      setScanning(false);
      setShowModal(true);
    }
  }, []);

  const handleConfirm = async () => {
    try {
      await fetch(`${API_URL}/api/cards/confirm`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Bypass-Tunnel-Reminder': 'true'
        },
        body: JSON.stringify({
          name: scanResult.name,
          collection: scanResult.set || scanResult.collection || 'unknown',
          number: scanResult.number,
          language: scanResult.language || 'unknown'
        })
      });
    } catch (e) {
      console.error('[APP] Confirm error:', e);
    }
    resetAndResume();
  };

  const handleCancel = () => resetAndResume();

  const resetAndResume = () => {
    setShowModal(false);
    setScanResult(null);
    setBoxes([]);
    setScanning(true);
  };

  const handleUpload = async (file, dbg) => {
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`${API_URL}/api/cards/identify`, { 
        method: 'POST', 
        headers: { 'Bypass-Tunnel-Reminder': 'true' },
        body: formData 
      });
      const data = await res.json();
      if (data.error) setError(data.error);
      else {
        setScanResult(data);
        setBoxes(data.boxes || []);
        if (data.name && data.number && data.confidence >= CONFIDENCE_THRESHOLD) setShowModal(true);
      }
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="app">
      <h1>Pokemon Card Scanner</h1>
      
      <div className="controls">
        <div className="mode-toggle">
          <button className={mode === 'camera' ? 'active' : ''} onClick={() => setMode('camera')}>📷 Camera</button>
          <button className={mode === 'upload' ? 'active' : ''} onClick={() => setMode('upload')}>📁 Upload</button>
        </div>
        <label className="debug-toggle">
          <input type="checkbox" checked={debug} onChange={e => setDebug(e.target.checked)} />
          Debug
        </label>
      </div>

      {mode === 'camera' ? (
        <CameraScanner 
          apiUrl={API_URL} 
          scanning={scanning} 
          onResult={handleScanResult} 
          boxes={boxes}
          debug={debug}
        />
      ) : (
        <>
          <ImageUpload onUpload={handleUpload} loading={false} />
          {error && <p className="error">{error}</p>}
          {scanResult && <ScanResult result={scanResult} />}
        </>
      )}

      {/* Debug info panel */}
      {debug && scanResult && (
        <div className="debug-panel">
          <h4>Debug Info</h4>
          <pre>{JSON.stringify(scanResult.debug || {}, null, 2)}</pre>
          <p>Boxes: {boxes.length}</p>
          <p>Raw OCR Title: {scanResult.debug?.raw_ocr_title || 'N/A'}</p>
          <p>Raw OCR Bottom: {scanResult.debug?.raw_ocr_bottom_left || 'N/A'}</p>
        </div>
      )}

      {showModal && scanResult && (
        <ConfirmModal result={scanResult} onConfirm={handleConfirm} onCancel={handleCancel} />
      )}
    </div>
  );
}
