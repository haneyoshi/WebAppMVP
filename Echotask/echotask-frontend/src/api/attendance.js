import { apiRequest } from './client'

export function getAttendance({ date } = {}) {
  const search = date ? `?date=${encodeURIComponent(date)}` : ''
  return apiRequest(`/attendance${search}`)
}

export function checkIn() {
  return apiRequest('/attendance/check-in', { method: 'POST' })
}

export function createAttendance(attendance) {
  return apiRequest('/attendance', {
    method: 'POST',
    body: JSON.stringify(attendance),
  })
}

export function updateAttendance(attendanceRecordId, attendance) {
  return apiRequest(`/attendance/${attendanceRecordId}`, {
    method: 'PATCH',
    body: JSON.stringify(attendance),
  })
}
