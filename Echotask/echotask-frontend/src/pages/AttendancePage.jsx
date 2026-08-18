import { useCallback, useEffect, useState } from 'react'
import { checkIn, createAttendance, getAttendance, updateAttendance } from '../api/attendance'
import { getWorkerAvailability } from '../api/availability'

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

function statusClassName(status) {
  if (status === 'Away') return 'status-badge status-badge--away'
  if (status === 'Assigned elsewhere') return 'status-badge status-badge--assigned'
  if (status === 'Not recorded' || status === 'Loading attendance' || status === 'Attendance unavailable') {
    return 'status-badge status-badge--pending'
  }
  return 'status-badge'
}

function assignmentLabel(assignment) {
  if (assignment.destination_area_id !== null) {
    return `${assignment.destination_building_name} — ${assignment.destination_area_name}`
  }
  return assignment.location_task
}

function TeamAvailability(props) {
  const {
    workers, isLoading, error, onRetry, canManageAttendance,
    recordsByUserId, isAttendanceLoading, attendanceError, onAttendanceRetry,
    isAttendanceManagementMode, enterAttendanceManagement, leaveAttendanceManagement,
    editingUserId, editStatus, setEditStatus, absenceReason, setAbsenceReason,
    isSaving, saveError, startEditing, cancelEditing, handleAttendanceSave,
  } = props

  return (
    <section className={`team-availability${isAttendanceManagementMode ? ' team-availability--managing' : ''}`} aria-labelledby="team-availability-title">
      <div className="team-availability-heading">
        <div>
          <p className="eyebrow">Shared operations</p>
          <h3 id="team-availability-title">Team Availability</h3>
          <p className="muted-text">Current operational status for active workers.</p>
        </div>
        <div className="team-availability-heading-actions">
          {!isLoading && !error && <strong>{workers.length} workers</strong>}
          {canManageAttendance && (
            <button
              type="button"
              className="secondary-button"
              onClick={isAttendanceManagementMode ? leaveAttendanceManagement : enterAttendanceManagement}
              disabled={isAttendanceManagementMode && isSaving}
            >
              {isAttendanceManagementMode ? 'Done' : 'Manage attendance'}
            </button>
          )}
        </div>
      </div>
      {isLoading && <p className="muted-text" aria-live="polite">Loading team availability&hellip;</p>}
      {error && (
        <div className="attendance-error" role="alert">
          <p className="form-error">{error}</p>
          <button type="button" className="secondary-button" onClick={onRetry}>Try again</button>
        </div>
      )}
      {!isLoading && !error && workers.length === 0 && (
        <p className="empty-state">No active workers are available to show.</p>
      )}
      {!isLoading && !error && canManageAttendance && attendanceError && (
        <div className="attendance-error" role="alert">
          <p className="form-error">Official attendance is unavailable. {attendanceError}</p>
          <button type="button" className="secondary-button" onClick={onAttendanceRetry}>Try again</button>
        </div>
      )}
      {!isLoading && !error && workers.length > 0 && (
        <ul className="team-availability-list">
          {workers.map((worker) => {
            const record = recordsByUserId?.get(worker.user_id)
            const officialStatus = isAttendanceLoading
              ? 'Loading attendance'
              : attendanceError ? 'Attendance unavailable' : record?.status || 'Not recorded'
            const isEditing = editingUserId === worker.user_id

            return (
              <li key={worker.user_id}>
                <details className="team-availability-worker">
                  <summary>
                    <strong>{worker.name}</strong>
                    <span className="team-availability-statuses">
                      <span className="team-availability-status">
                        <span>Availability</span>
                        <span className={statusClassName(worker.status)}>{worker.status}</span>
                      </span>
                      {canManageAttendance && (
                        <span className="team-availability-status team-availability-status--official">
                          <span>Official attendance</span>
                          <span className={statusClassName(officialStatus)}>{officialStatus}</span>
                        </span>
                      )}
                    </span>
                  </summary>
                  <div className="team-availability-details">
                    <p><span>Regular area</span><strong>{worker.regular_area_name || 'No regular area'}</strong></p>
                    <div>
                      <span>Current assignments</span>
                      {worker.assignments.length > 0 ? (
                        <ul>
                          {worker.assignments.map((assignment) => (
                            <li key={assignment.assignment_id}>{assignmentLabel(assignment)}</li>
                          ))}
                        </ul>
                      ) : <strong>None</strong>}
                    </div>
                    {canManageAttendance && isAttendanceManagementMode && !isAttendanceLoading && !attendanceError && (
                      <div className="attendance-management-controls">
                        <div className="attendance-management-control-heading">
                          <div>
                            <span>Official attendance</span>
                            <strong>{record?.status || 'Not recorded'}</strong>
                          </div>
                          {!isEditing && (
                            <button type="button" className="secondary-button attendance-edit-button" onClick={() => startEditing(worker, record)} disabled={isSaving}>
                              {record ? 'Edit' : 'Mark attendance'}
                            </button>
                          )}
                        </div>
                        {record?.status === 'Away' && record.absence_reason && !isEditing && (
                          <p className="attendance-private-reason"><span>Private absence reason</span>{record.absence_reason}</p>
                        )}
                        {isEditing && (
                          <div className="attendance-inline-editor">
                            <label htmlFor={`attendance-status-${worker.user_id}`}>Official attendance
                              <select id={`attendance-status-${worker.user_id}`} value={editStatus} onChange={(event) => setEditStatus(event.target.value)} disabled={isSaving}><option value="Working">Working</option><option value="Away">Away</option></select>
                            </label>
                            {editStatus === 'Away' && <label htmlFor={`absence-reason-${worker.user_id}`}>Private absence reason <span className="muted-text">(optional)</span><input id={`absence-reason-${worker.user_id}`} type="text" value={absenceReason} onChange={(event) => setAbsenceReason(event.target.value)} disabled={isSaving} /></label>}
                            {saveError && <p className="form-error" role="alert">{saveError}</p>}
                            <div className="attendance-editor-actions">
                              <button type="button" onClick={() => handleAttendanceSave(worker, record)} disabled={isSaving}>{isSaving ? 'Saving...' : 'Save'}</button>
                              <button type="button" className="secondary-button" onClick={cancelEditing} disabled={isSaving}>Cancel</button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </details>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}

function AttendancePage({ user }) {
  const today = new Date()
  const todayKey = localDateKey(today)
  const [records, setRecords] = useState([])
  const [workers, setWorkers] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isTeamLoading, setIsTeamLoading] = useState(true)
  const [isCheckingIn, setIsCheckingIn] = useState(false)
  const [error, setError] = useState('')
  const [teamError, setTeamError] = useState('')
  const [editingUserId, setEditingUserId] = useState(null)
  const [editStatus, setEditStatus] = useState('Working')
  const [absenceReason, setAbsenceReason] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [isAttendanceManagementMode, setIsAttendanceManagementMode] = useState(false)

  const loadAttendance = useCallback(async () => {
    setIsLoading(true)
    setError('')
    try { setRecords(await getAttendance({ date: todayKey })) }
    catch (requestError) { setError(requestError.message) }
    finally { setIsLoading(false) }
  }, [todayKey])

  const loadTeamAvailability = useCallback(async () => {
    setIsTeamLoading(true)
    setTeamError('')
    try { setWorkers(await getWorkerAvailability({ date: todayKey })) }
    catch (requestError) { setTeamError(requestError.message) }
    finally { setIsTeamLoading(false) }
  }, [todayKey])

  useEffect(() => {
    loadAttendance()
    loadTeamAvailability()
  }, [loadAttendance, loadTeamAvailability])

  async function handleCheckIn() {
    setIsCheckingIn(true)
    setError('')
    try { setRecords([await checkIn()]) }
    catch (requestError) {
      if (requestError.status === 409) await loadAttendance()
      else setError(requestError.message)
    } finally { setIsCheckingIn(false) }
  }

  function startEditing(worker, record) {
    setEditingUserId(worker.user_id)
    setEditStatus(record?.status === 'Away' ? 'Away' : 'Working')
    setAbsenceReason(record?.status === 'Away' ? record.absence_reason || '' : '')
    setSaveError('')
  }

  function cancelEditing() {
    setEditingUserId(null)
    setEditStatus('Working')
    setAbsenceReason('')
    setSaveError('')
  }

  function leaveAttendanceManagement() {
    cancelEditing()
    setIsAttendanceManagementMode(false)
  }

  async function handleAttendanceSave(worker, record) {
    setIsSaving(true)
    setSaveError('')
    const values = {
      status: editStatus,
      absence_reason: editStatus === 'Away' ? absenceReason.trim() || null : null,
    }
    try {
      if (record) await updateAttendance(record.attendance_record_id, values)
      else await createAttendance({ user_id: worker.user_id, attendance_date: todayKey, ...values })
      cancelEditing()
      await Promise.all([loadAttendance(), loadTeamAvailability()])
    } catch (requestError) {
      if (!record && requestError.status === 409) {
        cancelEditing()
        await Promise.all([loadAttendance(), loadTeamAvailability()])
      } else setSaveError(requestError.message)
    } finally { setIsSaving(false) }
  }

  const dateLabel = today.toLocaleDateString([], {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
  const recordsByUserId = new Map(records.map((record) => [record.user_id, record]))
  const workerRecord = records[0]
  const canManageAttendance = user.role === 'coordinator' || user.role === 'supervisor'

  return (
    <section className="attendance-page">
      <div className="page-heading">
        <p className="eyebrow">Today</p><h2>Attendance</h2><p className="muted-text">{dateLabel}</p>
      </div>

      {user.role === 'worker' ? (
        <div className="attendance-status-card" aria-live="polite">
          {isLoading ? <p className="muted-text">Loading today&apos;s attendance&hellip;</p> : error ? (
            <><p className="form-error" role="alert">{error}</p><button type="button" className="secondary-button" onClick={loadAttendance}>Try again</button></>
          ) : workerRecord ? (
            <>
              <span className={statusClassName(workerRecord.status)}>{workerRecord.status}</span>
              <h3>{workerRecord.status === 'Working' ? 'You\'re checked in' : workerRecord.status === 'Away' ? 'You\'re marked away today' : 'Your attendance is recorded'}</h3>
              <p className="muted-text">Recorded at {formatTime(workerRecord.marked_at)}.</p>
            </>
          ) : (
            <>
              <span className="status-badge status-badge--pending">Not checked in</span>
              <h3>Ready to start your day?</h3>
              <p className="muted-text">Check in once for today. Your status will be saved securely.</p>
              <button type="button" onClick={handleCheckIn} disabled={isCheckingIn}>{isCheckingIn ? 'Checking in...' : 'Check In'}</button>
            </>
          )}
        </div>
      ) : null}

      <TeamAvailability
        workers={workers}
        isLoading={isTeamLoading}
        error={teamError}
        onRetry={loadTeamAvailability}
        canManageAttendance={canManageAttendance}
        recordsByUserId={canManageAttendance ? recordsByUserId : undefined}
        isAttendanceLoading={canManageAttendance && isLoading}
        attendanceError={canManageAttendance ? error : ''}
        onAttendanceRetry={loadAttendance}
        isAttendanceManagementMode={isAttendanceManagementMode}
        enterAttendanceManagement={() => setIsAttendanceManagementMode(true)}
        leaveAttendanceManagement={leaveAttendanceManagement}
        editingUserId={editingUserId}
        editStatus={editStatus}
        setEditStatus={setEditStatus}
        absenceReason={absenceReason}
        setAbsenceReason={setAbsenceReason}
        isSaving={isSaving}
        saveError={saveError}
        startEditing={startEditing}
        cancelEditing={cancelEditing}
        handleAttendanceSave={handleAttendanceSave}
      />
    </section>
  )
}

export default AttendancePage
