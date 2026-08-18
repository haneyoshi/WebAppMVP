import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  createAssignment,
  deleteAssignment,
  getAssignments,
  updateAssignment,
} from '../api/assignments'
import { getWorkerAvailability } from '../api/availability'
import { getAreas } from '../api/locations'

function localDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function AssignmentsPage() {
  const today = new Date()
  const todayKey = localDateKey(today)
  const [assignments, setAssignments] = useState([])
  const [workers, setWorkers] = useState([])
  const [areas, setAreas] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [editingAssignmentId, setEditingAssignmentId] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [destinationAreaId, setDestinationAreaId] = useState('')
  const [workerIds, setWorkerIds] = useState([])
  const [note, setNote] = useState('')
  const [saveError, setSaveError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [removingAssignmentId, setRemovingAssignmentId] = useState(null)

  const loadData = useCallback(async () => {
    setIsLoading(true)
    setLoadError('')
    try {
      const [todayAssignments, activeWorkers, availableAreas] = await Promise.all([
        getAssignments({ date: todayKey }),
        getWorkerAvailability({ date: todayKey }),
        getAreas(),
      ])
      setAssignments(todayAssignments)
      setWorkers(activeWorkers)
      setAreas(availableAreas)
    } catch (requestError) {
      setLoadError(requestError.message)
    } finally {
      setIsLoading(false)
    }
  }, [todayKey])

  useEffect(() => {
    loadData()
  }, [loadData])

  const assignedElsewhereIds = useMemo(() => {
    const assignedIds = new Set()
    assignments.forEach((assignment) => {
      if (assignment.assignment_id === editingAssignmentId) return
      assignment.worker_ids.forEach((workerId) => assignedIds.add(workerId))
    })
    return assignedIds
  }, [assignments, editingAssignmentId])

  const selectedAreaId = destinationAreaId ? Number(destinationAreaId) : null
  const selectedArea = areas.find((area) => area.area_id === selectedAreaId)
  const hasOwnAreaConflict = workers.some(
    (worker) => workerIds.includes(worker.user_id) && worker.regular_area_id === selectedAreaId,
  )

  function resetEditor() {
    setIsCreating(false)
    setEditingAssignmentId(null)
    setDestinationAreaId('')
    setWorkerIds([])
    setNote('')
    setSaveError('')
  }

  function startCreating() {
    resetEditor()
    setIsCreating(true)
  }

  function startEditing(assignment) {
    setIsCreating(false)
    setEditingAssignmentId(assignment.assignment_id)
    setDestinationAreaId(String(assignment.destination_area_id))
    setWorkerIds(assignment.worker_ids)
    setNote(assignment.note || '')
    setSaveError('')
  }

  function toggleWorker(workerId) {
    setWorkerIds((currentIds) => currentIds.includes(workerId)
      ? currentIds.filter((currentId) => currentId !== workerId)
      : [...currentIds, workerId])
  }

  async function handleSave(event) {
    event.preventDefault()
    if (!selectedArea) {
      setSaveError('Select a destination area.')
      return
    }
    if (workerIds.length === 0) {
      setSaveError('Select at least one worker.')
      return
    }
    if (workerIds.some((workerId) => assignedElsewhereIds.has(workerId))) {
      setSaveError('A selected worker already has another assignment today.')
      return
    }
    if (hasOwnAreaConflict) {
      setSaveError('A worker cannot cover their own regular area.')
      return
    }

    const payload = {
      assignment_date: todayKey,
      assignment_type: 'Coverage',
      destination_area_id: selectedArea.area_id,
      location_task: `${selectedArea.area_name} coverage`,
      worker_ids: workerIds,
      note: note.trim() || null,
    }

    setIsSaving(true)
    setSaveError('')
    try {
      if (editingAssignmentId === null) {
        await createAssignment(payload)
      } else {
        await updateAssignment(editingAssignmentId, payload)
      }
      resetEditor()
      await loadData()
    } catch (requestError) {
      setSaveError(requestError.message)
    } finally {
      setIsSaving(false)
    }
  }

  async function handleRemove(assignment) {
    const confirmed = window.confirm(
      `Remove temporary coverage for ${assignment.destination_area_name}?`,
    )
    if (!confirmed) return

    setRemovingAssignmentId(assignment.assignment_id)
    setLoadError('')
    try {
      await deleteAssignment(assignment.assignment_id)
      if (editingAssignmentId === assignment.assignment_id) resetEditor()
      await loadData()
    } catch (requestError) {
      setLoadError(requestError.message)
    } finally {
      setRemovingAssignmentId(null)
    }
  }

  const isEditorOpen = isCreating || editingAssignmentId !== null
  const dateLabel = today.toLocaleDateString([], {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })

  return (
    <section className="assignments-page" aria-labelledby="assignments-title">
      <div className="page-heading assignments-heading">
        <div>
          <p className="eyebrow">Today</p>
          <h2 id="assignments-title">Temporary Assignments</h2>
          <p className="muted-text">{dateLabel}</p>
        </div>
        {!isEditorOpen && (
          <button type="button" onClick={startCreating} disabled={isLoading}>
            New assignment
          </button>
        )}
      </div>

      {isEditorOpen && (
        <form className="assignment-editor" onSubmit={handleSave}>
          <div className="assignment-editor-heading">
            <div>
              <h3>{isCreating ? 'New temporary coverage' : 'Edit temporary coverage'}</h3>
              <p className="muted-text">Choose a destination and one or more workers.</p>
            </div>
          </div>

          <label htmlFor="assignment-destination">
            Destination area
            <select
              id="assignment-destination"
              value={destinationAreaId}
              onChange={(event) => setDestinationAreaId(event.target.value)}
              disabled={isSaving}
            >
              <option value="">Select an area</option>
              {areas.map((area) => (
                <option key={area.area_id} value={area.area_id}>
                  {area.building_name} — {area.area_name}
                </option>
              ))}
            </select>
          </label>

          <fieldset disabled={isSaving}>
            <legend>Workers</legend>
            <p className="assignment-help">
              Workers may be selected even when their availability is Away.
            </p>
            <div className="assignment-worker-options">
              {workers.map((worker) => {
                const isSelected = workerIds.includes(worker.user_id)
                const hasAnotherAssignment = assignedElsewhereIds.has(worker.user_id)
                const isOwnArea = selectedAreaId !== null
                  && worker.regular_area_id === selectedAreaId
                const isDisabled = !isSelected && (hasAnotherAssignment || isOwnArea)
                let explanation = worker.regular_area_name || 'No regular area'
                if (hasAnotherAssignment) explanation = 'Already assigned today'
                if (isOwnArea) explanation = 'This is their regular area'

                return (
                  <label key={worker.user_id} className={isDisabled ? 'worker-option worker-option--disabled' : 'worker-option'}>
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleWorker(worker.user_id)}
                      disabled={isDisabled}
                    />
                    <span>
                      <strong>{worker.name}</strong>
                      <small>{explanation}</small>
                    </span>
                  </label>
                )
              })}
            </div>
            {workers.length === 0 && <p className="muted-text">No active workers are available.</p>}
          </fieldset>

          <label htmlFor="assignment-note">
            Note <span className="muted-text">(optional)</span>
            <textarea
              id="assignment-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              disabled={isSaving}
              rows="3"
            />
          </label>

          {hasOwnAreaConflict && (
            <p className="form-error" role="alert">
              Remove any selected worker whose regular area is the destination.
            </p>
          )}
          {saveError && <p className="form-error" role="alert">{saveError}</p>}
          <div className="assignment-editor-actions">
            <button type="submit" disabled={isSaving || hasOwnAreaConflict}>
              {isSaving ? 'Saving...' : isCreating ? 'Create assignment' : 'Save changes'}
            </button>
            <button type="button" className="secondary-button" onClick={resetEditor} disabled={isSaving}>
              Cancel
            </button>
          </div>
        </form>
      )}

      {isLoading && <p className="muted-text">Loading today&apos;s assignments...</p>}
      {loadError && (
        <div className="attendance-error" role="alert">
          <p className="form-error">{loadError}</p>
          <button type="button" className="secondary-button" onClick={loadData}>Try again</button>
        </div>
      )}
      {!isLoading && !loadError && assignments.length === 0 && (
        <p className="empty-state">No temporary assignments are recorded for today.</p>
      )}
      {!isLoading && !loadError && assignments.length > 0 && (
        <ul className="assignment-list">
          {assignments.map((assignment) => {
            const isStructured = assignment.destination_area_id !== null
            return (
              <li key={assignment.assignment_id} className="assignment-row">
                <div className="assignment-details">
                  <span className={isStructured ? 'assignment-kind' : 'assignment-kind assignment-kind--legacy'}>
                    {isStructured ? 'Temporary coverage' : 'Free-form assignment'}
                  </span>
                  <h3>
                    {isStructured
                      ? `${assignment.destination_building_name} — ${assignment.destination_area_name}`
                      : assignment.location_task}
                  </h3>
                  <p><strong>Workers:</strong> {assignment.workers.map((worker) => worker.name).join(', ')}</p>
                  {assignment.note && <p className="assignment-note"><strong>Note:</strong> {assignment.note}</p>}
                  {!isStructured && <p className="assignment-read-only">Legacy free-form assignments are read-only.</p>}
                </div>
                {isStructured && (
                  <div className="assignment-row-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => startEditing(assignment)}
                      disabled={isSaving || removingAssignmentId !== null}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="secondary-button assignment-remove-button"
                      onClick={() => handleRemove(assignment)}
                      disabled={isSaving || removingAssignmentId !== null}
                    >
                      {removingAssignmentId === assignment.assignment_id ? 'Removing...' : 'Remove'}
                    </button>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}

export default AssignmentsPage
