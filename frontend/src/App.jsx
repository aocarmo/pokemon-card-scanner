// FILE: src/App.jsx
import { useState } from 'react';
import CameraScanner from './components/CameraScanner';
import ConfirmModal from './components/ConfirmModal';
import ImageUpload from './components/ImageUpload';
import ScanResult from './components/ScanResult';
import './App.css';

const API_URL = 'http://localhost:8000';
const CONFIDENCE_THRESHOLD = 0.6;

export default function App() {
  const [mode, setMode] = useState('camera');
  const [scanResult, setScanResult] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [scanning, setScanning] = useState(true);
  const [error, setError] = useState(null);

  const handleScanResult = (result) => {
    if (result.error) return;
    setScanResult(result);
    if (result.name && result.number && result.confidence >= CONFIDENCE_THRESHOLD) {
      setScanning(false);
      setShowModal(true);
    }
  };

  const handleConfirm = async () => {
    try {
      await fetch(`${API_URL}/cards/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: scanResult.name,
          collection: scanResult.set || 'unknown',
          number: scanResult.number,
          language: scanResult.language || 'unknown'
        })
      });
    } catch (e) {
      console.error('Confirm error:', e);
    }
    setShowModal(false);
    setScanResult(null);
    setScanning(true);
  };

  const handleCancel = () => {
    setShowModal(false);
    setScanResult(null);
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
        <CameraScanner apiUrl={API_URL} scanning={scanning} onResult={handleScanResult} boxes={scanResult?.boxes || []} />
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
