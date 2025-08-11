const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export function api(path: string, init: RequestInit = {}) {
  const token =
    typeof localStorage !== 'undefined'
      ? localStorage.getItem('token')
      : null
  const headers = new Headers(init.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return fetch(`${API_BASE_URL}${path}`, { ...init, headers })
}
