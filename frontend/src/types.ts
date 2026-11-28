// Price is a string because the API sends decimals as strings (for example "12.50").
export type Product = {
  id: number
  name: string
  description: string | null
  price: string
  stock: number
  category: string
  created_at: string
  updated_at: string
}

export type ProductList = {
  items: Product[]
  total: number
  page: number
  page_size: number
}

export type ProductInput = {
  name: string
  description: string | null
  price: string
  stock: number
  category: string
}

export type Role = "user" | "admin"

export type User = {
  id: number
  username: string
  email: string
  full_name: string
  role: Role
  is_banned: boolean
  created_at: string
}

// The admin detail view also shows the ban reason and the last update.
export type UserDetail = User & {
  ban_reason: string | null
  updated_at: string
}

export type TokenResponse = {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export type SignupInput = {
  username: string
  email: string
  full_name: string
  password: string
}

export type UserList = {
  items: User[]
  total: number
  page: number
  page_size: number
}

export type Stats = {
  total_users: number
  banned_users: number
  admins: number
  total_products: number
  new_users_7d: number
  new_products_7d: number
  failed_logins_24h: number
}

export type AuditEntry = {
  id: number
  event: string
  user_id: number | null
  username: string | null
  ip_address: string | null
  user_agent: string | null
  detail: string | null
  created_at: string
}

export type AuditList = {
  items: AuditEntry[]
  total: number
  page: number
  page_size: number
}

export type CountItem = { key: string; count: number }

export type SecurityOverview = {
  by_ip: CountItem[]
  by_account: CountItem[]
}

export type AdminProduct = Product & {
  owner_id: number | null
  owner_username: string | null
}

export type AdminProductList = {
  items: AdminProduct[]
  total: number
  page: number
  page_size: number
}

export type BulkResult = { updated: number; skipped: number }
