// Tokenul băncii stă doar în sessionStorage (niciodată în VITE_* sau în URL).

const TOKEN_KEY = 'orb.token'
const NAME_KEY = 'orb.name'

export function getToken(): string | null {
  try { return sessionStorage.getItem(TOKEN_KEY) } catch { return null }
}

export function getUserName(): string {
  try { return sessionStorage.getItem(NAME_KEY) || '' } catch { return '' }
}

export function login(token: string, name: string) {
  sessionStorage.setItem(TOKEN_KEY, token.trim())
  sessionStorage.setItem(NAME_KEY, name.trim())
}

export function logout() {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(NAME_KEY)
}
