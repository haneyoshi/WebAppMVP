import { apiRequest } from './client'

export function getEvents() {
  return apiRequest('/events')
}

export function createEvent(event) {
  return apiRequest('/events', {
    method: 'POST',
    body: JSON.stringify(event),
  })
}

export function updateEvent(eventId, event) {
  return apiRequest(`/events/${eventId}`, {
    method: 'PATCH',
    body: JSON.stringify(event),
  })
}
