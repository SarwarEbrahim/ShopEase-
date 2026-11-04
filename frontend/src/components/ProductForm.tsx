import { type FormEvent, useEffect, useState } from "react"
import { createProduct, getProduct, updateProduct } from "../api"

type Props = {
  // When `id` is set the form edits that product, otherwise it creates a new one.
  id?: number
  onDone: () => void
  onCancel: () => void
}

type FormState = {
  name: string
  description: string
  category: string
  price: string
  stock: string
}

const EMPTY: FormState = { name: "", description: "", category: "", price: "", stock: "" }

export default function ProductForm({ id, onDone, onCancel }: Props) {
  const [form, setForm] = useState<FormState>(EMPTY)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(id !== undefined)
  const [saving, setSaving] = useState(false)

  // Editing: load the current values into the form.
  useEffect(() => {
    if (id === undefined) return
    let cancelled = false
    getProduct(id)
      .then((p) => {
        if (cancelled) return
        setForm({
          name: p.name,
          description: p.description ?? "",
          category: p.category,
          price: p.price,
          stock: String(p.stock),
        })
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
  }, [id])

  function setField(field: keyof FormState, value: string) {
    setForm({ ...form, [field]: value })
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError("")
    setSaving(true)
    const input = {
      name: form.name.trim(),
      description: form.description.trim() || null,
      category: form.category.trim(),
      price: form.price,
      stock: Number(form.stock),
    }
    try {
      if (id === undefined) await createProduct(input)
      else await updateProduct(id, input)
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
      setSaving(false)
    }
  }

  if (loading) return <p>Loading...</p>

  return (
    <section>
      <h2>{id === undefined ? "Add product" : "Edit product"}</h2>
      <form className="product-form" onSubmit={handleSubmit}>
        <label>
          Name
          <input
            value={form.name}
            onChange={(e) => setField("name", e.target.value)}
            maxLength={120}
            required
          />
        </label>
        <label>
          Description
          <textarea
            value={form.description}
            onChange={(e) => setField("description", e.target.value)}
            maxLength={2000}
            rows={3}
          />
        </label>
        <label>
          Category
          <input
            value={form.category}
            onChange={(e) => setField("category", e.target.value)}
            maxLength={60}
            required
          />
        </label>
        <label>
          Price
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={form.price}
            onChange={(e) => setField("price", e.target.value)}
            required
          />
        </label>
        <label>
          Stock
          <input
            type="number"
            step="1"
            min="0"
            value={form.stock}
            onChange={(e) => setField("stock", e.target.value)}
            required
          />
        </label>

        {error && <p className="error">{error}</p>}

        <div className="form-actions">
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </button>
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </section>
  )
}
