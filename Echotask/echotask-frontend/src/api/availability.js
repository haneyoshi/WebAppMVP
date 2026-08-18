import { apiRequest } from './client'

export function getWorkerAvailability({ date } = {}) {
  const search = date ? `?date=${encodeURIComponent(date)}` : ''
  return apiRequest(`/workers/availability${search}`)
}
