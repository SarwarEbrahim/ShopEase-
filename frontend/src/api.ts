import type { Product, ProductList } from "./types"

const BASE = "/api/v1"

// Turn an error response into a readable message.
async function readError(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.message === "string") return body.message
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((d: { loc: (string | number)[]; msg: string }) => `${d.loc.slice(1).join(".")}: ${d.msg}`)
        .join("; ")
    }
  } catch {
    // The body was not JSON; fall through to the generic message.
  }
  return `Request failed (${res.status})`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) throw new Error(await readError(res))
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export type ListParams = {
  q: string
  category: string
  page: number
  pageSize: number
}

// Read list: GET /api/v1/products
export function listProducts({ q, category, page, pageSize }: ListParams): Promise<ProductList> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (q) params.set("q", q)
  if (category) params.set("category", category)
  return request<ProductList>(`/products?${params}`)
}

// Read single: GET /api/v1/products/{id}
export function getProduct(id: number): Promise<Product> {
  return request<Product>(`/products/${id}`)
}
