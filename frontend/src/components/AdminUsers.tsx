import { type FormEvent, useEffect, useState } from "react"
import { banUser, bulkBan, bulkUnban, changeRole, downloadCsv, listUsers, unbanUser } from "../api"
import { useAuth } from "../AuthContext"
import type { Role, User, UserList } from "../types"

const PAGE_SIZE = 10

export default function AdminUsers() {
  const { user: me } = useAuth()
  const [data, setData] = useState<UserList | null>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)

  const [qInput, setQInput] = useState("")
  const [filters, setFilters] = useState({ q: "", role: "", status: "" })
  const [page, setPage] = useState(1)
  const [reloadKey, setReloadKey] = useState(0)

  // The user we are about to ban (we ask for a reason first).
  const [banTarget, setBanTarget] = useState<User | null>(null)
  const [reason, setReason] = useState("")

  // Users ticked for a bulk ban / unban, and the reason typed for a bulk ban.
  const [selected, setSelected] = useState<number[]>([])
  const [bulkReason, setBulkReason] = useState("")
  const [info, setInfo] = useState("")

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError("")
    listUsers({ ...filters, page, pageSize: PAGE_SIZE })
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
  }, [filters, page, reloadKey])

  function handleSearch(e: FormEvent) {
    e.preventDefault()
    setPage(1)
    setFilters({ ...filters, q: qInput.trim() })
  }

  function setFilter(name: "role" | "status", value: string) {
    setPage(1)
    setFilters({ ...filters, [name]: value })
  }

  // Run an admin action, then reload the list. The server decides if it is allowed.
  async function run(action: () => Promise<unknown>) {
    setError("")
    try {
      await action()
      setReloadKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  function toggle(id: number) {
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
  }

  async function runBulk(action: () => Promise<{ updated: number; skipped: number }>) {
    setError("")
    setInfo("")
    try {
      const result = await action()
      setInfo(`${result.updated} updated, ${result.skipped} skipped (yourself and admins cannot be banned).`)
      setSelected([])
      setBulkReason("")
      setReloadKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  async function handleExport() {
    setError("")
    try {
      const params: Record<string, string> = {}
      if (filters.q) params.q = filters.q
      if (filters.role) params.role = filters.role
      if (filters.status) params.is_banned = String(filters.status === "banned")
      await downloadCsv("/admin/export/users.csv", params, "users.csv")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  async function confirmBan(e: FormEvent) {
    e.preventDefault()
    if (!banTarget || !reason.trim()) return
    const target = banTarget
    setBanTarget(null)
    setReason("")
    await run(() => banUser(target.id, reason.trim()))
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <section>
      <div className="toolbar">
        <h3>Users</h3>
        <button type="button" onClick={handleExport}>
          Export CSV
        </button>
      </div>

      <form className="filters" onSubmit={handleSearch}>
        <input
          value={qInput}
          onChange={(e) => setQInput(e.target.value)}
          placeholder="Search username, email or name"
        />
        <select value={filters.role} onChange={(e) => setFilter("role", e.target.value)}>
          <option value="">All roles</option>
          <option value="user">user</option>
          <option value="admin">admin</option>
        </select>
        <select value={filters.status} onChange={(e) => setFilter("status", e.target.value)}>
          <option value="">All status</option>
          <option value="active">Active</option>
          <option value="banned">Banned</option>
        </select>
        <button type="submit">Search</button>
      </form>

      {banTarget && (
        <form className="filters ban-form" onSubmit={confirmBan}>
          <span>
            Ban <strong>{banTarget.username}</strong>:
          </span>
          <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason (required)" maxLength={300} required />
          <button type="submit">Confirm ban</button>
          <button type="button" onClick={() => setBanTarget(null)}>
            Cancel
          </button>
        </form>
      )}

      {selected.length > 0 && (
        <div className="filters">
          <span>{selected.length} selected</span>
          <input value={bulkReason} onChange={(e) => setBulkReason(e.target.value)} placeholder="Reason for bulk ban" maxLength={300} />
          <button type="button" disabled={!bulkReason.trim()} onClick={() => runBulk(() => bulkBan(selected, bulkReason.trim()))}>
            Ban selected
          </button>
          <button type="button" onClick={() => runBulk(() => bulkUnban(selected))}>
            Unban selected
          </button>
        </div>
      )}

      {info && <p className="success">{info}</p>}
      {error && <p className="error">{error}</p>}
      {loading && <p>Loading...</p>}
      {data && !loading && data.items.length === 0 && <p>No users found.</p>}

      {data && data.items.length > 0 && (
        <table>
          <thead>
            <tr>
              <th />
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.items.map((u) => {
              const isMe = u.id === me?.id
              const nextRole: Role = u.role === "admin" ? "user" : "admin"
              return (
                <tr key={u.id}>
                  <td>
                    {!isMe && (
                      <input type="checkbox" className="check" checked={selected.includes(u.id)} onChange={() => toggle(u.id)} />
                    )}
                  </td>
                  <td>{u.id}</td>
                  <td>
                    {u.username}
                    {isMe && " (you)"}
                  </td>
                  <td>{u.email}</td>
                  <td>
                    <span className={`badge ${u.role}`}>{u.role}</span>
                  </td>
                  <td>
                    <span className={`badge ${u.is_banned ? "banned" : "active"}`}>
                      {u.is_banned ? "banned" : "active"}
                    </span>
                  </td>
                  <td className="actions">
                    {/* Same rules as the server: no actions on yourself, no banning admins. */}
                    {!isMe && (
                      <button type="button" onClick={() => run(() => changeRole(u.id, nextRole))}>
                        Make {nextRole}
                      </button>
                    )}
                    {!isMe && u.is_banned && (
                      <button type="button" onClick={() => run(() => unbanUser(u.id))}>
                        Unban
                      </button>
                    )}
                    {!isMe && !u.is_banned && u.role !== "admin" && (
                      <button type="button" onClick={() => setBanTarget(u)}>
                        Ban
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}

      {data && (
        <div className="pager">
          <button type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>
            Previous
          </button>
          <span>
            Page {page} of {totalPages} ({data.total} users)
          </span>
          <button type="button" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
            Next
          </button>
        </div>
      )}
    </section>
  )
}
