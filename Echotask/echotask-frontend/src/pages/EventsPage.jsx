import { useCallback, useEffect, useState } from 'react'
import { createEvent, getEvents, updateEvent } from '../api/events'
import { getBuildings } from '../api/locations'

const eventDateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

function formatEventDateTime(timestamp) {
  const date = new Date(timestamp)
  return Number.isNaN(date.getTime()) ? 'Time unavailable' : eventDateTimeFormatter.format(date)
}

function utcTimestampToLocalInput(timestamp) {
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return ''
  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return localDate.toISOString().slice(0, 16)
}

function localInputToUtcTimestamp(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date.toISOString()
}

function EventsPage({ user }) {
  const canManageEvents = user.role === 'coordinator' || user.role === 'supervisor'
  const [events, setEvents] = useState([])
  const [buildings, setBuildings] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [editingEventId, setEditingEventId] = useState(null)
  const [buildingId, setBuildingId] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  const loadData = useCallback(async () => {
    setIsLoading(true)
    setLoadError('')
    try {
      if (canManageEvents) {
        const [listedEvents, listedBuildings] = await Promise.all([getEvents(), getBuildings()])
        setEvents(listedEvents)
        setBuildings(listedBuildings)
      } else {
        setEvents(await getEvents())
      }
    } catch (requestError) {
      setLoadError(requestError.message)
    } finally {
      setIsLoading(false)
    }
  }, [canManageEvents])

  useEffect(() => {
    loadData()
  }, [loadData])

  function resetEditor() {
    setIsCreating(false)
    setEditingEventId(null)
    setBuildingId('')
    setTitle('')
    setDescription('')
    setStartTime('')
    setEndTime('')
    setSaveError('')
  }

  function startCreating() {
    resetEditor()
    setIsCreating(true)
  }

  function startEditing(event) {
    setIsCreating(false)
    setEditingEventId(event.event_id)
    setBuildingId(String(event.building_id))
    setTitle(event.title)
    setDescription(event.description || '')
    setStartTime(utcTimestampToLocalInput(event.start_time))
    setEndTime(utcTimestampToLocalInput(event.end_time))
    setSaveError('')
  }

  async function handleSave(submitEvent) {
    submitEvent.preventDefault()
    const utcStartTime = localInputToUtcTimestamp(startTime)
    const utcEndTime = localInputToUtcTimestamp(endTime)

    if (!buildingId) {
      setSaveError('Select a building.')
      return
    }
    if (!title.trim()) {
      setSaveError('Enter an event title.')
      return
    }
    if (!utcStartTime || !utcEndTime) {
      setSaveError('Enter valid start and end times.')
      return
    }
    if (new Date(utcEndTime) <= new Date(utcStartTime)) {
      setSaveError('End time must be after start time.')
      return
    }

    const payload = {
      building_id: Number(buildingId),
      title: title.trim(),
      description: description.trim() || null,
      start_time: utcStartTime,
      end_time: utcEndTime,
    }

    setIsSaving(true)
    setSaveError('')
    try {
      if (editingEventId === null) {
        await createEvent(payload)
      } else {
        await updateEvent(editingEventId, payload)
      }
      resetEditor()
      await loadData()
    } catch (requestError) {
      setSaveError(requestError.message)
    } finally {
      setIsSaving(false)
    }
  }

  const isEditorOpen = isCreating || editingEventId !== null

  return (
    <section className="events-page" aria-labelledby="events-title">
      <div className="page-heading events-heading">
        <div>
          <p className="eyebrow">Schedule</p>
          <h2 id="events-title">Events</h2>
          <p className="muted-text">Times are shown in your local timezone.</p>
        </div>
        {canManageEvents && !isEditorOpen && (
          <button type="button" onClick={startCreating} disabled={isLoading}>
            New event
          </button>
        )}
      </div>

      {canManageEvents && isEditorOpen && (
        <form className="event-editor" onSubmit={handleSave}>
          <h3>{isCreating ? 'New event' : 'Edit event'}</h3>
          <label htmlFor="event-building">
            Building
            <select
              id="event-building"
              value={buildingId}
              onChange={(event) => setBuildingId(event.target.value)}
              disabled={isSaving}
              required
            >
              <option value="">Select a building</option>
              {buildings.map((building) => (
                <option key={building.building_id} value={building.building_id}>
                  {building.building_name}
                </option>
              ))}
            </select>
          </label>
          <label htmlFor="event-title">
            Title
            <input
              id="event-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              disabled={isSaving}
              required
            />
          </label>
          <label className="event-editor-wide" htmlFor="event-description">
            Description <span className="muted-text">(optional)</span>
            <textarea
              id="event-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              disabled={isSaving}
              rows="3"
            />
          </label>
          <label htmlFor="event-start-time">
            Start date and time
            <input
              id="event-start-time"
              type="datetime-local"
              value={startTime}
              onChange={(event) => setStartTime(event.target.value)}
              disabled={isSaving}
              required
            />
          </label>
          <label htmlFor="event-end-time">
            End date and time
            <input
              id="event-end-time"
              type="datetime-local"
              value={endTime}
              onChange={(event) => setEndTime(event.target.value)}
              disabled={isSaving}
              required
            />
          </label>
          {saveError && <p className="form-error event-editor-wide" role="alert">{saveError}</p>}
          <div className="event-editor-actions event-editor-wide">
            <button type="submit" disabled={isSaving}>
              {isSaving ? 'Saving...' : isCreating ? 'Create event' : 'Save changes'}
            </button>
            <button type="button" className="secondary-button" onClick={resetEditor} disabled={isSaving}>
              Cancel
            </button>
          </div>
        </form>
      )}

      {isLoading && <p className="muted-text" aria-live="polite">Loading events&hellip;</p>}
      {loadError && (
        <div className="attendance-error" role="alert">
          <p className="form-error">{loadError}</p>
          <button type="button" className="secondary-button" onClick={loadData}>Try again</button>
        </div>
      )}
      {!isLoading && !loadError && events.length === 0 && (
        <p className="empty-state">No events are scheduled.</p>
      )}
      {!isLoading && !loadError && events.length > 0 && (
        <ul className="event-management-list">
          {events.map((event) => (
            <li key={event.event_id} className="event-management-row">
              <div className="event-management-details">
                <span className="event-building">{event.building_name}</span>
                <h3>{event.title}</h3>
                <p>
                  <time dateTime={event.start_time}>{formatEventDateTime(event.start_time)}</time>
                  {' — '}
                  <time dateTime={event.end_time}>{formatEventDateTime(event.end_time)}</time>
                </p>
                {event.description && <p className="event-description">{event.description}</p>}
              </div>
              {canManageEvents && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => startEditing(event)}
                  disabled={isSaving}
                >
                  Edit
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

export default EventsPage
