import { type FormEvent, useEffect, useState } from "react"
import { bulkDeleteProducts, deleteAdminProduct, downloadCsv, listAdminProducts } from "../api"
import type { AdminProductList } from "../types"

const PAGE_SIZE = 10

export default function AdminProducts() {
  const [data, setData] = useState<AdminProductList | null>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)
  const [qInput, setQInput] = useState("")
  const [q, setQ] = useState("")
  const [page, setPage] = useState(1)
  const [reloadKey, setReloadKey] = useState(0)
  const [selected, setSelected] = useState<number[]>([])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError("")
    listAdminProducts({ q, page, pageSize: PAGE_SIZE })
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
  }, [q, page, reloadKey])

  function handleSearch(e: FormEvent) {
    e.preventDefault()
    setPage(1)
    setQ(qInput.trim())
  }

  function toggle(id: number) {
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]))
  }

  async function run(action: () => Promise<unknown>) {
    setError("")
    try {
      await action()
      setSelected([])
      setReloadKey((k) => k + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <section>
      <div className="toolbar">
        <h3>All products (moderation)</h3>
        <button
          type="button"
          onClick={() =>
            run(() => downloadCsv("/admin/export/products.csv", q ? { q } : {}, "products.csv"))
          }
        >
          Export CSV
        </button>
      </div>

      <form className="filters" onSubmit={handleSearch}>
        <input value={qInput} onChange={(e) => setQInput(e.target.value)} placeholder="Search by name" />
        <button type="submit">Search</button>
        <button
          type="button"
          disabled={selected.length === 0}
          onClick={() => {
            if (window.confirm(`Delete ${selected.length} product(s)?`)) run(() => bulkDeleteProducts(selected))
          }}
        >
          Delete selected ({selected.length})
        </button>
      </form>

      {error && <p className="error">{error}</p>}
      {loading && <p>Loading...</p>}
      {data && !loading && data.items.length === 0 && <p>No products found.</p>}

      {data && data.items.length > 0 && (
        <table>
          <thead>
            <tr>
              <th />
              <th>Name</th>
              <th>Category</th>
              <th>Price</th>
              <th>Owner</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.items.map((p) => (
              <tr key={p.id}>
                <td>
                  <input
                    type="checkbox"
                    className="check"
                    checked={selected.includes(p.id)}
                    onChange={() => toggle(p.id)}
                  />
                </td>
                <td>{p.name}</td>
                <td>{p.category}</td>
                <td>{Number(p.price).toFixed(2)}</td>
                <td>{p.owner_username ?? "-"}</td>
                <td className="actions">
                  <button
                    type="button"
                    onClick={() => {
                      if (window.confirm(`Delete "${p.name}"?`)) run(() => deleteAdminProduct(p.id))
                    }}
                  >
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
            Page {page} of {totalPages} ({data.total} products)
          </span>
          <button type="button" disabled={page >= totalPages} onClick={() => setPage(page + 1)}>
            Next
          </button>
        </div>
      )}
    </section>
  )
}
