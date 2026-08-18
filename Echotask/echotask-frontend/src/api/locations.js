import { apiRequest } from './client'

export function getAreas() {
  return apiRequest('/areas')
}

export function getBuildings() {
  return apiRequest('/buildings')
}
