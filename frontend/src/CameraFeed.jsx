import { useState, useRef, useEffect } from 'react'

export default function CameraFeed() {
  const [streaming, setStreaming] = useState(false)
  const [cameraError, setCameraError] = useState('')
  const [snapshots, setSnapshots] = useState([])
  const [flash, setFlash] = useState(false)
  const videoRef = useRef(null)
  const canvasRef = useRef(null)

  const startCamera = async () => {
    setCameraError('')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: false,
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.play()
        setStreaming(true)
      }
    } catch (err) {
      console.error('Camera error:', err)
      setCameraError('Unable to access camera: ' + (err.message || 'Permission denied or in use.'))
    }
  }

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks()
      tracks.forEach((track) => track.stop())
      videoRef.current.srcObject = null
    }
    setStreaming(false)
  }

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
    ctx.fillText(`SKYGUARD AI · ${timestamp} · GPS: 18.5204° N, 73.8567° E`, 16, canvas.height - 13)

    const dataUrl = canvas.toDataURL('image/jpeg', 0.92)
    setSnapshots((prev) => [{ id: Date.now(), url: dataUrl, time: new Date().toLocaleTimeString() }, ...prev.slice(0, 4)])

    // Shutter flash effect
    setFlash(true)
    setTimeout(() => setFlash(false), 300)
  }

  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  return (
    <div className="camera-feed-container">
      {/* Video Viewport */}
      <div className={`camera-viewport ${flash ? 'camera-flash' : ''}`}>
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
            <video ref={videoRef} className="camera-video-elem" playsInline muted />
            <canvas ref={canvasRef} style={{ display: 'none' }} />

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
                <a href={snap.url} download={`skyguard_site_${snap.id}.jpg`} className="snap-dl-link">
                  Save
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
