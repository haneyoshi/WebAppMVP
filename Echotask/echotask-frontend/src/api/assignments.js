import { apiRequest } from './client'

export function getAssignments({ date } = {}) {
  const search = date ? `?date=${encodeURIComponent(date)}` : ''
  return apiRequest(`/assignments${search}`)
}

export function createAssignment(assignment) {
  return apiRequest('/assignments', {
    method: 'POST',
    body: JSON.stringify(assignment),
  })
}

export function updateAssignment(assignmentId, assignment) {
  return apiRequest(`/assignments/${assignmentId}`, {
    method: 'PUT',
    body: JSON.stringify(assignment),
  })
}

export function deleteAssignment(assignmentId) {
  return apiRequest(`/assignments/${assignmentId}`, { method: 'DELETE' })
}
