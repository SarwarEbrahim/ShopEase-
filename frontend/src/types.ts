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
