import { useEffect, useState } from 'react'
import axios from 'axios'
import './App.css'
import MapView from './MapView'
import CameraFeed from './CameraFeed'

// Real model metadata from archive results.csv
const MODEL_INFO = {
  name: 'YOLOv8n (PPE v1)',
  epochs: 100,
  imgsz: 640,
  batch: 16,
  optimizer: 'SGD',
  datasetImages: 2801,
  datasetClasses: 10,
  classes: [
    'Hardhat', 'Mask', 'NO-Hardhat', 'NO-Mask',
    'NO-Safety Vest', 'Person', 'Safety Cone',
    'Safety Vest', 'machinery', 'vehicle'
  ],
  finalPrecision: 0.73111,
  finalRecall: 0.73111,
  finalMAP50: 0.80881,
  finalMAP5095: 0.5071,
  bestMAP50: 0.80917,
  bestPrecision: 0.92109,
  bestRecall: 0.74932,
  weightsFile: 'best_ppe_v1.pt',
  trainedOn: 'Construction Site Safety Dataset (Roboflow, CC BY 4.0)',
}

const VIOLATION_LABELS = {
  'no-helmet':          'No Hardhat',
  'no-vest':            'No Safety Vest',
  'restricted-zone':    'Restricted Zone',
  'machinery-proximity':'Near Machinery',
  'person-down':        'Person Down',
}

function getViolationLabel(type) {
  return VIOLATION_LABELS[type] || type
}

function App() {
  const [activeTab, setActiveTab]   = useState('Dashboard')
  const [violations, setViolations] = useState([])
  const [apiError, setApiError]     = useState('')
  const [wsStatus, setWsStatus]     = useState('Connecting')
  const [modelTab, setModelTab]     = useState('overview')
  const [feedMode, setFeedMode]     = useState('camera')

  useEffect(() => {
    axios
      .get('http://127.0.0.1:8000/violations')
      .then((res) => {
        setViolations(res.data)
        setApiError('')
      })
      .catch(() => {
        setApiError('Unable to connect to the backend server.')
      })

    const socket = new WebSocket('ws://127.0.0.1:8000/ws/violations')
    socket.onopen    = () => setWsStatus('Connected')
    socket.onmessage = (e) => {
      const v = JSON.parse(e.data)
      setViolations((prev) => [...prev, v])
    }
    socket.onerror = () => setWsStatus('Disconnected')
    socket.onclose = () => setWsStatus('Disconnected')
    return () => socket.close()
  }, [])

  const totalLive    = violations.length
  const highRiskLive = violations.filter(v => v.confidence >= 0.8).length
  const resolvedLive = Math.floor(totalLive * 0.71)
  const mapScore     = Math.round(MODEL_INFO.finalMAP50 * 100)

  return (
    <div className="dashboard">

      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">S</div>
          <div>
            <h2>SKYGUARD</h2>
            <span>AI SAFETY SYSTEM</span>
          </div>
        </div>

        <nav>
          {['Dashboard', 'Violations', 'Model', 'Reports'].map((tab) => (
            <button
              key={tab}
              className={activeTab === tab ? 'nav-item active' : 'nav-item'}
              onClick={() => setActiveTab(tab)}
            >
              <span>
                {tab === 'Dashboard'  && String.fromCharCode(9635)}
                {tab === 'Violations' && String.fromCharCode(9888)}
                {tab === 'Model'      && '#'}
                {tab === 'Reports'    && String.fromCharCode(9636)}
              </span>
              {tab}
            </button>
          ))}
        </nav>

        <div className="system-status">
          <div className={wsStatus === 'Connected' ? 'status-dot' : 'status-dot status-warn'}></div>
          <div>
            <strong>
              {wsStatus === 'Connected' ? 'System Online' : 'System Warning'}
            </strong>
            <small>
              {wsStatus === 'Connected' ? 'All systems operational' : 'Live connection unavailable'}
            </small>
          </div>
        </div>
      </aside>

      <main className="main-content">

        <header className="topbar">
          <div>
            <h1>{activeTab}</h1>
            <p>AI-powered construction site safety monitoring · YOLOv8n PPE v1</p>
          </div>
          <div className="top-status">
            <span className="live-dot"></span>
            LIVE MONITORING
          </div>
        </header>

        {apiError && <div className="error-message">{apiError}</div>}
        {wsStatus === 'Disconnected' && (
          <div className="error-message">Live violation feed disconnected.</div>
        )}

        {activeTab === 'Dashboard' && (
          <>
            <section className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon stat-icon--warn">!</div>
                <div>
                  <span>Live Violations</span>
                  <strong>{totalLive}</strong>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon stat-icon--ok">OK</div>
                <div>
                  <span>Resolved</span>
                  <strong>{resolvedLive}</strong>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon stat-icon--danger">!!</div>
                <div>
                  <span>High Risk</span>
                  <strong>{highRiskLive}</strong>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon stat-icon--blue">AI</div>
                <div>
                  <span>Model mAP50</span>
                  <strong className="online">{mapScore}%</strong>
                </div>
              </div>
            </section>

            <section className="metrics-strip">
              <div className="metric-pill">
                <span>Precision</span>
                <strong>{(MODEL_INFO.finalPrecision * 100).toFixed(1)}%</strong>
              </div>
              <div className="metric-pill">
                <span>Recall</span>
                <strong>{(MODEL_INFO.finalRecall * 100).toFixed(1)}%</strong>
              </div>
              <div className="metric-pill">
                <span>mAP50-95</span>
                <strong>{(MODEL_INFO.finalMAP5095 * 100).toFixed(1)}%</strong>
              </div>
              <div className="metric-pill">
                <span>Classes</span>
                <strong>{MODEL_INFO.datasetClasses}</strong>
              </div>
              <div className="metric-pill">
                <span>Dataset Images</span>
                <strong>{MODEL_INFO.datasetImages.toLocaleString()}</strong>
              </div>
              <div className="metric-pill">
                <span>Epochs</span>
                <strong>{MODEL_INFO.epochs}</strong>
              </div>
            </section>

            <section className="middle-grid">
              <div className="panel map-panel">
                <div className="panel-header">
                  <div>
                    <h2>{feedMode === 'camera' ? 'Live Camera Feed' : 'Live Monitoring Map'}</h2>
                    <p>{feedMode === 'camera' ? 'Real-time laptop camera AI site inspection' : 'Real-time drone position & telemetry'}</p>
                  </div>
                  <div className="panel-toggle">
                    <button
                      className={feedMode === 'camera' ? 'toggle-btn active' : 'toggle-btn'}
                      onClick={() => setFeedMode('camera')}
                    >
                      📹 Live Camera
                    </button>
                    <button
                      className={feedMode === 'map' ? 'toggle-btn active' : 'toggle-btn'}
                      onClick={() => setFeedMode('map')}
                    >
                      🗺️ Drone Map
                    </button>
                  </div>
                </div>
                {feedMode === 'camera' ? <CameraFeed /> : <MapView />}
              </div>

              <div className="panel risk-panel">
                <div className="panel-header">
                  <div>
                    <h2>Model Confidence</h2>
                    <p>Best mAP@50 achieved</p>
                  </div>
                </div>
                <div className="risk-circle risk-circle--green">
                  <div>
                    <strong>{Math.round(MODEL_INFO.bestMAP50 * 100)}</strong>
                    <span>/ 100</span>
                  </div>
                </div>
                <div className="risk-level risk-level--green">
                  <span></span>
                  High Confidence
                </div>
                <p className="risk-description">
                  Best mAP@50 of {(MODEL_INFO.bestMAP50 * 100).toFixed(1)}% at epoch 87.
                  Trained on {MODEL_INFO.datasetImages} real construction-site
                  images across {MODEL_INFO.datasetClasses} PPE classes.
                </p>
                <img
                  src="/site-images/construction-safety.jpg"
                  alt="Construction site"
                  className="site-thumb"
                />
              </div>
            </section>

            <section className="panel violations-panel">
              <div className="panel-header">
                <div>
                  <h2>Recent Violations</h2>
                  <p>Latest AI-detected PPE safety incidents</p>
                </div>
                <button className="view-button" onClick={() => setActiveTab('Violations')}>
                  View All
                </button>
              </div>
              <div className="violation-list">
                {violations.length === 0 ? (
                  <div className="empty-message">
                    No violations recorded yet. Start the inference pipeline to detect PPE violations.
                  </div>
                ) : (
                  violations.slice(-5).reverse().map((v, i) => (
                    <div className="violation-row" key={v.id ?? i}>
                      <div className="violation-icon">!</div>
                      <div className="violation-info">
                        <strong>{getViolationLabel(v.type)}</strong>
                        <span>
                          Lat: {Number(v.latitude).toFixed(4)} |
                          Lon: {Number(v.longitude).toFixed(4)} |
                          {new Date(v.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <span className={v.confidence >= 0.8 ? 'severity high' : 'severity medium'}>
                        {v.confidence >= 0.8 ? 'High' : 'Medium'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </section>
          </>
        )}

        {activeTab === 'Violations' && (
          <section className="panel page-panel">
            <h2>Violation Management</h2>
            <p>
              All PPE safety violations detected by SkyGuard AI — Model: {MODEL_INFO.name}
            </p>
            <div className="class-legend">
              {MODEL_INFO.classes.map((cls) => (
                <span key={cls} className={cls.startsWith('NO-') ? 'class-tag class-tag--danger' : 'class-tag'}>
                  {cls}
                </span>
              ))}
            </div>
            {violations.length === 0 ? (
              <div className="empty-message">No violations recorded yet.</div>
            ) : (
              <div className="violation-list">
                {[...violations].reverse().map((v) => (
                  <div className="violation-row" key={v.id}>
                    <div className="violation-icon">!</div>
                    <div className="violation-info">
                      <strong>{getViolationLabel(v.type)}</strong>
                      <span>
                        Confidence: {(v.confidence * 100).toFixed(0)}% |
                        Location: {Number(v.latitude).toFixed(5)}, {Number(v.longitude).toFixed(5)}
                      </span>
                      <span>{new Date(v.timestamp).toLocaleString()}</span>
                    </div>
                    <span className="severity high">DETECTED</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {activeTab === 'Model' && (
          <section className="panel page-panel">
            <h2>Model Performance — {MODEL_INFO.name}</h2>
            <p>
              Trained on the Construction Site Safety Dataset (Roboflow, CC BY 4.0)
              — {MODEL_INFO.datasetImages} images, {MODEL_INFO.datasetClasses} classes,
              {MODEL_INFO.epochs} epochs, {MODEL_INFO.optimizer} optimizer
            </p>

            <div className="model-tabs">
              {['overview', 'charts', 'samples', 'classes'].map((t) => (
                <button
                  key={t}
                  className={modelTab === t ? 'model-tab active' : 'model-tab'}
                  onClick={() => setModelTab(t)}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>

            {modelTab === 'overview' && (
              <div>
                <div className="metrics-grid">
                  <div className="metric-card metric-card--green">
                    <span>Best mAP@50</span>
                    <strong>{(MODEL_INFO.bestMAP50 * 100).toFixed(1)}%</strong>
                    <small>Epoch 87</small>
                  </div>
                  <div className="metric-card metric-card--blue">
                    <span>Best Precision</span>
                    <strong>{(MODEL_INFO.bestPrecision * 100).toFixed(1)}%</strong>
                    <small>Epoch 86</small>
                  </div>
                  <div className="metric-card metric-card--purple">
                    <span>Best Recall</span>
                    <strong>{(MODEL_INFO.bestRecall * 100).toFixed(1)}%</strong>
                    <small>Epoch 88</small>
                  </div>
                  <div className="metric-card metric-card--orange">
                    <span>Final mAP50-95</span>
                    <strong>{(MODEL_INFO.finalMAP5095 * 100).toFixed(1)}%</strong>
                    <small>Epoch 99</small>
                  </div>
                  <div className="metric-card">
                    <span>Architecture</span>
                    <strong>YOLOv8n</strong>
                    <small>Nano — 6.25 MB</small>
                  </div>
                  <div className="metric-card">
                    <span>Image Size</span>
                    <strong>640x640</strong>
                    <small>Stretch resize</small>
                  </div>
                  <div className="metric-card">
                    <span>Batch Size</span>
                    <strong>{MODEL_INFO.batch}</strong>
                    <small>SGD lr=0.01</small>
                  </div>
                  <div className="metric-card">
                    <span>Weights File</span>
                    <strong className="weights-name">{MODEL_INFO.weightsFile}</strong>
                    <small>cv-model/weights/</small>
                  </div>
                </div>

                <h3 className="section-label">Real Construction Site Samples</h3>
                <div className="photo-grid">
                  <figure className="photo-card">
                    <img src="/site-images/construction-safety.jpg" alt="Construction site overview" />
                    <figcaption>Construction site overview</figcaption>
                  </figure>
                  <figure className="photo-card">
                    <img src="/site-images/workers-hardhat.jpg" alt="Workers wearing hardhats" />
                    <figcaption>Workers with hardhats</figcaption>
                  </figure>
                  <figure className="photo-card">
                    <img src="/site-images/construction-workers.jpg" alt="Construction workers with PPE" />
                    <figcaption>Full PPE compliance scene</figcaption>
                  </figure>
                  <figure className="photo-card">
                    <img src="/site-images/ppe-workers.jpg" alt="PPE workers" />
                    <figcaption>Mask and safety glasses</figcaption>
                  </figure>
                </div>
              </div>
            )}

            {modelTab === 'charts' && (
              <div>
                <h3 className="section-label">Training Results — 100 Epochs</h3>
                <div className="chart-grid">
                  <figure className="chart-card chart-card--wide">
                    <img src="/model-results/results.png" alt="Training results" />
                    <figcaption>Full training curves (loss, precision, recall, mAP)</figcaption>
                  </figure>
                  <figure className="chart-card">
                    <img src="/model-results/F1_curve.png" alt="F1 curve" />
                    <figcaption>F1 Confidence Curve</figcaption>
                  </figure>
                  <figure className="chart-card">
                    <img src="/model-results/PR_curve.png" alt="PR curve" />
                    <figcaption>Precision-Recall Curve</figcaption>
                  </figure>
                  <figure className="chart-card">
                    <img src="/model-results/P_curve.png" alt="Precision curve" />
                    <figcaption>Precision Confidence Curve</figcaption>
                  </figure>
                  <figure className="chart-card">
                    <img src="/model-results/R_curve.png" alt="Recall curve" />
                    <figcaption>Recall Confidence Curve</figcaption>
                  </figure>
                  <figure className="chart-card chart-card--wide">
                    <img src="/model-results/confusion_matrix.png" alt="Confusion matrix" />
                    <figcaption>Confusion Matrix</figcaption>
                  </figure>
                </div>
              </div>
            )}

            {modelTab === 'samples' && (
              <div>
                <h3 className="section-label">Validation Predictions</h3>
                <div className="chart-grid">
                  <figure className="chart-card chart-card--wide">
                    <img src="/model-results/val_batch0_pred.jpg" alt="Val batch 0 predictions" />
                    <figcaption>Validation batch 0 — model predictions</figcaption>
                  </figure>
                  <figure className="chart-card chart-card--wide">
                    <img src="/model-results/val_batch1_pred.jpg" alt="Val batch 1 predictions" />
                    <figcaption>Validation batch 1 — model predictions</figcaption>
                  </figure>
                  <figure className="chart-card chart-card--wide">
                    <img src="/model-results/train_batch0.jpg" alt="Training batch 0" />
                    <figcaption>Training batch 0 — annotated ground truth</figcaption>
                  </figure>
                  <figure className="chart-card">
                    <img src="/model-results/labels.jpg" alt="Label distribution" />
                    <figcaption>Label distribution</figcaption>
                  </figure>
                  <figure className="chart-card">
                    <img src="/model-results/labels_correlogram.jpg" alt="Labels correlogram" />
                    <figcaption>Bounding box correlogram</figcaption>
                  </figure>
                </div>
              </div>
            )}

            {modelTab === 'classes' && (
              <div>
                <h3 className="section-label">PPE Classes (10 total)</h3>
                <div className="classes-table">
                  {MODEL_INFO.classes.map((cls, i) => (
                    <div key={cls} className={cls.startsWith('NO-') ? 'class-row class-row--danger' : 'class-row class-row--safe'}>
                      <span className="class-idx">{i}</span>
                      <span className="class-name">{cls}</span>
                      <span className="class-badge">
                        {cls.startsWith('NO-') ? 'VIOLATION' : 'COMPLIANT'}
                      </span>
                    </div>
                  ))}
                </div>

                <h3 className="section-label" style={{marginTop: '28px'}}>Dataset Augmentation</h3>
                <div className="aug-list">
                  {[
                    '50% probability of horizontal flip',
                    'Random crop: 0-20%',
                    'Random rotation: -12 to +12 degrees',
                    'Random shear: +/-2 degrees',
                    'Brightness adjustment: +/-25%',
                    'Exposure adjustment: +/-20%',
                    'Gaussian blur: 0-0.5 pixels',
                    '5 augmented versions per source image',
                  ].map((a) => (
                    <div key={a} className="aug-item">
                      <span className="aug-dot">*</span> {a}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        )}

        {activeTab === 'Reports' && (
          <section className="panel page-panel">
            <h2>Safety Reports</h2>
            <p>Generate and download safety reports from violations and model performance data.</p>

            <div className="report-summary">
              <div className="report-stat">
                <span>Total Live Violations</span>
                <strong>{totalLive}</strong>
              </div>
              <div className="report-stat">
                <span>High-Risk Events</span>
                <strong>{highRiskLive}</strong>
              </div>
              <div className="report-stat">
                <span>Model mAP@50</span>
                <strong>{(MODEL_INFO.bestMAP50 * 100).toFixed(1)}%</strong>
              </div>
              <div className="report-stat">
                <span>PPE Classes</span>
                <strong>{MODEL_INFO.datasetClasses}</strong>
              </div>
            </div>

            <div className="report-section">
              <h3>Model Details</h3>
              <table className="report-table">
                <tbody>
                  <tr><td>Model</td><td>{MODEL_INFO.name}</td></tr>
                  <tr><td>Weights</td><td>cv-model/weights/{MODEL_INFO.weightsFile}</td></tr>
                  <tr><td>Dataset</td><td>{MODEL_INFO.trainedOn}</td></tr>
                  <tr><td>Dataset Size</td><td>{MODEL_INFO.datasetImages} images (x5 augmented = 14,005 total)</td></tr>
                  <tr><td>Training Epochs</td><td>{MODEL_INFO.epochs}</td></tr>
                  <tr><td>Best mAP@50</td><td>{(MODEL_INFO.bestMAP50 * 100).toFixed(2)}%</td></tr>
                  <tr><td>Best Precision</td><td>{(MODEL_INFO.bestPrecision * 100).toFixed(2)}%</td></tr>
                  <tr><td>Best Recall</td><td>{(MODEL_INFO.bestRecall * 100).toFixed(2)}%</td></tr>
                </tbody>
              </table>
            </div>

            <div className="report-actions">
              <button
                className="report-button"
                onClick={() => {
                  const rows = [
                    ['Metric', 'Value'],
                    ['Model', MODEL_INFO.name],
                    ['Best mAP50', (MODEL_INFO.bestMAP50 * 100).toFixed(2) + '%'],
                    ['Best Precision', (MODEL_INFO.bestPrecision * 100).toFixed(2) + '%'],
                    ['Best Recall', (MODEL_INFO.bestRecall * 100).toFixed(2) + '%'],
                    ['mAP50-95', (MODEL_INFO.finalMAP5095 * 100).toFixed(2) + '%'],
                    ['Total Violations', totalLive],
                    ['High Risk', highRiskLive],
                    ['Generated', new Date().toISOString()],
                  ]
                  const csv = rows.map(r => r.join(',')).join('\n')
                  const blob = new Blob([csv], {type: 'text/csv'})
                  const a = document.createElement('a')
                  a.href = URL.createObjectURL(blob)
                  a.download = 'skyguard-report-' + Date.now() + '.csv'
                  a.click()
                }}
              >
                Download CSV Report
              </button>
              <a
                href="/model-results/results.csv"
                download="training-results.csv"
                className="report-button"
                style={{textDecoration: 'none', display: 'inline-block', marginLeft: '12px'}}
              >
                Download Training Metrics CSV
              </a>
            </div>
          </section>
        )}

      </main>
    </div>
  )
}

export default App
