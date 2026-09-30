import { useEffect, useState } from 'react'
import axios from 'axios'
import './App.css'
import MapView from './MapView'

function App() {
  const [activeTab, setActiveTab] = useState('Dashboard')
  const [violations, setViolations] = useState([])
  const [apiError, setApiError] = useState('')
  const [wsStatus, setWsStatus] = useState('Connecting')

  useEffect(() => {
    // Load existing violations from the backend
    axios
      .get('http://127.0.0.1:8000/violations')
      .then((response) => {
        setViolations(response.data)
        setApiError('')
      })
      .catch((error) => {
        console.error('Error fetching violations:', error)
        setApiError('Unable to connect to the backend server.')
      })

    // Connect to the live WebSocket
    const socket = new WebSocket(
      'ws://127.0.0.1:8000/ws/violations'
    )

    socket.onopen = () => {
      console.log('WebSocket connected')
      setWsStatus('Connected')
    }

    socket.onmessage = (event) => {
      const newViolation = JSON.parse(event.data)

      console.log('New live violation:', newViolation)

      setViolations((currentViolations) => [
        ...currentViolations,
        newViolation
      ])
    }

    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setWsStatus('Disconnected')
    }

    socket.onclose = () => {
      console.log('WebSocket disconnected')
      setWsStatus('Disconnected')
    }

    // Close WebSocket when component is removed
    return () => {
      socket.close()
    }
  }, [])

  return (
    <div className="dashboard">

      {/* Sidebar */}
      <aside className="sidebar">

        <div className="logo">
          <div className="logo-icon">S</div>

          <div>
            <h2>SKYGUARD</h2>
            <span>AI SAFETY SYSTEM</span>
          </div>
        </div>

        <nav>

          <button
            className={
              activeTab === 'Dashboard'
                ? 'nav-item active'
                : 'nav-item'
            }
            onClick={() => setActiveTab('Dashboard')}
          >
            <span>▣</span>
            Dashboard
          </button>

          <button
            className={
              activeTab === 'Violations'
                ? 'nav-item active'
                : 'nav-item'
            }
            onClick={() => setActiveTab('Violations')}
          >
            <span>⚠</span>
            Violations
          </button>

          <button
            className={
              activeTab === 'Reports'
                ? 'nav-item active'
                : 'nav-item'
            }
            onClick={() => setActiveTab('Reports')}
          >
            <span>▤</span>
            Reports
          </button>

        </nav>

        {/* System status */}
        <div className="system-status">

          <div className="status-dot"></div>

          <div>
            <strong>
              {wsStatus === 'Connected'
                ? 'System Online'
                : 'System Warning'}
            </strong>

            <small>
              {wsStatus === 'Connected'
                ? 'All systems operational'
                : 'Live connection unavailable'}
            </small>
          </div>

        </div>

      </aside>

      {/* Main content */}
      <main className="main-content">

        {/* Header */}
        <header className="topbar">

          <div>
            <h1>{activeTab}</h1>
            <p>AI-powered workplace safety monitoring</p>
          </div>

          <div className="top-status">
            <span className="live-dot"></span>
            LIVE MONITORING
          </div>

        </header>

        {/* Connection status messages */}

        {apiError && (
          <div className="error-message">
            ⚠️ {apiError}
          </div>
        )}

        {wsStatus === 'Disconnected' && (
          <div className="error-message">
            ⚠️ Live violation feed disconnected.
          </div>
        )}

        {/* ===================================================== */}
        {/* DASHBOARD */}
        {/* ===================================================== */}

        {activeTab === 'Dashboard' && (
          <>

            {/* Statistics */}
            <section className="stats-grid">

              <div className="stat-card">
                <div className="stat-icon">⚠</div>

                <div>
                  <span>Total Violations</span>
                  <strong>24</strong>
                </div>
              </div>


              <div className="stat-card">
                <div className="stat-icon">✓</div>

                <div>
                  <span>Resolved</span>
                  <strong>17</strong>
                </div>
              </div>


              <div className="stat-card">
                <div className="stat-icon">!</div>

                <div>
                  <span>High Risk</span>
                  <strong>5</strong>
                </div>
              </div>


              <div className="stat-card">
                <div className="stat-icon">●</div>

                <div>
                  <span>Drone Status</span>
                  <strong className="online">
                    ONLINE
                  </strong>
                </div>
              </div>

            </section>


            {/* ================================================= */}
            {/* MAP + RISK */}
            {/* ================================================= */}

            <section className="middle-grid">

              {/* Live Monitoring Map */}
              <div className="panel map-panel">

                <div className="panel-header">

                  <div>
                    <h2>Live Monitoring Map</h2>
                    <p>Real-time drone position</p>
                  </div>

                  <span className="badge">
                    LIVE
                  </span>

                </div>

                {/* Real Leaflet map */}
                <MapView />

              </div>


              {/* Risk Score */}
              <div className="panel risk-panel">

                <div className="panel-header">

                  <div>
                    <h2>Risk Score</h2>
                    <p>Current site safety level</p>
                  </div>

                </div>


                <div className="risk-circle">

                  <div>
                    <strong>62</strong>
                    <span>/ 100</span>
                  </div>

                </div>


                <div className="risk-level">
                  <span></span>
                  Medium Risk
                </div>


                <p className="risk-description">
                  Several safety violations have been
                  detected. Immediate attention is
                  recommended.
                </p>

              </div>

            </section>


            {/* ================================================= */}
            {/* VIOLATION FEED */}
            {/* ================================================= */}

            <section className="panel violations-panel">

              <div className="panel-header">

                <div>
                  <h2>Recent Violations</h2>
                  <p>
                    Latest AI-detected safety incidents
                  </p>
                </div>

                <button className="view-button">
                  View All
                </button>

              </div>


              <div className="violation-list">

                {violations.length === 0 ? (

                  <div className="empty-message">
                    No violations recorded yet.
                  </div>

                ) : (

                  violations.map((violation, index) => (

                    <div
                      className="violation-row"
                      key={violation.id ?? index}
                    >

                      <div className="violation-icon">
                        ⚠
                      </div>


                      <div className="violation-info">

                        <strong>
                          {violation.type}
                        </strong>

                        <span>
                          Lat:{' '}
                          {Number(violation.latitude).toFixed(4)}
                          {' • '}
                          Lon:{' '}
                          {Number(violation.longitude).toFixed(4)}
                          {' • '}
                          {new Date(
                            violation.timestamp
                          ).toLocaleTimeString()}
                        </span>

                      </div>


                      <span
                        className={
                          violation.confidence >= 0.8
                            ? 'severity high'
                            : 'severity medium'
                        }
                      >
                        {violation.confidence >= 0.8
                          ? 'High'
                          : 'Medium'}
                      </span>

                    </div>

                  ))

                )}

              </div>

            </section>

          </>
        )}


        {/* ===================================================== */}
        {/* VIOLATIONS PAGE */}
        {/* ===================================================== */}

        {activeTab === 'Violations' && (

          <section className="panel page-panel">

            <h2>Violation Management</h2>

            <p>
              All detected safety violations from the
              SkyGuard AI system.
            </p>


            {violations.length === 0 ? (

              <div className="empty-message">
                No violations recorded yet.
              </div>

            ) : (

              <div className="violation-list">

                {violations.map((violation) => (

                  <div
                    className="violation-row"
                    key={violation.id}
                  >

                    <div className="violation-icon">
                      ⚠
                    </div>


                    <div className="violation-info">

                      <strong>
                        {violation.type}
                      </strong>


                      <span>
                        Confidence:{' '}
                        {(
                          violation.confidence * 100
                        ).toFixed(0)}
                        %
                        {' • '}
                        Location:{' '}
                        {violation.latitude},{' '}
                        {violation.longitude}
                      </span>


                      <span>
                        {new Date(
                          violation.timestamp
                        ).toLocaleString()}
                      </span>

                    </div>


                    <span className="severity high">
                      DETECTED
                    </span>

                  </div>

                ))}

              </div>

            )}

          </section>

        )}


        {/* ===================================================== */}
        {/* REPORTS PAGE */}
        {/* ===================================================== */}

        {activeTab === 'Reports' && (

          <section className="panel page-panel">

            <h2>Safety Reports</h2>

            <p>
              Generate and download safety reports
              from recorded violations.
            </p>


            <button className="report-button">
              Generate Report
            </button>

          </section>

        )}

      </main>

    </div>
  )
}

export default App