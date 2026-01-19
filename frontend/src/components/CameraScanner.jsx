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
    console.log('[CAMERA] Starting with high resolution + autofocus...');
    setCameraStarted(true);

    try {
      // First get device list to find back camera
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(d => d.kind === 'videoinput');
      console.log('[CAMERA] Available devices:', videoDevices.map(d => d.label));
      
      const backCamera = videoDevices.find(d => {
        const label = d.label.toLowerCase();
        return label.includes('back') || label.includes('rear') || 
               label.includes('environment') || label.includes('traseira');
      });

      // Build constraints with REAL high resolution + continuous autofocus
      const constraints = {
        video: {
          deviceId: backCamera ? { exact: backCamera.deviceId } : undefined,
          facingMode: backCamera ? undefined : { ideal: 'environment' },
          width: { ideal: 1920, min: 1280 },
          height: { ideal: 1080, min: 720 },
          // Critical: enable continuous autofocus
          focusMode: { ideal: 'continuous' },
          // Additional quality settings
          aspectRatio: { ideal: 16/9 },
          frameRate: { ideal: 30, min: 15 }
        }
      };

      console.log('[CAMERA] Requesting with constraints:', JSON.stringify(constraints));
      
      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (e) {
        console.warn('[CAMERA] High-res failed, trying fallback:', e.message);
        // Fallback without advanced constraints
        stream = await navigator.mediaDevices.getUserMedia({
          video: { 
            facingMode: 'environment',
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        });
      }

      streamRef.current = stream;

      // Log actual track settings
      const track = stream.getVideoTracks()[0];
      const settings = track.getSettings();
      console.log('[CAMERA] Actual settings:', settings);

      // Try to apply continuous focus if supported
      const capabilities = track.getCapabilities?.();
      if (capabilities?.focusMode?.includes('continuous')) {
        try {
          await track.applyConstraints({ focusMode: 'continuous' });
          console.log('[CAMERA] Continuous autofocus enabled');
        } catch (e) {
          console.warn('[CAMERA] Could not set continuous focus:', e);
        }
      }

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        
        videoRef.current.onloadedmetadata = () => {
          // Wait for video to stabilize
          setTimeout(() => {
            const vw = videoRef.current.videoWidth;
            const vh = videoRef.current.videoHeight;
            console.log(`[CAMERA] Video ready: ${vw}x${vh}`);
            setVideoDims({ w: vw, h: vh });
            setCameraReady(true);
          }, 800);
        };
      }
    } catch (err) {
      console.error('[CAMERA] Fatal error:', err);
      setHint('Camera access denied or not available');
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

    // Create canvas at FULL video resolution
    const canvas = document.createElement('canvas');
    canvas.width = vw;
    canvas.height = vh;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, vw, vh);

    const count = frameCount + 1;
    setFrameCount(count);

    // Export as high-quality JPEG
    canvas.toBlob(async (blob) => {
      if (!blob) return;

      const sizeKB = (blob.size / 1024).toFixed(1);
      console.log(`[CAMERA] Frame #${count}: ${vw}x${vh}, ${sizeKB}KB`);

      const formData = new FormData();
      formData.append('file', blob, 'frame.jpg');

      try {
        const url = `${apiUrl}/scan${debug ? '?debug=true' : ''}`;
        const res = await fetch(url, { method: 'POST', body: formData });
        const data = await res.json();

        console.log(`[CAMERA] Response: status=${data.status}, name=${data.name || '-'}, boxes=${data.boxes?.length || 0}`);

        // Update hint based on status
        if (data.status === 'no_card_detected') {
          setHint('📷 Position card fully in frame');
        } else if (data.status === 'card_detected' || data.status === 'ok') {
          setHint('');
        } else if (data.status === 'ocr_failed') {
          setHint('🔍 Card found, reading text...');
        }

        onResult(data);
      } catch (e) {
        console.error('[CAMERA] Scan error:', e);
      }
    }, 'image/jpeg', 0.92);
  }, [apiUrl, scanning, cameraReady, onResult, frameCount, debug]);

  // Scan loop at ~2.5 FPS (400ms interval)
  useEffect(() => {
    if (!scanning || !cameraReady) return;
    const interval = setInterval(captureAndScan, 400);
    return () => clearInterval(interval);
  }, [scanning, cameraReady, captureAndScan]);

  // Draw overlay - boxes are in ORIGINAL frame coordinates
  useEffect(() => {
    if (!canvasRef.current || !videoRef.current) return;

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const ctx = canvas.getContext('2d');

    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 480;
    
    // Canvas MUST match video dimensions for correct overlay
    canvas.width = vw;
    canvas.height = vh;

    ctx.clearRect(0, 0, vw, vh);

    if (!boxes || boxes.length === 0) return;

    boxes.forEach(box => {
      if (box.type === 'quad' && box.points && box.points.length === 4) {
        // Draw card outline as green polygon
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 4;
        ctx.shadowColor = '#00ff00';
        ctx.shadowBlur = 8;
        
        ctx.beginPath();
        ctx.moveTo(box.points[0][0], box.points[0][1]);
        for (let i = 1; i < 4; i++) {
          ctx.lineTo(box.points[i][0], box.points[i][1]);
        }
        ctx.closePath();
        ctx.stroke();
        ctx.shadowBlur = 0;
        
        // Label
        ctx.fillStyle = '#00ff00';
        ctx.font = 'bold 16px sans-serif';
        ctx.fillText(`Card (${(box.conf * 100).toFixed(0)}%)`, box.points[0][0], box.points[0][1] - 8);
        
      } else if (box.x !== undefined && box.w > 0 && box.h > 0) {
        // Draw ROI rectangles
        const isTitle = box.label.includes('title');
        ctx.strokeStyle = isTitle ? '#00ffff' : '#ffff00';
        ctx.lineWidth = 2;
        ctx.strokeRect(box.x, box.y, box.w, box.h);

        // Label background
        ctx.fillStyle = ctx.strokeStyle;
        ctx.font = '12px sans-serif';
        const labelText = box.label.replace('roi_', '');
        ctx.fillText(labelText, box.x + 2, box.y - 4);
      }
    });
  }, [boxes]);

  // Render start button if camera not started
  if (!cameraStarted) {
    return (
      <div className="camera-container">
        <button className="start-camera-btn" onClick={startCamera}>
          📷 Start Camera
        </button>
        <p className="camera-tip">Tip: Use good lighting and hold card steady</p>
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
        {!cameraReady && <span className="loading">⏳ Starting camera...</span>}
        {cameraReady && (
          <>
            <span className="dims">{videoDims.w}×{videoDims.h}</span>
            <span className="frame">Frame #{frameCount}</span>
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
