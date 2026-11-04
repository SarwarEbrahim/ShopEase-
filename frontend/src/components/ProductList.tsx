import { type FormEvent, useEffect, useState } from "react"
import { listProducts } from "../api"
import type { ProductList as ProductListData } from "../types"

const PAGE_SIZE = 10

type Props = {
  onView: (id: number) => void
}

export default function ProductList({ onView }: Props) {
  const [data, setData] = useState<ProductListData | null>(null)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(true)

  // What the user is typing, and the filters that are actually applied.
  const [qInput, setQInput] = useState("")
  const [categoryInput, setCategoryInput] = useState("")
  const [filters, setFilters] = useState({ q: "", category: "" })
  const [page, setPage] = useState(1)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError("")
    listProducts({ ...filters, page, pageSize: PAGE_SIZE })
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
    setFilters({ q: qInput.trim(), category: categoryInput.trim() })
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <section>
      <div className="toolbar">
        <h2>Products</h2>
      </div>

      <form className="search" onSubmit={handleSearch}>
        <input
          value={qInput}
          onChange={(e) => setQInput(e.target.value)}
          placeholder="Search by name"
        />
        <input
          value={categoryInput}
          onChange={(e) => setCategoryInput(e.target.value)}
          placeholder="Category"
        />
        <button type="submit">Search</button>
      </form>

      {error && <p className="error">{error}</p>}
      {loading && <p>Loading...</p>}

      {data && !loading && data.items.length === 0 && <p>No products found.</p>}

      {data && data.items.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Price</th>
              <th>Stock</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data.items.map((p) => (
              <tr key={p.id}>
                <td>{p.name}</td>
                <td>{p.category}</td>
                <td>{Number(p.price).toFixed(2)}</td>
                <td>{p.stock}</td>
                <td className="actions">
                  <button type="button" onClick={() => onView(p.id)}>
                    View
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
