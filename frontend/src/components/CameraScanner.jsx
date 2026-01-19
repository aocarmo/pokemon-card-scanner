// FILE: src/components/CameraScanner.jsx
import { useRef, useEffect, useState, useCallback } from 'react';

export default function CameraScanner({ apiUrl, scanning, onDetection, cardQuad, debug }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [videoDims, setVideoDims] = useState({ w: 0, h: 0 });

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          setVideoDims({ w: videoRef.current.videoWidth, h: videoRef.current.videoHeight });
          setCameraReady(true);
        };
      }
    } catch (err) {
      console.error('[CAMERA] Error:', err);
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
  };

  const captureAndScan = useCallback(async () => {
    if (!videoRef.current || !scanning || !cameraReady) return;
    
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const formData = new FormData();
      formData.append('file', blob, 'frame.jpg');
      
      try {
        const res = await fetch(`${apiUrl}/scan${debug ? '?debug=true' : ''}`, { 
          method: 'POST', 
          body: formData 
        });
        const data = await res.json();
        console.log('[CAMERA] Response:', data);
        onDetection(data);
      } catch (e) {
        console.error('[CAMERA] Error:', e);
      }
    }, 'image/jpeg', 0.9);
  }, [apiUrl, scanning, cameraReady, onDetection, debug]);

  // Scan loop ~3 FPS
  useEffect(() => {
    if (!scanning || !cameraReady) return;
    const interval = setInterval(captureAndScan, 333);
    return () => clearInterval(interval);
  }, [scanning, cameraReady, captureAndScan]);

  // Draw card outline only when detected
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) return;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');
    
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Only draw if we have a quad
    if (cardQuad && cardQuad.length === 4) {
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(cardQuad[0][0], cardQuad[0][1]);
      ctx.lineTo(cardQuad[1][0], cardQuad[1][1]);
      ctx.lineTo(cardQuad[2][0], cardQuad[2][1]);
      ctx.lineTo(cardQuad[3][0], cardQuad[3][1]);
      ctx.closePath();
      ctx.stroke();
    }
  }, [cardQuad]);

  return (
    <div className="camera-container">
      <div className="video-wrapper">
        <video ref={videoRef} autoPlay playsInline muted />
        <canvas ref={canvasRef} className="overlay-canvas" />
      </div>
      <div className="camera-status">
        {!cameraReady && <span>Starting camera...</span>}
        {cameraReady && <span className="dims">{videoDims.w}x{videoDims.h}</span>}
        {cameraReady && scanning && <span className="scanning">🔍 Scanning...</span>}
        {cameraReady && !scanning && <span className="paused">⏸ Paused</span>}
      </div>
    </div>
  );
}
