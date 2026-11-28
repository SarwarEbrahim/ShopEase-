import { useCallback, useEffect, useState } from "react"
import { listSessions, revokeSession } from "../api"
import type { SessionInfo } from "../types"

// A short, readable name for the browser (the full User-Agent string is very long).
export function browserName(userAgent: string | null): string {
  if (!userAgent) return "Unknown device"
  const ua = userAgent.toLowerCase()
  const browser = ua.includes("edg/")
    ? "Edge"
    : ua.includes("chrome")
      ? "Chrome"
      : ua.includes("firefox")
        ? "Firefox"
        : ua.includes("safari")
          ? "Safari"
          : "Browser"
  const os = ua.includes("windows")
    ? "Windows"
    : ua.includes("android")
      ? "Android"
      : ua.includes("iphone") || ua.includes("ipad")
        ? "iOS"
        : ua.includes("mac")
          ? "macOS"
          : ua.includes("linux")
            ? "Linux"
            : ""
  return os ? `${browser} on ${os}` : browser
}

// "My sessions": every device where this account is logged in, with a revoke button.
export default function SessionsList() {
  const [sessions, setSessions] = useState<SessionInfo[] | null>(null)
  const [error, setError] = useState("")

  const load = useCallback(() => {
    listSessions()
      .then(setSessions)
      .catch((err) => setError(err instanceof Error ? err.message : "Something went wrong"))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function revoke(id: number) {
    setError("")
    try {
      await revokeSession(id)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  return (
    <div>
      <h3>My sessions</h3>
      <p>
        <small>These are the devices where you are logged in. Revoke one to sign that device out.</small>
      </p>
      {error && <p className="error">{error}</p>}
      {sessions === null && !error && <p>Loading...</p>}
      {sessions && (
        <table>
          <thead>
            <tr>
              <th>Device</th>
              <th>IP address</th>
              <th>Logged in</th>
              <th>Last used</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>
                  {browserName(s.user_agent)}
                  {s.current && <span className="badge active"> this device</span>}
                </td>
                <td>{s.ip_address ?? "-"}</td>
                <td>{new Date(s.created_at).toLocaleString()}</td>
                <td>{new Date(s.last_used_at).toLocaleString()}</td>
                <td className="actions">
                  {!s.current && (
                    <button type="button" onClick={() => revoke(s.id)}>
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
