import { useState } from 'react'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('Dashboard')

  const violations = [
    {
      type: 'No PPE Detected',
      location: 'Zone A',
      time: '10:42 AM',
      severity: 'High',
    },
    {
      type: 'Restricted Zone Entry',
      location: 'Zone B',
      time: '10:38 AM',
      severity: 'Medium',
    },
    {
      type: 'Unsafe Proximity',
      location: 'Zone C',
      time: '10:31 AM',
      severity: 'High',
    },
  ]

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
            className={activeTab === 'Dashboard' ? 'nav-item active' : 'nav-item'}
            onClick={() => setActiveTab('Dashboard')}
          >
            <span>▣</span>
            Dashboard
          </button>

          <button
            className={activeTab === 'Violations' ? 'nav-item active' : 'nav-item'}
            onClick={() => setActiveTab('Violations')}
          >
            <span>⚠</span>
            Violations
          </button>

          <button
            className={activeTab === 'Reports' ? 'nav-item active' : 'nav-item'}
            onClick={() => setActiveTab('Reports')}
          >
            <span>▤</span>
            Reports
          </button>
        </nav>

        <div className="system-status">
          <div className="status-dot"></div>
          <div>
            <strong>System Online</strong>
            <small>All systems operational</small>
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

        {/* Dashboard */}
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
                  <strong className="online">ONLINE</strong>
                </div>
              </div>

            </section>

            {/* Map + Risk */}
            <section className="middle-grid">

              <div className="panel map-panel">
                <div className="panel-header">
                  <div>
                    <h2>Live Monitoring Map</h2>
                    <p>Real-time drone position</p>
                  </div>
                  <span className="badge">LIVE</span>
                </div>

                <div className="map">
                  <div className="map-grid"></div>

                  <div className="map-zone zone-a">ZONE A</div>
                  <div className="map-zone zone-b">ZONE B</div>
                  <div className="map-zone zone-c">ZONE C</div>

                  <div className="drone">
                    🚁
                  </div>

                  <div className="map-label">
                    Drone Position
                  </div>
                </div>
              </div>

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
                  Several safety violations have been detected.
                  Immediate attention is recommended.
                </p>
              </div>

            </section>

            {/* Violation Feed */}
            <section className="panel violations-panel">

              <div className="panel-header">
                <div>
                  <h2>Recent Violations</h2>
                  <p>Latest AI-detected safety incidents</p>
                </div>

                <button className="view-button">
                  View All
                </button>
              </div>

              <div className="violation-list">

                {violations.map((violation, index) => (
                  <div className="violation-row" key={index}>

                    <div className="violation-icon">⚠</div>

                    <div className="violation-info">
                      <strong>{violation.type}</strong>
                      <span>
                        {violation.location} • {violation.time}
                      </span>
                    </div>

                    <span
                      className={
                        violation.severity === 'High'
                          ? 'severity high'
                          : 'severity medium'
                      }
                    >
                      {violation.severity}
                    </span>

                  </div>
                ))}

              </div>
            </section>

          </>
        )}

        {/* Violations page */}
        {activeTab === 'Violations' && (
          <section className="panel page-panel">
            <h2>Violation Management</h2>
            <p>
              All detected safety violations will appear here.
            </p>

            <div className="empty-message">
              Violation records will be connected to the FastAPI backend next.
            </div>
          </section>
        )}

        {/* Reports page */}
        {activeTab === 'Reports' && (
          <section className="panel page-panel">
            <h2>Safety Reports</h2>
            <p>
              Generate and download safety reports from recorded violations.
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