import { apiRequest } from './client'

export function getSupplyItems() {
  return apiRequest('/supplies/items')
}

export function createSupplyRequest(request) {
  return apiRequest('/supplies/requests', {
    method: 'POST',
    body: JSON.stringify(request),
  })
}

export function getSupplyRequests() {
  return apiRequest('/supplies/requests')
}

export function updateSupplyRequestStatus(requestId, status) {
  return apiRequest(`/supplies/requests/${requestId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}
