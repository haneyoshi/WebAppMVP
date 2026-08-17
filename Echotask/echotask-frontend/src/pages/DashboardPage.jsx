import { useCallback, useEffect, useState } from 'react'
import { getWorkerAvailability } from '../api/availability'

const dashboardSections = [
  { title: "Today's Operations", message: 'More operational detail will be added in a future milestone.' },
  { title: 'Area Coverage', message: 'Interactive area coverage is not connected yet.' },
  { title: "Today's Events", message: 'Event reminders are not connected yet.' },
]

function localDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function statusClassName(status) {
  if (status === 'Away') return 'status-badge status-badge--away'
  if (status === 'Assigned elsewhere') return 'status-badge status-badge--assigned'
  return 'status-badge'
}

function DashboardPage({ user }) {
  const today = new Date()
  const todayKey = localDateKey(today)
  const canViewAvailability = user.role === 'coordinator' || user.role === 'supervisor'
  const [workers, setWorkers] = useState([])
  const [isLoading, setIsLoading] = useState(canViewAvailability)
  const [error, setError] = useState('')

  const loadAvailability = useCallback(async () => {
    if (!canViewAvailability) return
    setIsLoading(true)
    setError('')
    try {
      setWorkers(await getWorkerAvailability({ date: todayKey }))
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setIsLoading(false)
    }
  }, [canViewAvailability, todayKey])

  useEffect(() => {
    loadAvailability()
  }, [loadAvailability])

  return (
    <section aria-labelledby="dashboard-title">
      <div className="page-heading">
        <p className="eyebrow">Daily overview</p>
        <h2 id="dashboard-title">Dashboard</h2>
        <p className="muted-text">A shared operational view of attendance, availability, and area coverage.</p>
      </div>
      <div className="dashboard-grid">
        {canViewAvailability && (
          <article className="dashboard-card dashboard-card--availability">
            <div className="availability-heading">
              <div>
                <p className="eyebrow">Today</p>
                <h3>Worker Availability</h3>
              </div>
              {!isLoading && !error && <strong>{workers.length} workers</strong>}
            </div>
            {isLoading && <p className="muted-text" aria-live="polite">Loading worker availability&hellip;</p>}
            {error && (
              <div className="attendance-error" role="alert">
                <p className="form-error">{error}</p>
                <button type="button" className="secondary-button" onClick={loadAvailability}>Try again</button>
              </div>
            )}
            {!isLoading && !error && workers.length === 0 && (
              <p className="empty-state">No active workers are available to show.</p>
            )}
            {!isLoading && !error && workers.length > 0 && (
              <ul className="availability-list">
                {workers.map((worker) => (
                  <li key={worker.user_id}>
                    <div className="availability-worker">
                      <strong>{worker.name}</strong>
                      <span>{worker.regular_area_name || 'No regular area'}</span>
                    </div>
                    <div className="availability-state">
                      <span className={statusClassName(worker.status)}>{worker.status}</span>
                      {worker.status === 'Assigned elsewhere' && worker.assignments.length > 0 && (
                        <span className="assignment-destination">
                          {worker.assignments.map((assignment) => assignment.location_task).join(', ')}
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </article>
        )}
        {dashboardSections.map((section) => (
          <article className="dashboard-card" key={section.title}>
            <h3>{section.title}</h3>
            <p className="empty-state">{section.message}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

export default DashboardPage
