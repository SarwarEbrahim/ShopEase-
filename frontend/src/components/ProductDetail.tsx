import { useEffect, useState } from "react"
import { deleteProduct, getProduct } from "../api"
import type { Product } from "../types"

type Props = {
  id: number
  onBack: () => void
  onEdit: (id: number) => void
}

export default function ProductDetail({ id, onBack, onEdit }: Props) {
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false
    setError("")
    getProduct(id)
      .then((result) => {
        if (!cancelled) setProduct(result)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Something went wrong")
      })
    return () => {
      cancelled = true
    }
  }, [id])

  async function handleDelete() {
    if (!product || !window.confirm(`Delete "${product.name}"?`)) return
    setError("")
    try {
      await deleteProduct(product.id)
      onBack()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    }
  }

  return (
    <section>
      <div className="toolbar">
        <h2>Product details</h2>
        <button type="button" onClick={onBack}>
          Back to list
        </button>
      </div>

      {error && <p className="error">{error}</p>}
      {!product && !error && <p>Loading...</p>}

      {product && (
        <>
          <dl className="details">
            <dt>Name</dt>
            <dd>{product.name}</dd>
            <dt>Description</dt>
            <dd>{product.description || "-"}</dd>
            <dt>Category</dt>
            <dd>{product.category}</dd>
            <dt>Price</dt>
            <dd>{Number(product.price).toFixed(2)}</dd>
            <dt>Stock</dt>
            <dd>{product.stock}</dd>
            <dt>Created</dt>
            <dd>{new Date(product.created_at).toLocaleString()}</dd>
            <dt>Updated</dt>
            <dd>{new Date(product.updated_at).toLocaleString()}</dd>
          </dl>

          <div className="form-actions">
            <button type="button" onClick={() => onEdit(product.id)}>
              Edit
            </button>
            <button type="button" onClick={handleDelete}>
              Delete
            </button>
          </div>
        </>
      )}
    </section>
  )
}
