// FILE: src/components/CameraScanner.jsx
import { useRef, useEffect, useState, useCallback } from 'react';

export default function CameraScanner({ apiUrl, scanning, onResult, boxes, debug }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraStarted, setCameraStarted] = useState(false);
  const [videoDims, setVideoDims] = useState({ w: 0, h: 0 });
  const [frameCount, setFrameCount] = useState(0);
  const [hint, setHint] = useState('');

  const startCamera = async () => {
    console.log('[CAMERA] Starting...');
    setCameraStarted(true);

    try {
      // Get back camera explicitly
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(d => d.kind === 'videoinput');
      const backCamera = videoDevices.find(d => 
        d.label.toLowerCase().includes('back') || 
        d.label.toLowerCase().includes('rear') ||
        d.label.toLowerCase().includes('environment')
      );

      const constraints = {
        video: {
          deviceId: backCamera ? { exact: backCamera.deviceId } : undefined,
          facingMode: backCamera ? undefined : { ideal: 'environment' },
          width: { ideal: 1920, min: 1280 },
          height: { ideal: 1080, min: 720 }
        }
      };

      console.log('[CAMERA] Constraints:', constraints);
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          // Stabilization delay
          setTimeout(() => {
            const vw = videoRef.current.videoWidth;
            const vh = videoRef.current.videoHeight;
            console.log(`[CAMERA] Ready: ${vw}x${vh}`);
            setVideoDims({ w: vw, h: vh });
            setCameraReady(true);
          }, 600);
        };
      }
    } catch (err) {
      console.error('[CAMERA] Error:', err);
      setHint('Camera access denied');
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach(t => t.stop());
    setCameraReady(false);
    setCameraStarted(false);
  };

  useEffect(() => {
    return () => stopCamera();
  }, []);

  const captureAndScan = useCallback(async () => {
    if (!videoRef.current || !scanning || !cameraReady) return;

    const video = videoRef.current;
    const vw = video.videoWidth;
    const vh = video.videoHeight;

    const canvas = document.createElement('canvas');
    canvas.width = vw;
    canvas.height = vh;
    canvas.getContext('2d').drawImage(video, 0, 0, vw, vh);

    const count = frameCount + 1;
    setFrameCount(count);

    canvas.toBlob(async (blob) => {
      if (!blob) return;

      console.log(`[CAMERA] Frame #${count}: ${vw}x${vh}, ${(blob.size/1024).toFixed(1)}KB`);

      const formData = new FormData();
      formData.append('file', blob, 'frame.jpg');

      try {
        const res = await fetch(`${apiUrl}/scan${debug ? '?debug=true' : ''}`, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        
        console.log('[CAMERA] Response:', data.status, data.name, `boxes=${data.boxes?.length}`);
        
        if (data.status === 'no_card_detected') {
          setHint('Position card fully in frame');
        } else {
          setHint('');
        }
        
        onResult(data);
      } catch (e) {
        console.error('[CAMERA] Error:', e);
      }
    }, 'image/jpeg', 0.9);
  }, [apiUrl, scanning, cameraReady, onResult, frameCount, debug]);

  // Scan loop ~3 FPS
  useEffect(() => {
    if (!scanning || !cameraReady) return;
    const interval = setInterval(captureAndScan, 350);
    return () => clearInterval(interval);
  }, [scanning, cameraReady, captureAndScan]);

  // Draw overlay
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) return;

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');

    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 480;
    canvas.width = vw;
    canvas.height = vh;

    ctx.clearRect(0, 0, vw, vh);

    if (!boxes || boxes.length === 0) return;

    boxes.forEach(box => {
      if (box.type === 'quad' && box.points) {
        // Draw card outline as polygon
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(box.points[0][0], box.points[0][1]);
        for (let i = 1; i < box.points.length; i++) {
          ctx.lineTo(box.points[i][0], box.points[i][1]);
        }
        ctx.closePath();
        ctx.stroke();
      } else if (box.x !== undefined) {
        // Draw ROI rectangle
        ctx.strokeStyle = box.label.includes('title') ? '#00ffff' : '#ffff00';
        ctx.lineWidth = 2;
        ctx.strokeRect(box.x, box.y, box.w, box.h);
        
        // Label
        ctx.fillStyle = ctx.strokeStyle;
        ctx.font = '14px sans-serif';
        ctx.fillText(box.label, box.x, box.y - 4);
      }
    });
  }, [boxes]);

  if (!cameraStarted) {
    return (
      <div className="camera-container">
        <button className="start-camera-btn" onClick={startCamera}>
          📷 Start Camera
        </button>
      </div>
    );
  }

  return (
    <div className="camera-container">
      <div className="video-wrapper">
        <video ref={videoRef} autoPlay playsInline muted />
        <canvas ref={canvasRef} className="overlay-canvas" />
        {hint && <div className="camera-hint">{hint}</div>}
      </div>
      <div className="camera-status">
        {!cameraReady && <span>Starting camera...</span>}
        {cameraReady && (
          <>
            <span className="dims">{videoDims.w}x{videoDims.h}</span>
            <span>Frame #{frameCount}</span>
            {scanning ? (
              <span className="scanning">🔍 Scanning</span>
            ) : (
              <span className="paused">⏸ Paused</span>
            )}
          </>
        )}
      </div>
    </div>
  );
}
