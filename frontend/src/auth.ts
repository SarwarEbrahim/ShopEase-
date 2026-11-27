// Where the access token is kept in the browser.
// localStorage can be blocked (private mode), so every access is wrapped in try/catch.
const KEY = "shopease_token"

// Fired when the server rejects our token (expired, invalid, banned user).
export const AUTH_EXPIRED_EVENT = "auth:expired"

export function getToken(): string | null {
  try {
    return localStorage.getItem(KEY)
  } catch {
    return null
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(KEY, token)
  } catch {
    // Storage is blocked: the user simply has to log in again after a reload.
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(KEY)
  } catch {
    // Nothing to clear.
  }
}
