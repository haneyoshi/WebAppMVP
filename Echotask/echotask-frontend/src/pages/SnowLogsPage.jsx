import { useCallback, useEffect, useState } from 'react'
import { getAreas } from '../api/locations'
import {
  createSnowLog,
  createSnowLogLocation,
  getSnowLogLocations,
  getSnowLogs,
  updateSnowLogLocation,
} from '../api/snowLogs'

function formatSnowLogTimestamp(timestamp) {
  if (!timestamp) return 'Time unavailable'
  const parsedTimestamp = new Date(timestamp)
  if (Number.isNaN(parsedTimestamp.getTime())) return 'Time unavailable'
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsedTimestamp)
}

function SnowLogsPage({ user }) {
  const [locations, setLocations] = useState([])
  const [isLoading, setIsLoading] = useState(user.role === 'worker')
  const [loadError, setLoadError] = useState('')
  const [locationId, setLocationId] = useState('')
  const [actionTaken, setActionTaken] = useState('')
  const [condition, setCondition] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')
  const [submittedLog, setSubmittedLog] = useState(null)
  const [history, setHistory] = useState([])
  const [isHistoryLoading, setIsHistoryLoading] = useState(user.role !== 'worker')
  const [historyError, setHistoryError] = useState('')
  const [managementLocations, setManagementLocations] = useState([])
  const [areas, setAreas] = useState([])
  const [isManagementLoading, setIsManagementLoading] = useState(user.role !== 'worker')
  const [managementError, setManagementError] = useState('')
  const [managementActionError, setManagementActionError] = useState('')
  const [managementMessage, setManagementMessage] = useState('')
  const [newAreaId, setNewAreaId] = useState('')
  const [newLocationName, setNewLocationName] = useState('')
  const [isCreatingLocation, setIsCreatingLocation] = useState(false)
  const [editingLocationId, setEditingLocationId] = useState(null)
  const [editingLocationName, setEditingLocationName] = useState('')
  const [savingLocationId, setSavingLocationId] = useState(null)

  const loadLocations = useCallback(async () => {
    if (user.role !== 'worker') return
    if (!user.area_id) {
      setLocations([])
      setLoadError('Snow Log submission is unavailable because your account has no regular area.')
      setIsLoading(false)
      return
    }

    setIsLoading(true)
    setLoadError('')
    try {
      const availableLocations = await getSnowLogLocations({ areaId: user.area_id })
      setLocations(availableLocations.filter((location) => location.is_active === true))
    } catch (requestError) {
      setLoadError(requestError.message)
    } finally {
      setIsLoading(false)
    }
  }, [user.area_id, user.role])

  useEffect(() => {
    loadLocations()
  }, [loadLocations])

  const loadHistory = useCallback(async () => {
    if (user.role === 'worker') return

    setIsHistoryLoading(true)
    setHistoryError('')
    try {
      setHistory(await getSnowLogs())
    } catch (requestError) {
      setHistoryError(requestError.message)
    } finally {
      setIsHistoryLoading(false)
    }
  }, [user.role])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  const loadManagementData = useCallback(async () => {
    if (user.role === 'worker') return

    setIsManagementLoading(true)
    setManagementError('')
    try {
      const [availableLocations, availableAreas] = await Promise.all([
        getSnowLogLocations(),
        getAreas(),
      ])
      setManagementLocations(availableLocations)
      setAreas(availableAreas)
    } catch (requestError) {
      setManagementError(requestError.message)
    } finally {
      setIsManagementLoading(false)
    }
  }, [user.role])

  useEffect(() => {
    loadManagementData()
  }, [loadManagementData])

  async function refreshLocationsAfterMutation(message) {
    await loadManagementData()
    setManagementMessage(message)
  }

  async function handleCreateLocation(event) {
    event.preventDefault()
    const areaId = Number(newAreaId)
    if (!Number.isInteger(areaId) || !newLocationName.trim()) {
      setManagementActionError('Select an area and enter a location name.')
      return
    }

    setIsCreatingLocation(true)
    setManagementActionError('')
    setManagementMessage('')
    try {
      await createSnowLogLocation({ area_id: areaId, location_name: newLocationName.trim() })
      setNewAreaId('')
      setNewLocationName('')
      await refreshLocationsAfterMutation('Snow Log location created.')
    } catch (requestError) {
      setManagementActionError(requestError.message)
    } finally {
      setIsCreatingLocation(false)
    }
  }

  function beginRename(location) {
    setEditingLocationId(location.snow_log_location_id)
    setEditingLocationName(location.location_name)
    setManagementActionError('')
    setManagementMessage('')
  }

  async function handleRename(event, locationId) {
    event.preventDefault()
    if (!editingLocationName.trim()) {
      setManagementActionError('Location name cannot be empty.')
      return
    }

    setSavingLocationId(locationId)
    setManagementActionError('')
    setManagementMessage('')
    try {
      await updateSnowLogLocation(locationId, { location_name: editingLocationName.trim() })
      setEditingLocationId(null)
      setEditingLocationName('')
      await refreshLocationsAfterMutation('Snow Log location renamed.')
    } catch (requestError) {
      setManagementActionError(requestError.message)
    } finally {
      setSavingLocationId(null)
    }
  }

  async function handleLocationState(location) {
    const locationId = location.snow_log_location_id
    setSavingLocationId(locationId)
    setManagementActionError('')
    setManagementMessage('')
    try {
      await updateSnowLogLocation(locationId, { is_active: !location.is_active })
      await refreshLocationsAfterMutation(
        `Snow Log location ${location.is_active ? 'deactivated' : 'activated'}.`,
      )
    } catch (requestError) {
      setManagementActionError(requestError.message)
    } finally {
      setSavingLocationId(null)
    }
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const selectedLocationId = Number(locationId)
    const selectedLocation = locations.find(
      (location) => location.snow_log_location_id === selectedLocationId,
    )
    if (!selectedLocation) {
      setSubmitError('Select an active snow-clearing location.')
      return
    }

    setIsSubmitting(true)
    setSubmitError('')
    try {
      const result = await createSnowLog({
        snow_log_location_id: selectedLocationId,
        action_taken: actionTaken.trim() || null,
        condition: condition.trim() || null,
      })
      setSubmittedLog(result)
    } catch (requestError) {
      setSubmitError(requestError.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  function resetForm() {
    setLocationId('')
    setActionTaken('')
    setCondition('')
    setSubmitError('')
    setSubmittedLog(null)
  }

  if (user.role !== 'worker') {
    const sortedManagementLocations = [...managementLocations].sort((first, second) =>
      first.building_name.localeCompare(second.building_name)
      || first.area_name.localeCompare(second.area_name)
      || first.location_name.localeCompare(second.location_name),
    )

    return (
      <section className="snow-logs-page" aria-labelledby="snow-logs-title">
        <div className="page-heading">
          <p className="eyebrow">Winter operations</p>
          <h2 id="snow-logs-title">Snow Logs</h2>
          <p className="muted-text">Manage snow-clearing locations and review completed work.</p>
        </div>

        <section className="snow-location-management" aria-labelledby="snow-locations-title">
          <div className="snow-location-management-heading">
            <div>
              <p className="eyebrow">Location setup</p>
              <h3 id="snow-locations-title">Snow Log Locations</h3>
              <p className="muted-text">Manage reusable locations while preserving inactive locations.</p>
            </div>
          </div>

          <form className="snow-location-create-form" onSubmit={handleCreateLocation}>
            <label htmlFor="snow-location-area">
              Area
              <select
                id="snow-location-area"
                value={newAreaId}
                onChange={(event) => setNewAreaId(event.target.value)}
                disabled={isCreatingLocation || isManagementLoading}
                required
              >
                <option value="">Select an area</option>
                {areas.map((area) => (
                  <option key={area.area_id} value={area.area_id}>
                    {area.building_name} — {area.area_name}
                  </option>
                ))}
              </select>
            </label>
            <label htmlFor="snow-location-name">
              Location name
              <input
                id="snow-location-name"
                value={newLocationName}
                onChange={(event) => setNewLocationName(event.target.value)}
                disabled={isCreatingLocation || isManagementLoading}
                required
              />
            </label>
            <button type="submit" disabled={isCreatingLocation || isManagementLoading}>
              {isCreatingLocation ? 'Creating...' : 'Add location'}
            </button>
          </form>

          {managementActionError && <p className="form-error" role="alert">{managementActionError}</p>}
          {managementMessage && <p className="form-success" aria-live="polite">{managementMessage}</p>}
          {isManagementLoading && (
            <p className="muted-text" aria-live="polite">Loading Snow Log locations&hellip;</p>
          )}
          {!isManagementLoading && managementError && (
            <div className="attendance-error" role="alert">
              <p className="form-error">{managementError}</p>
              <button type="button" className="secondary-button" onClick={loadManagementData}>Try again</button>
            </div>
          )}
          {!isManagementLoading && !managementError && sortedManagementLocations.length === 0 && (
            <p className="empty-state">No Snow Log locations have been created.</p>
          )}
          {!isManagementLoading && !managementError && sortedManagementLocations.length > 0 && (
            <ul className="snow-location-list">
              {sortedManagementLocations.map((location) => {
                const isEditing = editingLocationId === location.snow_log_location_id
                const isSaving = savingLocationId === location.snow_log_location_id
                return (
                  <li key={location.snow_log_location_id} className="snow-location-row">
                    <div className="snow-location-details">
                      <span>{location.building_name} — {location.area_name}</span>
                      <h4>{location.location_name}</h4>
                      <span className={`status-badge${location.is_active ? '' : ' status-badge--inactive'}`}>
                        {location.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    {isEditing ? (
                      <form className="snow-location-rename-form" onSubmit={(event) => handleRename(event, location.snow_log_location_id)}>
                        <label htmlFor={`snow-location-name-${location.snow_log_location_id}`}>
                          Location name
                          <input
                            id={`snow-location-name-${location.snow_log_location_id}`}
                            value={editingLocationName}
                            onChange={(event) => setEditingLocationName(event.target.value)}
                            disabled={isSaving}
                            required
                            autoFocus
                          />
                        </label>
                        <div className="snow-location-actions">
                          <button type="submit" disabled={isSaving}>{isSaving ? 'Saving...' : 'Save'}</button>
                          <button type="button" className="secondary-button" disabled={isSaving} onClick={() => setEditingLocationId(null)}>Cancel</button>
                        </div>
                      </form>
                    ) : (
                      <div className="snow-location-actions">
                        <button type="button" className="secondary-button" disabled={isSaving} onClick={() => beginRename(location)}>Rename</button>
                        <button type="button" className="secondary-button" disabled={isSaving} onClick={() => handleLocationState(location)}>
                          {isSaving ? 'Saving...' : location.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        <div className="snow-log-history-heading-block">
          <p className="eyebrow">Completed work</p>
          <h3>Snow Log History</h3>
        </div>

        {isHistoryLoading && (
          <p className="muted-text" aria-live="polite">Loading Snow Log history&hellip;</p>
        )}
        {!isHistoryLoading && historyError && (
          <div className="attendance-error" role="alert">
            <p className="form-error">{historyError}</p>
            <button type="button" className="secondary-button" onClick={loadHistory}>Try again</button>
          </div>
        )}
        {!isHistoryLoading && !historyError && history.length === 0 && (
          <p className="empty-state">No Snow Logs have been recorded.</p>
        )}
        {!isHistoryLoading && !historyError && history.length > 0 && (
          <ul className="snow-log-history-list">
            {history.map((log) => (
              <li key={log.snow_log_id} className="snow-log-history-row">
                <div className="snow-log-history-heading">
                  <span>{log.area_name}</span>
                  <h3>{log.location_name}</h3>
                  <p>{log.user_name}</p>
                  <time dateTime={log.timestamp || undefined}>
                    {formatSnowLogTimestamp(log.timestamp)}
                  </time>
                </div>
                <dl className="snow-log-history-details">
                  <div>
                    <dt>Action taken</dt>
                    <dd>{log.action_taken || 'Not provided'}</dd>
                  </div>
                  <div>
                    <dt>Condition</dt>
                    <dd>{log.condition || 'Not provided'}</dd>
                  </div>
                </dl>
              </li>
            ))}
          </ul>
        )}
      </section>
    )
  }

  return (
    <section className="snow-logs-page" aria-labelledby="snow-logs-title">
      <div className="page-heading">
        <p className="eyebrow">Completed work</p>
        <h2 id="snow-logs-title">Submit a Snow Log</h2>
        <p className="muted-text">Record snow-clearing work after it is completed.</p>
      </div>

      {isLoading && <p className="muted-text" aria-live="polite">Loading snow-clearing locations&hellip;</p>}
      {!isLoading && loadError && (
        <div className="attendance-error" role="alert">
          <p className="form-error">{loadError}</p>
          {user.area_id && (
            <button type="button" className="secondary-button" onClick={loadLocations}>
              Try again
            </button>
          )}
        </div>
      )}
      {!isLoading && !loadError && locations.length === 0 && (
        <p className="empty-state">No active snow-clearing locations are available for your area.</p>
      )}

      {!isLoading && !loadError && locations.length > 0 && submittedLog && (
        <div className="snow-log-confirmation" aria-live="polite">
          <span className="status-badge">Recorded</span>
          <h3>Snow Log recorded</h3>
          <dl>
            <div>
              <dt>Location</dt>
              <dd>{submittedLog.location_name}</dd>
            </div>
            <div>
              <dt>Area</dt>
              <dd>{submittedLog.area_name}</dd>
            </div>
            {submittedLog.action_taken && (
              <div>
                <dt>Action taken</dt>
                <dd>{submittedLog.action_taken}</dd>
              </div>
            )}
            {submittedLog.condition && (
              <div>
                <dt>Condition</dt>
                <dd>{submittedLog.condition}</dd>
              </div>
            )}
          </dl>
          <button type="button" onClick={resetForm}>Submit another log</button>
        </div>
      )}

      {!isLoading && !loadError && locations.length > 0 && !submittedLog && (
        <form className="snow-log-form" onSubmit={handleSubmit}>
          <label htmlFor="snow-log-location">
            Snow-clearing location
            <select
              id="snow-log-location"
              value={locationId}
              onChange={(event) => setLocationId(event.target.value)}
              disabled={isSubmitting}
              required
            >
              <option value="">Select a location</option>
              {locations.map((location) => (
                <option key={location.snow_log_location_id} value={location.snow_log_location_id}>
                  {location.location_name}
                </option>
              ))}
            </select>
          </label>
          <label htmlFor="snow-log-action">
            Action taken <span className="muted-text">(optional)</span>
            <textarea
              id="snow-log-action"
              value={actionTaken}
              onChange={(event) => setActionTaken(event.target.value)}
              disabled={isSubmitting}
              rows="3"
            />
          </label>
          <label htmlFor="snow-log-condition">
            Condition <span className="muted-text">(optional)</span>
            <textarea
              id="snow-log-condition"
              value={condition}
              onChange={(event) => setCondition(event.target.value)}
              disabled={isSubmitting}
              rows="3"
            />
          </label>
          {submitError && <p className="form-error" role="alert">{submitError}</p>}
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Submitting...' : 'Submit Snow Log'}
          </button>
        </form>
      )}
    </section>
  )
}

export default SnowLogsPage
