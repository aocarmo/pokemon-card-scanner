// FILE: src/App.jsx
import { useState, useCallback } from 'react';
import CameraScanner from './components/CameraScanner';
import ConfirmModal from './components/ConfirmModal';
import ImageUpload from './components/ImageUpload';
import ScanResult from './components/ScanResult';
import './App.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const RESULT_CONFIDENCE_THRESHOLD = 0.4;

export default function App() {
  const [mode, setMode] = useState('camera');
  const [scanning, setScanning] = useState(true);
  const [cardQuad, setCardQuad] = useState(null);
  const [cardResult, setCardResult] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [debug, setDebug] = useState(false);
  const [error, setError] = useState(null);

  const handleDetection = useCallback((data) => {
    // No detection - clear overlay
    if (!data.detected) {
      setCardQuad(null);
      return;
    }

    // Detection but no result yet - show outline only
    setCardQuad(data.card_quad);

    // If we have a result with sufficient confidence, show modal
    if (data.result && data.result.name && data.result.confidence >= RESULT_CONFIDENCE_THRESHOLD) {
      console.log('[APP] Card identified:', data.result);
      setCardResult(data.result);
      setScanning(false);
      setShowModal(true);
    }
  }, []);

  const handleConfirm = async () => {
    try {
      await fetch(`${API_URL}/cards/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: cardResult.name,
          collection: cardResult.collection || 'unknown',
          number: cardResult.number || '',
          language: cardResult.language || 'unknown'
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
    setCardResult(null);
    setCardQuad(null);
    setScanning(true);
  };

  const handleUpload = async (file, dbg) => {
    setError(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`${API_URL}/scan${dbg ? '?debug=true' : ''}`, { method: 'POST', body: formData });
      const data = await res.json();
      if (data.result) {
        setCardResult(data.result);
        setShowModal(true);
      } else if (data.error) {
        setError(data.error);
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
          onDetection={handleDetection} 
          cardQuad={cardQuad}
          debug={debug}
        />
      ) : (
        <>
          <ImageUpload onUpload={handleUpload} loading={false} />
          {error && <p className="error">{error}</p>}
          {cardResult && <ScanResult result={cardResult} />}
        </>
      )}

      {showModal && cardResult && (
        <ConfirmModal result={cardResult} onConfirm={handleConfirm} onCancel={handleCancel} />
      )}
    </div>
  );
}
