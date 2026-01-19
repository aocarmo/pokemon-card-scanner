// FILE: src/components/CameraScanner.jsx
import { useRef, useEffect, useState, useCallback } from 'react';

export default function CameraScanner({ apiUrl, scanning, onResult, boxes, debug = false }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const [videoDims, setVideoDims] = useState({ w: 0, h: 0 });

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  const startCamera = async () => {
    console.log('[CAMERA] Starting camera with high resolution...');
    try {
      // Try high resolution first, fallback to lower
      const constraints = {
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1920, min: 1280 },
          height: { ideal: 1080, min: 720 }
        }
      };
      
      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (e) {
        console.log('[CAMERA] High-res failed, trying fallback...');
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: 1280, height: 720 }
        });
      }
      
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          const vw = videoRef.current.videoWidth;
          const vh = videoRef.current.videoHeight;
          console.log(`[CAMERA] Camera ready: ${vw}x${vh}`);
          setVideoDims({ w: vw, h: vh });
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
    if (!videoRef.current || !scanning || !cameraReady) return;
    
    const video = videoRef.current;
    const vw = video.videoWidth;
    const vh = video.videoHeight;
    
    // Create canvas with REAL video dimensions
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = vw;
    tempCanvas.height = vh;
    const ctx = tempCanvas.getContext('2d');
    ctx.drawImage(video, 0, 0, vw, vh);

    const currentFrame = frameCount + 1;
    setFrameCount(currentFrame);
    console.log(`[CAMERA] Frame #${currentFrame}: ${vw}x${vh}`);

    // Export as high quality JPEG
    tempCanvas.toBlob(async (blob) => {
      if (!blob) {
        console.warn('[CAMERA] Failed to create blob');
        return;
      }
      
      const url = `${apiUrl}/scan${debug ? '?debug=true' : ''}`;
      console.log(`[CAMERA] POST ${url}, size: ${(blob.size/1024).toFixed(1)}KB`);
      
      const formData = new FormData();
      formData.append('file', blob, 'frame.jpg');
      
      try {
        const res = await fetch(url, { method: 'POST', body: formData });
        const data = await res.json();
        
        console.log('[CAMERA] Response:', {
          name: data.name || '(none)',
          number: data.number || '(none)',
          confidence: data.confidence?.toFixed(2),
          boxes: data.boxes?.length || 0,
          debug: data.debug
        });
        
        if (data.boxes) {
          console.log('[CAMERA] Boxes:', data.boxes.map(b => `${b.label}@(${b.x},${b.y},${b.w},${b.h})`));
        }
        
        onResult(data);
      } catch (e) {
        console.error('[CAMERA] Scan error:', e);
      }
    }, 'image/jpeg', 0.9);
  }, [apiUrl, scanning, cameraReady, onResult, frameCount, debug]);

  // Scan loop at ~2-3 fps
  useEffect(() => {
    if (!scanning || !cameraReady) {
      console.log(`[CAMERA] Loop paused: scanning=${scanning}, ready=${cameraReady}`);
      return;
    }
    console.log('[CAMERA] Starting scan loop (~2fps)');
    const interval = setInterval(captureAndScan, 400);
    return () => clearInterval(interval);
  }, [scanning, cameraReady, captureAndScan]);

  // Draw bounding boxes on overlay canvas
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) return;
    
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');
    
    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 480;
    
    // Canvas must match video resolution for correct box positioning
    canvas.width = vw;
    canvas.height = vh;
    
    ctx.clearRect(0, 0, vw, vh);

    if (boxes && boxes.length > 0) {
      console.log(`[CAMERA] Drawing ${boxes.length} boxes on ${vw}x${vh}`);
      
      boxes.forEach((box) => {
        // Color by label
        if (box.label === 'card' || box.label.includes('card')) {
          ctx.strokeStyle = '#00ff00';
          ctx.lineWidth = 4;
        } else if (box.label.includes('title')) {
          ctx.strokeStyle = '#00ffff';
          ctx.lineWidth = 3;
        } else if (box.label.includes('bottom') || box.label.includes('number')) {
          ctx.strokeStyle = '#ffff00';
          ctx.lineWidth = 3;
        } else {
          ctx.strokeStyle = '#ff00ff';
          ctx.lineWidth = 2;
        }
        
        ctx.strokeRect(box.x, box.y, box.w, box.h);
        
        // Label
        const label = `${box.label} ${(box.conf * 100).toFixed(0)}%`;
        ctx.font = 'bold 16px sans-serif';
        const tw = ctx.measureText(label).width;
        
        ctx.fillStyle = ctx.strokeStyle;
        ctx.fillRect(box.x, box.y - 24, tw + 8, 22);
        
        ctx.fillStyle = '#000';
        ctx.fillText(label, box.x + 4, box.y - 7);
      });
    } else {
      // Draw "no detection" indicator
      ctx.strokeStyle = '#ff0000';
      ctx.lineWidth = 2;
      ctx.setLineDash([10, 10]);
      ctx.strokeRect(50, 50, vw - 100, vh - 100);
      ctx.setLineDash([]);
      
      ctx.fillStyle = '#ff0000';
      ctx.font = 'bold 20px sans-serif';
      ctx.fillText('Position card in frame', 60, 40);
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
        {cameraReady && (
          <>
            <span className="dims">{videoDims.w}x{videoDims.h}</span>
            {scanning ? (
              <span className="scanning">🔍 Scanning... #{frameCount}</span>
            ) : (
              <span className="paused">⏸ Paused</span>
            )}
          </>
        )}
      </div>
    </div>
  );
}
