export type Organization = {
  id: number
  name: string
  slug: string
  timezone: string
  currency: string
  role: string
}

export type UserIdentity = {
  id: number
  email: string
  first_name: string
  last_name: string
  memberships: Array<{ id: number; organization: number; organization_name: string; organization_slug: string; role: string; is_active: boolean }>
  active_organization: { id: number; name: string; slug: string } | null
}

export type AuthResponse = {
  access: string
  refresh: string
  user: UserIdentity
}

export type DashboardSummary = {
  active_products: number
  stock_units: string
  inventory_value: string
  low_stock_products: number
  out_of_stock_products: number
  active_hubs: number
  data_status: 'empty' | 'live'
}

export type ProductRecord = { id: number; name: string; sku: string; cost_price: string; unit_of_measure: string; is_active: boolean; balances: Array<{ product_name: string; hub_name: string; on_hand: string; available: string }> }
export type HubRecord = { id: number; name: string; code: string; city: string; is_active: boolean }
export type TransferRecord = { id: number; product_name: string; source_hub_name: string; destination_hub_name: string; quantity: string; status: string; created_at: string }
export type RestockRecord = { id: number; product_name: string; hub_name: string; supplier_name: string | null; quantity: string; status: string; created_at: string }

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
const ACCESS_KEY = 'stockpilot.access'
const REFRESH_KEY = 'stockpilot.refresh'

export const authStore = {
  get access() {
    return window.localStorage.getItem(ACCESS_KEY)
  },
  setTokens(tokens: Pick<AuthResponse, 'access' | 'refresh'>) {
    window.localStorage.setItem(ACCESS_KEY, tokens.access)
    window.localStorage.setItem(REFRESH_KEY, tokens.refresh)
  },
  clear() {
    window.localStorage.removeItem(ACCESS_KEY)
    window.localStorage.removeItem(REFRESH_KEY)
  },
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Content-Type', 'application/json')
  if (authStore.access) headers.set('Authorization', `Bearer ${authStore.access}`)
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (response.status === 401 && retry && window.localStorage.getItem(REFRESH_KEY)) {
    const refreshResponse = await fetch(`${API_BASE}/auth/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: window.localStorage.getItem(REFRESH_KEY) }),
    })
    if (refreshResponse.ok) {
      const refreshed = (await refreshResponse.json()) as { access: string; refresh?: string }
      authStore.setTokens({ access: refreshed.access, refresh: refreshed.refresh ?? window.localStorage.getItem(REFRESH_KEY)! })
      return request<T>(path, init, false)
    }
    authStore.clear()
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail ?? `Request failed (${response.status})`)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  login: async (email: string, password: string) => {
    const result = await request<AuthResponse>('/auth/login/', { method: 'POST', body: JSON.stringify({ email, password }) }, false)
    authStore.setTokens(result)
    return result
  },
  register: (payload: { email: string; password: string; first_name: string; organization_name: string }) => request<{ user: UserIdentity }>('/auth/register/', { method: 'POST', body: JSON.stringify(payload) }, false),
  me: () => request<UserIdentity>('/auth/me/'),
  dashboard: () => request<DashboardSummary>('/dashboard/summary/'),
  products: () => request<ProductRecord[]>('/products/'),
  hubs: () => request<HubRecord[]>('/hubs/'),
  transfers: () => request<TransferRecord[]>('/transfers/'),
  restocks: () => request<RestockRecord[]>('/restock-requests/'),
  organizations: () => request<Organization[]>('/organizations/'),
  logout: async () => {
    const refresh = window.localStorage.getItem(REFRESH_KEY)
    if (refresh && authStore.access) await request<void>('/auth/logout/', { method: 'POST', body: JSON.stringify({ refresh }) }, false).catch(() => undefined)
    authStore.clear()
  },
}
