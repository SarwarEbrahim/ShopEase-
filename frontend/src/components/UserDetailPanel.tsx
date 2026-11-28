import { useCallback, useEffect, useState } from "react"
import { getUserOverview, revokeUserSessions } from "../api"
import type { UserOverview } from "../types"
import { browserName } from "./SessionsList"

type Props = { userId: number; onClose: () => void }

// Admin user detail: profile, open sessions (with "sign out everywhere"), latest activity.
export default function UserDetailPanel({ userId, onClose }: Props) {
  const [data, setData] = useState<UserOverview | null>(null)
  const [error, setError] = useState("")

  const load = useCallback(() => {
    setError("")
    getUserOverview(userId)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Something went wrong"))
  }, [userId])

  useEffect(() => {
    setData(null)
    load()
  }, [load])

  async function signOutEverywhere() {
    setError("")
    try {
      await revokeUserSessions(userId)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  return (
    <div className="card" style={{ marginBottom: "1rem" }}>
      <div className="toolbar">
        <h3>User detail</h3>
        <button type="button" onClick={onClose}>
          Close
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {!data && !error && <p>Loading...</p>}
      {data && (
        <>
          <p>
            <strong>{data.user.username}</strong> ({data.user.full_name}), {data.user.email}
            <br />
            Role: {data.user.role}, status:{" "}
            <span className={`badge ${data.user.is_banned ? "banned" : "active"}`}>
              {data.user.is_banned ? "banned" : "active"}
            </span>
            {data.user.ban_reason && <> (reason: {data.user.ban_reason})</>}
            <br />
            Joined {new Date(data.user.created_at).toLocaleString()}. Products: {data.product_count}, groups owned:{" "}
            {data.group_count}.
          </p>

          <div className="toolbar">
            <h4>Open sessions ({data.sessions.length})</h4>
            {data.sessions.length > 0 && (
              <button type="button" onClick={signOutEverywhere}>
                Sign out everywhere
              </button>
            )}
          </div>
          {data.sessions.length === 0 ? (
            <p>No open sessions.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Device</th>
                  <th>IP address</th>
                  <th>Last used</th>
                </tr>
              </thead>
              <tbody>
                {data.sessions.map((s) => (
                  <tr key={s.id}>
                    <td>{browserName(s.user_agent)}</td>
                    <td>{s.ip_address ?? "-"}</td>
                    <td>{new Date(s.last_used_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <h4>Recent activity</h4>
          {data.recent_activity.length === 0 ? (
            <p>No activity yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Event</th>
                  <th>IP address</th>
                  <th>Detail</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_activity.map((a) => (
                  <tr key={a.id}>
                    <td>{new Date(a.created_at).toLocaleString()}</td>
                    <td>{a.event}</td>
                    <td>{a.ip_address ?? "-"}</td>
                    <td>{a.detail ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </div>
  )
}
