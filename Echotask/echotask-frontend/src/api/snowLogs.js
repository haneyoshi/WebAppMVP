import { apiRequest } from './client'

export function getSnowLogLocations({ areaId } = {}) {
  const search = areaId ? `?area_id=${encodeURIComponent(areaId)}` : ''
  return apiRequest(`/snow-log-locations${search}`)
}

export function createSnowLogLocation(location) {
  return apiRequest('/snow-log-locations', {
    method: 'POST',
    body: JSON.stringify(location),
  })
}

export function updateSnowLogLocation(locationId, updates) {
  return apiRequest(`/snow-log-locations/${locationId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  })
}

export function createSnowLog(snowLog) {
  return apiRequest('/snow-logs', {
    method: 'POST',
    body: JSON.stringify(snowLog),
  })
}

export function getSnowLogs() {
  return apiRequest('/snow-logs')
}
