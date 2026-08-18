import { useCallback, useEffect, useState } from 'react'
import { getWorkerAvailability } from '../api/availability'
import { getEvents } from '../api/events'
import { getAreas } from '../api/locations'

const dashboardSections = [
  { title: "Today's Operations", message: 'More operational detail will be added in a future milestone.' },
]

const eventTimeFormatter = new Intl.DateTimeFormat(undefined, {
  hour: 'numeric',
  minute: '2-digit',
})

function parseEventTimestamp(timestamp) {
  return new Date(timestamp)
}

function eventOverlapsLocalDay(event, dayStart, nextDayStart) {
  const eventStart = parseEventTimestamp(event.start_time)
  const eventEnd = parseEventTimestamp(event.end_time)
  return eventStart < nextDayStart && eventEnd > dayStart
}

function formatEventTimeRange(event) {
  const eventStart = parseEventTimestamp(event.start_time)
  const eventEnd = parseEventTimestamp(event.end_time)
  return `${eventTimeFormatter.format(eventStart)} – ${eventTimeFormatter.format(eventEnd)}`
}

function localDateKey(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function statusClassName(status) {
  if (status === 'Away' || status === 'Unavailable') return 'status-badge status-badge--away'
  if (status === 'Assigned elsewhere') return 'status-badge status-badge--assigned'
  return 'status-badge'
}

function summarizeBuildings(areas, workersById, coverageByAreaId) {
  const buildingsById = new Map()

  areas.forEach((area) => {
    const building = buildingsById.get(area.building_id) || {
      buildingId: area.building_id,
      buildingName: area.building_name,
      areas: [],
      working: 0,
      away: 0,
      assignedElsewhere: 0,
      temporaryCoverage: 0,
      uncovered: 0,
    }
    const regularWorker = workersById.get(area.assigned_user_id)
    const regularStatus = regularWorker?.status
    const hasTemporaryCoverage = coverageByAreaId.has(area.area_id)

    if (regularStatus === 'Working') building.working += 1
    if (regularStatus === 'Away') building.away += 1
    if (regularStatus === 'Assigned elsewhere') building.assignedElsewhere += 1
    if (hasTemporaryCoverage) building.temporaryCoverage += 1
    if (regularStatus !== 'Working' && !hasTemporaryCoverage) building.uncovered += 1

    building.areas.push({
      areaId: area.area_id,
      areaName: area.area_name,
      assignedUserId: area.assigned_user_id,
      regularWorker,
      coveringWorkers: coverageByAreaId.get(area.area_id) || [],
      visualState: hasTemporaryCoverage
        ? 'temporary'
        : regularStatus === 'Working' ? 'working' : 'uncovered',
    })
    buildingsById.set(area.building_id, building)
  })

  return [...buildingsById.values()].sort((a, b) => (
    a.buildingName.localeCompare(b.buildingName)
  ))
}

function DashboardPage({ user }) {
  const today = new Date()
  const todayKey = localDateKey(today)
  const canViewAvailability = user.role === 'coordinator' || user.role === 'supervisor'
  const [workers, setWorkers] = useState([])
  const [areas, setAreas] = useState([])
  const [isAvailabilityLoading, setIsAvailabilityLoading] = useState(canViewAvailability)
  const [availabilityError, setAvailabilityError] = useState('')
  const [areAreasLoading, setAreAreasLoading] = useState(canViewAvailability)
  const [areasError, setAreasError] = useState('')
  const [events, setEvents] = useState([])
  const [areEventsLoading, setAreEventsLoading] = useState(true)
  const [eventsError, setEventsError] = useState('')
  const [selectedBuildingId, setSelectedBuildingId] = useState(null)

  const loadAvailability = useCallback(async () => {
    if (!canViewAvailability) return
    setIsAvailabilityLoading(true)
    setAvailabilityError('')
    try {
      setWorkers(await getWorkerAvailability({ date: todayKey }))
    } catch (requestError) {
      setAvailabilityError(requestError.message)
    } finally {
      setIsAvailabilityLoading(false)
    }
  }, [canViewAvailability, todayKey])

  const loadAreas = useCallback(async () => {
    if (!canViewAvailability) return
    setAreAreasLoading(true)
    setAreasError('')
    try {
      setAreas(await getAreas())
    } catch (requestError) {
      setAreasError(requestError.message)
    } finally {
      setAreAreasLoading(false)
    }
  }, [canViewAvailability])

  const loadEvents = useCallback(async () => {
    setAreEventsLoading(true)
    setEventsError('')
    try {
      setEvents(await getEvents())
    } catch (requestError) {
      setEventsError(requestError.message)
    } finally {
      setAreEventsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAvailability()
    loadAreas()
    loadEvents()
  }, [loadAreas, loadAvailability, loadEvents])

  const dayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const nextDayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1)
  const todaysEvents = events.filter((event) => eventOverlapsLocalDay(event, dayStart, nextDayStart))

  const workersById = new Map(workers.map((worker) => [worker.user_id, worker]))
  const coverageByAreaId = new Map()
  workers.forEach((worker) => {
    worker.assignments.forEach((assignment) => {
      if (assignment.destination_area_id === null) return
      const coveringWorkers = coverageByAreaId.get(assignment.destination_area_id) || []
      if (!coveringWorkers.some((coveringWorker) => coveringWorker.user_id === worker.user_id)) {
        coveringWorkers.push(worker)
      }
      coverageByAreaId.set(assignment.destination_area_id, coveringWorkers)
    })
  })
  const buildingSummaries = summarizeBuildings(areas, workersById, coverageByAreaId)
  const selectedBuilding = buildingSummaries.find(
    (building) => building.buildingId === selectedBuildingId,
  ) || buildingSummaries[0]
  const isCoverageLoading = areAreasLoading || isAvailabilityLoading
  const coverageError = areasError || availabilityError

  return (
    <section aria-labelledby="dashboard-title">
      <div className="page-heading">
        <p className="eyebrow">Daily overview</p>
        <h2 id="dashboard-title">Dashboard</h2>
        <p className="muted-text">A shared operational view of attendance, availability, and area coverage.</p>
      </div>
      <div className="dashboard-grid">
        {canViewAvailability && (
          <section
            className="dashboard-card building-coverage-overview"
            aria-labelledby="building-coverage-title"
          >
            <div className="building-coverage-heading">
              <div>
                <p className="eyebrow">Campus operations</p>
                <h3 id="building-coverage-title">Building Coverage Overview</h3>
                <p className="muted-text">Today&apos;s regular and temporary area coverage by building.</p>
              </div>
              {!isCoverageLoading && !coverageError && (
                <strong>{buildingSummaries.length} buildings</strong>
              )}
            </div>

            {isCoverageLoading && (
              <p className="muted-text" aria-live="polite">Loading building coverage&hellip;</p>
            )}
            {coverageError && (
              <div className="attendance-error" role="alert">
                <p className="form-error">{coverageError}</p>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => {
                    loadAreas()
                    loadAvailability()
                  }}
                >
                  Try again
                </button>
              </div>
            )}
            {!isCoverageLoading && !coverageError && buildingSummaries.length === 0 && (
              <p className="empty-state">No building coverage is available to show.</p>
            )}
            {!isCoverageLoading && !coverageError && buildingSummaries.length > 0 && (
              <div className="building-coverage-layout">
                <ul className="building-coverage-grid">
                  {buildingSummaries.map((building) => {
                    const isSelected = building.buildingId === selectedBuilding.buildingId
                    return (
                      <li key={building.buildingId}>
                        <button
                          type="button"
                          className={`${building.uncovered > 0
                            ? 'building-coverage-card building-coverage-card--attention'
                            : 'building-coverage-card'}${isSelected ? ' building-coverage-card--selected' : ''}`}
                          aria-pressed={isSelected}
                          aria-controls="selected-building-coverage"
                          onClick={() => setSelectedBuildingId(building.buildingId)}
                        >
                          <div className="building-visual" aria-hidden="true">
                            <div className="building-visual-shadow" />
                            <div className="building-model">
                              <div className="building-model-top" />
                              <div className="building-model-side" />
                              <div className="building-model-front">
                                {building.areas.map((area) => (
                                  <span
                                    className={`building-area-segment building-area-segment--${area.visualState}`}
                                    key={area.areaId}
                                  />
                                ))}
                              </div>
                            </div>
                          </div>

                          <div className="building-coverage-card-heading">
                            <h4>{building.buildingName}</h4>
                            <span>{building.areas.length} {building.areas.length === 1 ? 'area' : 'areas'}</span>
                          </div>
                          <dl className="building-coverage-stats">
                            <div><dt>Working</dt><dd>{building.working}</dd></div>
                            <div><dt>Away</dt><dd>{building.away}</dd></div>
                            <div><dt>Assigned elsewhere</dt><dd>{building.assignedElsewhere}</dd></div>
                            <div><dt>Temporary coverage</dt><dd>{building.temporaryCoverage}</dd></div>
                            <div className="building-coverage-stat--wide">
                              <dt>Uncovered areas</dt><dd>{building.uncovered}</dd>
                            </div>
                          </dl>
                        </button>
                      </li>
                    )
                  })}
                </ul>

                <section
                  className="selected-building-coverage"
                  id="selected-building-coverage"
                  aria-labelledby="selected-building-title"
                >
                  <div className="selected-building-heading">
                    <p className="eyebrow">Selected building</p>
                    <h4 id="selected-building-title">{selectedBuilding.buildingName}</h4>
                    <p className="muted-text">
                      {selectedBuilding.areas.length} {selectedBuilding.areas.length === 1 ? 'area' : 'areas'} today
                    </p>
                  </div>
                  <ul className="selected-building-area-list">
                    {selectedBuilding.areas.map((area) => (
                      <li key={area.areaId}>
                        <div className="selected-building-area-heading">
                          <strong>{area.areaName}</strong>
                          {area.assignedUserId === null ? (
                            <span>No regular worker</span>
                          ) : area.regularWorker ? (
                            <span>
                              Regular: <strong>{area.regularWorker.name}</strong>{' '}
                              <span className={statusClassName(area.regularWorker.status)}>
                                {area.regularWorker.status}
                              </span>
                            </span>
                          ) : (
                            <span>Regular worker details unavailable</span>
                          )}
                        </div>
                        <span className="selected-building-temporary">
                          Temporary coverage:{' '}
                          <strong>{area.coveringWorkers.length > 0
                            ? area.coveringWorkers.map((worker) => worker.name).join(', ')
                            : 'None assigned'}</strong>
                        </span>
                      </li>
                    ))}
                  </ul>
                </section>
              </div>
            )}
          </section>
        )}
        <article className="dashboard-card">
          <div className="availability-heading">
            <div>
              <p className="eyebrow">Today</p>
              <h3>Today's Events</h3>
            </div>
            {!areEventsLoading && !eventsError && (
              <strong>{todaysEvents.length} {todaysEvents.length === 1 ? 'event' : 'events'}</strong>
            )}
          </div>
          {areEventsLoading && <p className="muted-text" aria-live="polite">Loading today's events&hellip;</p>}
          {eventsError && (
            <div className="attendance-error" role="alert">
              <p className="form-error">{eventsError}</p>
              <button type="button" className="secondary-button" onClick={loadEvents}>Try again</button>
            </div>
          )}
          {!areEventsLoading && !eventsError && todaysEvents.length === 0 && (
            <p className="empty-state">No events are scheduled today.</p>
          )}
          {!areEventsLoading && !eventsError && todaysEvents.length > 0 && (
            <ul className="event-list">
              {todaysEvents.map((event) => (
                <li key={event.event_id}>
                  <strong>{event.title}</strong>
                  <span>{event.building_name}</span>
                  <time>{formatEventTimeRange(event)}</time>
                </li>
              ))}
            </ul>
          )}
        </article>
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
