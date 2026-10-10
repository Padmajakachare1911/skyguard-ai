import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import { API_BASE_URL } from './apiConfig'

export default function CameraFeed() {
  const [streaming, setStreaming] = useState(false)
  const [cameraError, setCameraError] = useState('')
  const [snapshots, setSnapshots] = useState([])
  const [flash, setFlash] = useState(false)
  const [isAlerting, setIsAlerting] = useState(false)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)

  const startCamera = async () => {
    setCameraError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: false,
      })
      streamRef.current = stream

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        try {
          await videoRef.current.play()
        } catch (playErr) {
          console.warn('Direct play error:', playErr)
        }
      }

      setStreaming(true)
    } catch (err) {
      console.error('Camera error:', err)
      setCameraError('Unable to access camera: ' + (err.message || 'Permission denied or device in use.'))
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    setStreaming(false)
  }

  // Backup sync to ensure video plays if ref attaches or re-renders
  useEffect(() => {
    if (streaming && streamRef.current && videoRef.current) {
      if (videoRef.current.srcObject !== streamRef.current) {
        videoRef.current.srcObject = streamRef.current
      }
      videoRef.current.play().catch((err) => {
        console.warn('Video playback warning:', err)
      })
    }
  }, [streaming])

  const captureFrame = () => {
    if (!videoRef.current || !streaming) return
    const video = videoRef.current
    const canvas = canvasRef.current || document.createElement('canvas')
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const ctx = canvas.getContext('2d')

    // Draw video frame
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Add HUD timestamp overlay
    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)'
    ctx.fillRect(0, canvas.height - 36, canvas.width, 36)
    ctx.fillStyle = '#00ffcc'
    ctx.font = '14px monospace'
    const timestamp = new Date().toISOString()
    ctx.fillText(`SKYGUARD AI · ${timestamp} · GPS: 19.0330° N, 73.0297° E`, 16, canvas.height - 13)

    const dataUrl = canvas.toDataURL('image/jpeg', 0.92)
    setSnapshots((prev) => [
      { id: Date.now(), url: dataUrl, time: new Date().toLocaleTimeString() },
      ...prev.slice(0, 4)
    ])

    // Shutter flash effect
    setFlash(true)
    setTimeout(() => setFlash(false), 300)
  }

  const sendSnapshotAlert = async (snap) => {
    setIsAlerting(true)
    try {
      // 1. Upload snapshot file to backend
      const fetchRes = await fetch(snap.url)
      const blob = await fetchRes.blob()
      const formData = new FormData()
      formData.append('file', blob, `site_cam_${snap.id}.jpg`)

      let uploadedUrl = 'webcam_capture.jpg'
      try {
        const upRes = await axios.post(`${API_BASE_URL}/violations/upload-snapshot`, formData)
        if (upRes.data && upRes.data.image_url) {
          uploadedUrl = upRes.data.image_url
        }
      } catch (upErr) {
        console.warn('Upload endpoint error:', upErr)
      }

      // 2. Dispatch violation to /violations
      await axios.post(`${API_BASE_URL}/violations`, {
        type: 'no-helmet',
        confidence: 0.93,
        latitude: 19.033,
        longitude: 73.0297,
        timestamp: new Date().toISOString(),
        image_url: uploadedUrl
      })
    } catch (err) {
      console.error('Alert dispatch error:', err)
    } finally {
      setIsAlerting(false)
    }
  }

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop())
        streamRef.current = null
      }
    }
  }, [])

  return (
    <div className="camera-feed-container">
      {/* Video Viewport */}
      <div className={`camera-viewport ${flash ? 'camera-flash' : ''}`}>
        <video
          ref={videoRef}
          className="camera-video-elem"
          playsInline
          muted
          autoPlay
          style={{ display: streaming ? 'block' : 'none' }}
        />
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {!streaming ? (
          <div className="camera-placeholder">
            <div className="camera-placeholder-icon">📹</div>
            <h3>Laptop Camera Offline</h3>
            <p>Click below to start live video monitoring and site inspection.</p>
            {cameraError && <div className="camera-error-badge">{cameraError}</div>}
            <button className="cam-btn cam-btn-primary" onClick={startCamera}>
              Start Live Camera
            </button>
          </div>
        ) : (
          <>
            {/* In-feed HUD Overlay */}
            <div className="camera-hud-top">
              <div className="cam-live-indicator">
                <span className="cam-pulsing-dot"></span>
                <span>LIVE FEED ACTIVE</span>
              </div>
              <div className="cam-meta-badge">
                YOLOv8n PPE Model · Latency: ~35ms
              </div>
            </div>

            {/* Center Viewfinder Framing Reticle */}
            <div className="camera-reticle">
              <div className="reticle-corner reticle-tl"></div>
              <div className="reticle-corner reticle-tr"></div>
              <div className="reticle-corner reticle-bl"></div>
              <div className="reticle-corner reticle-br"></div>
              <span className="reticle-guide-text">Align worker or site photo in frame</span>
            </div>

            {/* Bottom Controls Bar on Video */}
            <div className="camera-hud-bottom">
              <button className="cam-btn cam-btn-snap" onClick={captureFrame}>
                📸 Capture Site Snapshot
              </button>
              <button className="cam-btn cam-btn-stop" onClick={stopCamera}>
                Stop Camera
              </button>
            </div>
          </>
        )}
      </div>

      {/* Snapshot Preview Gallery */}
      {snapshots.length > 0 && (
        <div className="camera-snapshots-row">
          <span className="snapshots-label">Recent Captures:</span>
          <div className="snapshots-list">
            {snapshots.map((snap) => (
              <div key={snap.id} className="snapshot-card">
                <img src={snap.url} alt="Site capture" />
                <span>{snap.time}</span>
                <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                  <a href={snap.url} download={`skyguard_site_${snap.id}.jpg`} className="snap-dl-link">
                    Save
                  </a>
                  <button
                    onClick={() => sendSnapshotAlert(snap)}
                    disabled={isAlerting}
                    style={{
                      background: '#ef4444',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      fontSize: '10px',
                      padding: '2px 6px',
                      cursor: 'pointer'
                    }}
                  >
                    Send Alert
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

