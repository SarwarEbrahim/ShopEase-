import { AUTH_EXPIRED_EVENT, clearToken, getToken, setToken } from "./auth"
import type {
  AdminGroupList,
  AdminProductList,
  AuditList,
  BulkResult,
  GroupDetail,
  Group,
  GroupProduct,
  Member,
  Product,
  ProductInput,
  ProductList,
  Role,
  SecurityOverview,
  SessionInfo,
  SignupInput,
  Stats,
  TokenResponse,
  User,
  UserDetail,
  UserList,
  UserOverview,
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

// Several requests can fail with 401 at the same moment. They must share ONE refresh
// call: every refresh replaces the refresh token, so a second parallel call would
// look like a stolen (reused) token to the server.
let refreshing: Promise<boolean> | null = null

// POST /api/v1/auth/refresh. The browser sends the httpOnly refresh cookie by itself
// (JavaScript cannot read it). On success we keep the new access token.
function refreshAccessToken(): Promise<boolean> {
  if (refreshing === null) {
    refreshing = (async () => {
      try {
        const res = await fetch(`${BASE}/auth/refresh`, { method: "POST" })
        if (!res.ok) return false
        const body = (await res.json()) as TokenResponse
        setToken(body.access_token)
        return true
      } catch {
        return false
      } finally {
        refreshing = null
      }
    })()
  }
  return refreshing
}

function send(url: string, init: RequestInit | undefined, token: string | null): Promise<Response> {
  // Send the access token on every request: Authorization: Bearer <token>
  const headers = new Headers(init?.headers)
  if (token) headers.set("Authorization", `Bearer ${token}`)
  return fetch(url, { ...init, headers })
}

// fetch with the token. On a 401 it refreshes once and repeats the request; if the
// refresh fails too, the session is over: forget the token and show the login page.
async function authedFetch(path: string, init?: RequestInit): Promise<Response> {
  const token = getToken()
  let res = await send(`${BASE}${path}`, init, token)
  if (res.status === 401 && token && path !== "/auth/login") {
    if (await refreshAccessToken()) {
      res = await send(`${BASE}${path}`, init, getToken())
    }
    if (res.status === 401) {
      clearToken()
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT))
    }
  }
  return res
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await authedFetch(path, init)
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

// POST /api/v1/auth/logout. The server closes this login session (the refresh cookie
// identifies it) and removes the cookie. No access token is needed.
export async function logoutRequest(): Promise<void> {
  await fetch(`${BASE}/auth/logout`, { method: "POST" })
}

// ---- Sessions (the devices where I am logged in) ----

// GET /api/v1/auth/sessions
export function listSessions(): Promise<SessionInfo[]> {
  return request<SessionInfo[]>("/auth/sessions")
}

// DELETE /api/v1/auth/sessions/{id}
export function revokeSession(id: number): Promise<void> {
  return request<void>(`/auth/sessions/${id}`, { method: "DELETE" })
}

// GET /api/v1/admin/users/{id}/overview
export function getUserOverview(id: number): Promise<UserOverview> {
  return request<UserOverview>(`/admin/users/${id}/overview`)
}

// POST /api/v1/admin/users/{id}/revoke-sessions
export function revokeUserSessions(id: number): Promise<BulkResult> {
  return request<BulkResult>(`/admin/users/${id}/revoke-sessions`, { method: "POST" })
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
  const query = new URLSearchParams(params)
  const res = await authedFetch(`${path}?${query}`)
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

// ---- Groups ----

const JSON_HEADERS = { "Content-Type": "application/json" }

export function listGroups(): Promise<Group[]> {
  return request<Group[]>("/groups")
}

export function createGroup(name: string): Promise<Group> {
  return request<Group>("/groups", { method: "POST", headers: JSON_HEADERS, body: JSON.stringify({ name }) })
}

export function getGroup(id: number): Promise<GroupDetail> {
  return request<GroupDetail>(`/groups/${id}`)
}

export function renameGroup(id: number, name: string): Promise<Group> {
  return request<Group>(`/groups/${id}`, { method: "PATCH", headers: JSON_HEADERS, body: JSON.stringify({ name }) })
}

export function deleteGroup(id: number): Promise<void> {
  return request<void>(`/groups/${id}`, { method: "DELETE" })
}

export type Permissions = { can_create: boolean; can_edit: boolean; can_assign: boolean }

export function addMember(groupId: number, username: string, perms: Permissions): Promise<Member> {
  return request<Member>(`/groups/${groupId}/members`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ username, ...perms }),
  })
}

export function updateMember(groupId: number, userId: number, perms: Permissions): Promise<Member> {
  return request<Member>(`/groups/${groupId}/members/${userId}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(perms),
  })
}

export function removeMember(groupId: number, userId: number): Promise<void> {
  return request<void>(`/groups/${groupId}/members/${userId}`, { method: "DELETE" })
}

export function listGroupProducts(groupId: number): Promise<GroupProduct[]> {
  return request<GroupProduct[]>(`/groups/${groupId}/products`)
}

export function createGroupProduct(groupId: number, input: ProductInput): Promise<GroupProduct> {
  return request<GroupProduct>(`/groups/${groupId}/products`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(input),
  })
}

export function updateGroupProduct(groupId: number, id: number, input: ProductInput): Promise<GroupProduct> {
  return request<GroupProduct>(`/groups/${groupId}/products/${id}`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify(input),
  })
}

export function deleteGroupProduct(groupId: number, id: number): Promise<void> {
  return request<void>(`/groups/${groupId}/products/${id}`, { method: "DELETE" })
}

export function assignGroupProduct(groupId: number, id: number, userId: number | null): Promise<GroupProduct> {
  return request<GroupProduct>(`/groups/${groupId}/products/${id}/assign`, {
    method: "PUT",
    headers: JSON_HEADERS,
    body: JSON.stringify({ user_id: userId }),
  })
}

// GET /api/v1/admin/groups and DELETE /api/v1/admin/groups/{id}
export function listAdminGroups(page: number): Promise<AdminGroupList> {
  return request<AdminGroupList>(`/admin/groups?page=${page}&page_size=10`)
}

export function deleteAdminGroup(id: number): Promise<void> {
  return request<void>(`/admin/groups/${id}`, { method: "DELETE" })
}
