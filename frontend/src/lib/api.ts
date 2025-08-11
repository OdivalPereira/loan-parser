const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export function api(path: string, init?: RequestInit) {
  return fetch(`${API_BASE_URL}${path}`, init)
}
