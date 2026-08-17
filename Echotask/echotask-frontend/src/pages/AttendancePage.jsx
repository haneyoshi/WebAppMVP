import { useCallback, useEffect, useState } from 'react'
import { checkIn, getAttendance } from '../api/attendance'

function localDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatTime(value) {
  if (!value) return 'Time unavailable'
  const date = new Date(value.endsWith('Z') ? value : `${value}Z`)
  if (Number.isNaN(date.getTime())) return 'Time unavailable'
  return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

function AttendancePage({ user }) {
  const today = new Date()
  const todayKey = localDateKey(today)
  const [records, setRecords] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isCheckingIn, setIsCheckingIn] = useState(false)
  const [error, setError] = useState('')

  const loadAttendance = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try {
      setRecords(await getAttendance({ date: todayKey }))
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setIsLoading(false)
    }
  }, [todayKey])

  useEffect(() => {
    loadAttendance()
  }, [loadAttendance])

  async function handleCheckIn() {
    setIsCheckingIn(true)
    setError('')
    try {
      const record = await checkIn()
      setRecords([record])
    } catch (requestError) {
      if (requestError.status === 409) {
        await loadAttendance()
      } else {
        setError(requestError.message)
      }
    } finally {
      setIsCheckingIn(false)
    }
  }

  const dateLabel = today.toLocaleDateString([], {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })

  if (user.role === 'worker') {
    const record = records[0]
    return (
      <section className="attendance-page">
        <div className="page-heading">
          <p className="eyebrow">Today</p>
          <h2>Attendance</h2>
          <p className="muted-text">{dateLabel}</p>
        </div>

        <div className="attendance-status-card" aria-live="polite">
          {isLoading ? (
            <p className="muted-text">Loading today&apos;s attendance…</p>
          ) : error ? (
            <>
              <p className="form-error" role="alert">{error}</p>
              <button type="button" className="secondary-button" onClick={loadAttendance}>Try again</button>
            </>
          ) : record ? (
            <>
              <span className="status-badge">{record.status}</span>
              <h3>You&apos;re checked in</h3>
              <p className="muted-text">Recorded at {formatTime(record.marked_at)}.</p>
            </>
          ) : (
            <>
              <span className="status-badge status-badge--pending">Not checked in</span>
              <h3>Ready to start your day?</h3>
              <p className="muted-text">Check in once for today. Your status will be saved securely.</p>
              <button type="button" onClick={handleCheckIn} disabled={isCheckingIn}>
                {isCheckingIn ? 'Checking in…' : 'Check In'}
              </button>
            </>
          )}
        </div>
      </section>
    )
  }

  return (
    <section className="attendance-page">
      <div className="page-heading">
        <p className="eyebrow">Today</p>
        <h2>Attendance</h2>
        <p className="muted-text">{dateLabel}</p>
      </div>

      <div className="attendance-summary">
        <div>
          <h3>Today&apos;s recorded attendance</h3>
          <p className="muted-text">Read-only summary. Attendance management is coming next.</p>
        </div>
        {!isLoading && !error && <strong>{records.length} recorded</strong>}
      </div>
      {isLoading && <p className="muted-text">Loading today&apos;s attendance…</p>}
      {error && (
        <div className="attendance-error" role="alert">
          <p className="form-error">{error}</p>
          <button type="button" className="secondary-button" onClick={loadAttendance}>Try again</button>
        </div>
      )}
      {!isLoading && !error && records.length === 0 && (
        <p className="empty-state">No attendance has been recorded today.</p>
      )}
      {!isLoading && !error && records.length > 0 && (
        <ul className="attendance-list">
          {records.map((record) => (
            <li key={record.attendance_record_id}>
              <div><strong>{record.user_name}</strong><span>{formatTime(record.marked_at)}</span></div>
              <span className="status-badge">{record.status}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default AttendancePage
