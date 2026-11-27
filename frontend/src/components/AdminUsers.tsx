import { type FormEvent, useEffect, useState } from "react"
import { banUser, changeRole, listUsers, unbanUser } from "../api"
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
        <h2>Users</h2>
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

      {error && <p className="error">{error}</p>}
      {loading && <p>Loading...</p>}
      {data && !loading && data.items.length === 0 && <p>No users found.</p>}

      {data && data.items.length > 0 && (
        <table>
          <thead>
            <tr>
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
