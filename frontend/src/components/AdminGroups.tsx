import { useEffect, useState } from "react"
import { deleteAdminGroup, listAdminGroups } from "../api"
import type { AdminGroupList } from "../types"

export default function AdminGroups() {
  const [data, setData] = useState<AdminGroupList | null>(null)
  const [error, setError] = useState("")
  const [page, setPage] = useState(1)
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    listAdminGroups(page)
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Something went wrong")
      })
    return () => {
      cancelled = true
    }
  }, [page, reloadKey])

  async function handleDelete(id: number, name: string) {
    if (!window.confirm(`Delete group "${name}" with its members and products?`)) return
    setError("")
    try {
      await deleteAdminGroup(id)
      setReloadKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <section>
      <h3>All groups (moderation)</h3>
      {error && <p className="error">{error}</p>}
      {data === null && !error && <p>Loading...</p>}
      {data && data.items.length === 0 && <p>No groups yet.</p>}
      {data && data.items.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Owner</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.items.map((g) => (
              <tr key={g.id}>
                <td>{g.id}</td>
                <td>{g.name}</td>
                <td>{g.owner_username ?? "-"}</td>
                <td className="actions">
                  <button type="button" onClick={() => handleDelete(g.id, g.name)}>
                    Delete
                  </button>
                </td>
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
            Page {page} of {totalPages} ({data.total} groups)
          </span>
          <button type="button" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
            Next
          </button>
        </div>
      )}
    </section>
  )
}
