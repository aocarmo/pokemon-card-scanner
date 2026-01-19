// FILE: src/App.jsx
// Run: npm install && npm start
// Expects backend at http://localhost:8000
import { useState } from 'react';
import ImageUpload from './components/ImageUpload';
import ScanResult from './components/ScanResult';
import './App.css';

const API_URL = 'http://localhost:8000';

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (file, debug) => {
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const url = `${API_URL}/scan${debug ? '?debug=true' : ''}`;
      const res = await fetch(url, { method: 'POST', body: formData });
      const data = await res.json();
      
      if (data.error) {
        setError(data.error);
      } else {
        if (data.debug_image) {
          data.debug_image = `${API_URL}${data.debug_image}`;
        }
        setResult(data);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <h1>Pokemon Card Scanner</h1>
      <ImageUpload onUpload={handleUpload} loading={loading} />
      {error && <p className="error">{error}</p>}
      {result && <ScanResult result={result} />}
    </div>
  );
}
