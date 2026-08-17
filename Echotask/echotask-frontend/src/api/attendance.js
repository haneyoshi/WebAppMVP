import { apiRequest } from './client'

export function getAttendance({ date } = {}) {
  const search = date ? `?date=${encodeURIComponent(date)}` : ''
  return apiRequest(`/attendance${search}`)
}

export function checkIn() {
  return apiRequest('/attendance/check-in', { method: 'POST' })
}
