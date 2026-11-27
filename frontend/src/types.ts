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
