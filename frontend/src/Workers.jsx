import { useMemo } from 'react'

function Workers({ violations }) {

  const workers = useMemo(() => {

    const workerMap = {}

    violations.forEach((violation) => {

      const personId = violation.person_id

      // Ignore old records that don't have a worker ID
      if (!personId || personId === 'UNKNOWN') {
        return
      }

      if (!workerMap[personId]) {
        workerMap[personId] = {
          person_id: personId,
          violations: [],
        }
      }

      workerMap[personId].violations.push(violation)
    })

    return Object.values(workerMap)

  }, [violations])


  const generateReport = (personId) => {

    const reportUrl =
      `http://127.0.0.1:8000/persons/${personId}/report`

    window.open(reportUrl, '_blank')
  }


  return (

    <section className="panel page-panel">

      <div className="panel-header">

        <div>
          <h2>Worker Safety Records</h2>

          <p>
            Individual worker safety monitoring and reports
          </p>
        </div>

      </div>


      {workers.length === 0 ? (

        <div className="empty-message">

          No identified workers found yet.

          <br />

          Worker records will appear when the AI
          system sends a Person ID with a violation.

        </div>

      ) : (

        <div
          style={{
            display: 'grid',
            gridTemplateColumns:
              'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '20px',
            marginTop: '20px',
          }}
        >

          {workers.map((worker) => {

            const workerViolations =
              worker.violations

            const highRiskCount =
              workerViolations.filter(
                (violation) =>
                  Number(violation.confidence) >= 0.8
              ).length

            const latestViolation =
              [...workerViolations].sort(
                (a, b) =>
                  new Date(b.timestamp) -
                  new Date(a.timestamp)
              )[0]


            return (

              <div
                key={worker.person_id}
                style={{
                  border: '1px solid #e2e8f0',
                  borderRadius: '12px',
                  padding: '20px',
                  background: '#ffffff',
                  boxShadow:
                    '0 4px 12px rgba(0,0,0,0.06)',
                }}
              >

                {/* Worker header */}

                <div
                  style={{
                    display: 'flex',
                    justifyContent:
                      'space-between',
                    alignItems: 'center',
                    marginBottom: '16px',
                  }}
                >

                  <div>

                    <span
                      style={{
                        fontSize: '12px',
                        color: '#64748b',
                      }}
                    >
                      PERSON ID
                    </span>

                    <h3
  style={{
    margin: '4px 0 0',
    fontSize: '24px',
    color: '#1f2937',
    fontWeight: '700',
  }}
>
  {worker.person_id}
</h3>
                  </div>


                  <span
                    style={{
                      padding: '6px 10px',
                      borderRadius: '20px',
                      fontSize: '11px',
                      fontWeight: '600',
                      background:
                        highRiskCount > 0
                          ? '#fee2e2'
                          : '#fef3c7',
                      color:
                        highRiskCount > 0
                          ? '#b91c1c'
                          : '#92400e',
                    }}
                  >
                    {highRiskCount > 0
                      ? 'HIGH RISK'
                      : 'MONITOR'}
                  </span>

                </div>


                {/* Statistics */}

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns:
                      '1fr 1fr',
                    gap: '12px',
                    marginBottom: '16px',
                  }}
                >

                  <div
                    style={{
                      background: '#f8fafc',
                      padding: '12px',
                      borderRadius: '8px',
                    }}
                  >

                    <span
                      style={{
                        display: 'block',
                        fontSize: '12px',
                        color: '#64748b',
                      }}
                    >
                      Violations
                    </span>

                   <strong
  style={{
    fontSize: '22px',
    color: '#1f2937',
  }}
>
                      {workerViolations.length}
                    </strong>

                  </div>


                  <div
                    style={{
                      background: '#f8fafc',
                      padding: '12px',
                      borderRadius: '8px',
                    }}
                  >

                    <span
                      style={{
                        display: 'block',
                        fontSize: '12px',
                        color: '#64748b',
                      }}
                    >
                      High Risk
                    </span>

                   <strong
  style={{
    fontSize: '22px',
    color: '#1f2937',
  }}
>
                      {highRiskCount}
                    </strong>

                  </div>

                </div>


                {/* Latest violation */}

                {latestViolation && (

                  <div
                    style={{
                      marginBottom: '16px',
                    }}
                  >

                    <span
                      style={{
                        fontSize: '12px',
                        color: '#64748b',
                      }}
                    >
                      Latest Violation
                    </span>

                    <strong
  style={{
    display: 'block',
    marginTop: '4px',
    color: '#1f2937',
  }}
>
                    
                      {latestViolation.type
                        .replaceAll('-', ' ')
                        .replace(
                          /\b\w/g,
                          (letter) =>
                            letter.toUpperCase()
                        )}
                    </strong>

                    <small
                      style={{
                        color: '#64748b',
                      }}
                    >
                      {new Date(
                        latestViolation.timestamp
                      ).toLocaleString()}
                    </small>

                  </div>

                )}


                {/* Report button */}

                <button
                  onClick={() =>
                    generateReport(
                      worker.person_id
                    )
                  }
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600',
                    background: '#1f2937',
                    color: '#ffffff',
                  }}
                >
                  📄 Generate Safety Report
                </button>

              </div>

            )

          })}

        </div>

      )}

    </section>

  )
}

export default Workers