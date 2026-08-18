import { apiRequest } from './client'

export function getUsers() { return apiRequest('/users') }
export function createUser(data) { return apiRequest('/users', { method: 'POST', body: JSON.stringify(data) }) }
export function updateUser(userId, data) { return apiRequest(`/users/${userId}`, { method: 'PATCH', body: JSON.stringify(data) }) }
