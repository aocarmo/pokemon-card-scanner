// FILE: src/components/CameraScanner.jsx
import { useRef, useEffect, useState, useCallback } from 'react';

export default function CameraScanner({ apiUrl, scanning, onResult, boxes }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [frameCount, setFrameCount] = useState(0);

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  const startCamera = async () => {
    console.log('[CAMERA] Starting camera...');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: 1280, height: 720 }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          console.log('[CAMERA] Camera ready');
          setCameraReady(true);
        };
      }
    } catch (err) {
      console.error('[CAMERA] Error:', err);
    }
  };

  const stopCamera = () => {
    console.log('[CAMERA] Stopping camera');
    streamRef.current?.getTracks().forEach(track => track.stop());
  };

  const captureAndScan = useCallback(async () => {
    if (!videoRef.current || !scanning || !cameraReady) {
      return;
    }
    
    const video = videoRef.current;
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    tempCanvas.getContext('2d').drawImage(video, 0, 0);

    setFrameCount(prev => prev + 1);
    console.log(`[CAMERA] Capturing frame #${frameCount + 1}, size: ${video.videoWidth}x${video.videoHeight}`);

    tempCanvas.toBlob(async (blob) => {
      if (!blob) {
        console.warn('[CAMERA] Failed to create blob');
        return;
      }
      
      console.log(`[CAMERA] Sending frame to ${apiUrl}/scan, blob size: ${blob.size}`);
      
      const formData = new FormData();
      formData.append('file', blob, 'frame.jpg');
      
      try {
        const res = await fetch(`${apiUrl}/scan`, { method: 'POST', body: formData });
        const data = await res.json();
        
        console.log('[CAMERA] Response received:', {
          name: data.name,
          number: data.number,
          confidence: data.confidence,
          boxCount: data.boxes?.length || 0,
          boxes: data.boxes
        });
        
        onResult(data);
      } catch (e) {
        console.error('[CAMERA] Scan error:', e);
      }
    }, 'image/jpeg', 0.8);
  }, [apiUrl, scanning, cameraReady, onResult, frameCount]);

  // Scan loop at ~2 fps
  useEffect(() => {
    if (!scanning || !cameraReady) {
      console.log(`[CAMERA] Scan loop paused: scanning=${scanning}, cameraReady=${cameraReady}`);
      return;
    }
    
    console.log('[CAMERA] Starting scan loop (2fps)');
    const interval = setInterval(captureAndScan, 500);
    return () => {
      console.log('[CAMERA] Stopping scan loop');
      clearInterval(interval);
    };
  }, [scanning, cameraReady, captureAndScan]);

  // Draw bounding boxes
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) return;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');
    
    // Match canvas size to video
    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 480;
    canvas.width = vw;
    canvas.height = vh;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (boxes && boxes.length > 0) {
      console.log(`[CAMERA] Drawing ${boxes.length} boxes on canvas ${vw}x${vh}`);
      
      boxes.forEach((box, i) => {
        // Card box - green
        if (box.label === 'card' || i === 0) {
          ctx.strokeStyle = '#00ff00';
          ctx.lineWidth = 4;
        } else {
          // ROI boxes - yellow
          ctx.strokeStyle = '#ffff00';
          ctx.lineWidth = 2;
        }
        
        ctx.strokeRect(box.x, box.y, box.w, box.h);
        
        // Label background
        ctx.fillStyle = ctx.strokeStyle;
        const label = `${box.label} (${(box.conf * 100).toFixed(0)}%)`;
        const textWidth = ctx.measureText(label).width;
        ctx.fillRect(box.x, box.y - 22, textWidth + 8, 20);
        
        // Label text
        ctx.fillStyle = '#000000';
        ctx.font = 'bold 14px sans-serif';
        ctx.fillText(label, box.x + 4, box.y - 7);
      });
    }
  }, [boxes]);

  return (
    <div className="camera-container">
      <div className="video-wrapper">
        <video ref={videoRef} autoPlay playsInline muted />
        <canvas ref={canvasRef} className="overlay-canvas" />
      </div>
      <div className="camera-status">
        {!cameraReady && <span>Starting camera...</span>}
        {cameraReady && scanning && <span className="scanning">🔍 Scanning... (Frame #{frameCount})</span>}
        {cameraReady && !scanning && <span className="paused">⏸ Paused - Card Detected!</span>}
      </div>
    </div>
  );
}
