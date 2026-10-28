// URL-ul API-ului: ?api=... (ținut minte în localStorage) → VITE_API_URL.
// Mod mock: ?mock=1 (ținut minte pe tab, în sessionStorage) → redă dosarul Mariei fără backend.

const API_KEY = 'orb.api'
const MOCK_KEY = 'orb.mock'

function safe<T>(fn: () => T, fallback: T): T {
  try { return fn() } catch { return fallback }
}

function readParams() {
  const params = new URLSearchParams(window.location.search)
  const api = params.get('api')
  if (api) safe(() => localStorage.setItem(API_KEY, api.replace(/\/+$/, '')), undefined)
  const mock = params.get('mock')
  if (mock !== null) safe(() => sessionStorage.setItem(MOCK_KEY, mock === '0' ? '0' : '1'), undefined)
}
readParams()

export function apiUrl(): string {
  const saved = safe(() => localStorage.getItem(API_KEY), null)
  return saved || import.meta.env.VITE_API_URL || 'http://localhost:8000'
}

/**
 * Headere trimise la FIECARE cerere către backend.
 * ngrok gratuit răspunde cu o pagină HTML de avertizare (nu cu JSON) dacă lipsește headerul ăsta.
 */
export const API_HEADERS: Record<string, string> = { 'ngrok-skip-browser-warning': '1' }

export function isMock(): boolean {
  return safe(() => sessionStorage.getItem(MOCK_KEY) === '1', false)
}
