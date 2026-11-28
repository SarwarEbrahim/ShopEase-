import { type FormEvent, useEffect, useState } from "react"
import { downloadCsv, listAudit } from "../api"
import type { AuditList } from "../types"

const PAGE_SIZE = 15

const EVENTS = [
  "login",
  "login_failed",
  "login_blocked",
  "logout",
  "password_change",
  "password_change_failed",
  "profile_update",
  "role_change",
  "ban",
  "unban",
  "product_delete",
  "export",
]

// A short browser name from the User-Agent text.
function browserName(ua: string | null): string {
  if (!ua) return "-"
  if (ua.includes("Edg/")) return "Edge"
  if (ua.includes("Chrome/")) return "Chrome"
  if (ua.includes("Firefox/")) return "Firefox"
  if (ua.includes("Safari/")) return "Safari"
  return ua.slice(0, 30)
}

export default function AdminAudit() {
  const [data, setData] = useState<AuditList | null>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const [qInput, setQInput] = useState("")
  const [filters, setFilters] = useState({ event: "", q: "" })
  const [page, setPage] = useState(1)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError("")
    listAudit({ ...filters, page, pageSize: PAGE_SIZE })
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Something went wrong")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [filters, page])

  function handleSearch(e: FormEvent) {
    e.preventDefault()
    setPage(1)
    setFilters({ ...filters, q: qInput.trim() })
  }

  async function handleExport() {
    setError("")
    try {
      const params: Record<string, string> = {}
      if (filters.event) params.event = filters.event
      if (filters.q) params.q = filters.q
      await downloadCsv("/admin/export/audit.csv", params, "activity.csv")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <section>
      <div className="toolbar">
        <h3>Activity log</h3>
        <button type="button" onClick={handleExport}>
          Export CSV
        </button>
      </div>

      <form className="filters" onSubmit={handleSearch}>
        <input value={qInput} onChange={(e) => setQInput(e.target.value)} placeholder="Search user, IP or detail" />
        <select
          value={filters.event}
          onChange={(e) => {
            setPage(1)
            setFilters({ ...filters, event: e.target.value })
          }}
        >
          <option value="">All events</option>
          {EVENTS.map((ev) => (
            <option key={ev} value={ev}>
              {ev}
            </option>
          ))}
        </select>
        <button type="submit">Search</button>
      </form>

      {error && <p className="error">{error}</p>}
      {loading && <p>Loading...</p>}
      {data && !loading && data.items.length === 0 && <p>No activity found.</p>}

      {data && data.items.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Event</th>
              <th>User</th>
              <th>IP</th>
              <th>Browser</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((l) => (
              <tr key={l.id}>
                <td>{new Date(l.created_at).toLocaleString()}</td>
                <td>{l.event}</td>
                <td>{l.username ?? "-"}</td>
                <td>{l.ip_address ?? "-"}</td>
                <td>{browserName(l.user_agent)}</td>
                <td>{l.detail ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {data && (
        <div className="pager">
          <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </button>
          <span>
            Page {page} of {totalPages} ({data.total} events)
          </span>
          <button type="button" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
            Next
          </button>
        </div>
      )}
    </section>
  )
}
