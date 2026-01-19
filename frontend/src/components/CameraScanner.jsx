// FILE: src/components/CameraScanner.jsx
import { useRef, useEffect, useState, useCallback } from 'react';

export default function CameraScanner({ apiUrl, scanning, onResult, boxes }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraReady, setCameraReady] = useState(false);

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: 1280, height: 720 }
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => setCameraReady(true);
      }
    } catch (err) {
      console.error('Camera error:', err);
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach(track => track.stop());
  };

  const captureAndScan = useCallback(async () => {
    if (!videoRef.current || !scanning || !cameraReady) return;
    const video = videoRef.current;
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = video.videoWidth;
    tempCanvas.height = video.videoHeight;
    tempCanvas.getContext('2d').drawImage(video, 0, 0);

    tempCanvas.toBlob(async (blob) => {
      if (!blob) return;
      const formData = new FormData();
      formData.append('file', blob, 'frame.jpg');
      try {
        const res = await fetch(`${apiUrl}/scan`, { method: 'POST', body: formData });
        onResult(await res.json());
      } catch (e) {}
    }, 'image/jpeg', 0.8);
  }, [apiUrl, scanning, cameraReady, onResult]);

  useEffect(() => {
    if (!scanning || !cameraReady) return;
    const interval = setInterval(captureAndScan, 500);
    return () => clearInterval(interval);
  }, [scanning, cameraReady, captureAndScan]);

  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) return;
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (boxes?.length > 0) {
      ctx.strokeStyle = '#00ff00';
      ctx.lineWidth = 3;
      ctx.font = '16px sans-serif';
      ctx.fillStyle = '#00ff00';
      boxes.forEach(box => {
        ctx.strokeRect(box.x, box.y, box.w, box.h);
        ctx.fillText(`${box.label} (${(box.conf * 100).toFixed(0)}%)`, box.x, box.y - 5);
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
        {cameraReady && scanning && <span className="scanning">🔍 Scanning...</span>}
        {cameraReady && !scanning && <span className="paused">⏸ Paused</span>}
      </div>
    </div>
  );
}
