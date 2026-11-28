import { AUTH_EXPIRED_EVENT, clearToken, getToken } from "./auth"
import type {
  AdminProductList,
  AuditList,
  BulkResult,
  Product,
  ProductInput,
  ProductList,
  Role,
  SecurityOverview,
  SignupInput,
  Stats,
  TokenResponse,
  User,
  UserDetail,
  UserList,
} from "./types"

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
  // Send the access token on every request: Authorization: Bearer <token>
  const token = getToken()
  const headers = new Headers(init?.headers)
  if (token) headers.set("Authorization", `Bearer ${token}`)

  const res = await fetch(`${BASE}${path}`, { ...init, headers })

  // The server rejected our token: forget it and tell the app to show the login page.
  if (res.status === 401 && token && path !== "/auth/login") {
    clearToken()
    window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
  }
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

// Create: POST /api/v1/products
export function createProduct(input: ProductInput): Promise<Product> {
  return request<Product>("/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  })
}

// Update: PUT /api/v1/products/{id}
export function updateProduct(id: number, input: ProductInput): Promise<Product> {
  return request<Product>(`/products/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  })
}

// Delete: DELETE /api/v1/products/{id}
export function deleteProduct(id: number): Promise<void> {
  return request<void>(`/products/${id}`, { method: "DELETE" })
}

// ---- Auth ----

// POST /api/v1/auth/signup
export function signup(input: SignupInput): Promise<User> {
  return request<User>("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  })
}

// POST /api/v1/auth/login
export function login(username: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  })
}

// GET /api/v1/auth/me (needs a valid token)
export function getMe(): Promise<User> {
  return request<User>("/auth/me")
}

// ---- Admin (the server only allows the admin role) ----

export type UserListParams = {
  q: string
  role: string
  status: string // "" | "active" | "banned"
  page: number
  pageSize: number
}

// GET /api/v1/admin/users
export function listUsers({ q, role, status, page, pageSize }: UserListParams): Promise<UserList> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
  if (q) params.set("q", q)
  if (role) params.set("role", role)
  if (status) params.set("is_banned", String(status === "banned"))
  return request<UserList>(`/admin/users?${params}`)
}

// POST /api/v1/admin/users/{id}/ban
export function banUser(id: number, reason: string): Promise<UserDetail> {
  return request<UserDetail>(`/admin/users/${id}/ban`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  })
}

// POST /api/v1/admin/users/{id}/unban
export function unbanUser(id: number): Promise<UserDetail> {
  return request<UserDetail>(`/admin/users/${id}/unban`, { method: "POST" })
}

// PATCH /api/v1/admin/users/{id}/role
export function changeRole(id: number, role: Role): Promise<UserDetail> {
  return request<UserDetail>(`/admin/users/${id}/role`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role }),
  })
}

// ---- Logout, profile and password ----

// POST /api/v1/auth/logout (records the logout in the activity log)
export function logoutRequest(): Promise<void> {
  return request<void>("/auth/logout", { method: "POST" })
}

// PATCH /api/v1/auth/me
export function updateProfile(input: { full_name?: string; email?: string }): Promise<User> {
  return request<User>("/auth/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  })
}

// POST /api/v1/auth/change-password
export function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return request<void>("/auth/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  })
}

// ---- More admin endpoints ----

// GET /api/v1/admin/stats
export function getStats(): Promise<Stats> {
  return request<Stats>("/admin/stats")
}

// GET /api/v1/admin/security
export function getSecurity(): Promise<SecurityOverview> {
  return request<SecurityOverview>("/admin/security")
}

// GET /api/v1/admin/audit
export function listAudit(p: { event: string; q: string; page: number; pageSize: number }): Promise<AuditList> {
  const params = new URLSearchParams({ page: String(p.page), page_size: String(p.pageSize) })
  if (p.event) params.set("event", p.event)
  if (p.q) params.set("q", p.q)
  return request<AuditList>(`/admin/audit?${params}`)
}

// GET /api/v1/admin/products
export function listAdminProducts(p: { q: string; page: number; pageSize: number }): Promise<AdminProductList> {
  const params = new URLSearchParams({ page: String(p.page), page_size: String(p.pageSize) })
  if (p.q) params.set("q", p.q)
  return request<AdminProductList>(`/admin/products?${params}`)
}

// DELETE /api/v1/admin/products/{id}
export function deleteAdminProduct(id: number): Promise<void> {
  return request<void>(`/admin/products/${id}`, { method: "DELETE" })
}

// POST /api/v1/admin/products/bulk-delete
export function bulkDeleteProducts(ids: number[]): Promise<BulkResult> {
  return request<BulkResult>("/admin/products/bulk-delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  })
}

// POST /api/v1/admin/users/bulk-ban and bulk-unban
export function bulkBan(ids: number[], reason: string): Promise<BulkResult> {
  return request<BulkResult>("/admin/users/bulk-ban", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids, reason }),
  })
}

export function bulkUnban(ids: number[]): Promise<BulkResult> {
  return request<BulkResult>("/admin/users/bulk-unban", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  })
}

// CSV export. A plain link cannot send the Authorization header, so we fetch the
// file with the token and let the browser save it.
export async function downloadCsv(
  path: string,
  params: Record<string, string>,
  filename: string,
): Promise<void> {
  const token = getToken()
  const query = new URLSearchParams(params)
  const res = await fetch(`${BASE}${path}?${query}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) throw new Error(await readError(res))
  const url = URL.createObjectURL(await res.blob())
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
