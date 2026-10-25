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
export type CategoryRecord = { id: number; name: string; slug: string; description: string; created_at: string }
export type HubRecord = { id: number; name: string; code: string; city: string; is_active: boolean }
export type SupplierRecord = { id: number; name: string; email: string; phone: string; website: string; notes: string; is_active: boolean; products: Array<{ id: number; product: number; supplier_sku: string; lead_time_days: number; last_cost: string | null; is_preferred: boolean }> }
export type TransferRecord = { id: number; product_name: string; source_hub_name: string; destination_hub_name: string; quantity: string; status: string; created_at: string }
export type RestockRecord = { id: number; product_name: string; hub_name: string; supplier_name: string | null; quantity: string; status: string; created_at: string }
export type MemberRecord = { id: number; user_id: number; email: string; first_name: string; last_name: string; role: string; role_label: string; is_active: boolean; joined_at: string; last_seen_at: string | null }
export type InvitationRecord = { id: number; email: string; role: string; role_label: string; status: 'pending' | 'accepted' | 'canceled' | 'expired'; expires_at: string; accepted_at: string | null; created_at: string; invited_by_name: string; invitation_token?: string }
export type PermissionMatrixRecord = { role: string; permissions: string[] }

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
  organizations: () => request<Organization[]>('/organizations/'),
  switchOrganization: (organizationId: number) => request<Organization>('/organizations/active/', { method: 'POST', body: JSON.stringify({ organization_id: organizationId }) }),
  products: () => request<ProductRecord[]>('/products/'),
  product: (id: number) => request<ProductRecord>(`/products/${id}/`),
  createProduct: (payload: Record<string, unknown>) => request<ProductRecord>('/products/', { method: 'POST', body: JSON.stringify(payload) }),
  updateProduct: (id: number, payload: Record<string, unknown>) => request<ProductRecord>(`/products/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }),
  archiveProduct: (id: number) => request<void>(`/products/${id}/`, { method: 'DELETE' }),
  categories: () => request<CategoryRecord[]>('/categories/'),
  createCategory: (payload: Record<string, unknown>) => request<CategoryRecord>('/categories/', { method: 'POST', body: JSON.stringify(payload) }),
  updateCategory: (id: number, payload: Record<string, unknown>) => request<CategoryRecord>(`/categories/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }),
  archiveCategory: (id: number) => request<void>(`/categories/${id}/`, { method: 'DELETE' }),
  hubs: () => request<HubRecord[]>('/hubs/'),
  createHub: (payload: Record<string, unknown>) => request<HubRecord>('/hubs/', { method: 'POST', body: JSON.stringify(payload) }),
  updateHub: (id: number, payload: Record<string, unknown>) => request<HubRecord>(`/hubs/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }),
  suppliers: () => request<SupplierRecord[]>('/suppliers/'),
  createSupplier: (payload: Record<string, unknown>) => request<SupplierRecord>('/suppliers/', { method: 'POST', body: JSON.stringify(payload) }),
  updateSupplier: (id: number, payload: Record<string, unknown>) => request<SupplierRecord>(`/suppliers/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }),
  stock: (productId: number, payload: Record<string, unknown>) => request<{ movement_id: number; on_hand: string; available: string }>(`/products/${productId}/stock/`, { method: 'POST', body: JSON.stringify(payload) }),
  transfers: () => request<TransferRecord[]>('/transfers/'),
  createTransfer: (payload: Record<string, unknown>) => request<TransferRecord>('/transfers/', { method: 'POST', body: JSON.stringify(payload) }),
  updateTransfer: (id: number, payload: Record<string, unknown>) => request<TransferRecord>(`/transfers/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }),
  transitionTransfer: (id: number, action: string) => request<TransferRecord>(`/transfers/${id}/${action}/`, { method: 'POST', body: JSON.stringify({}) }),
  restocks: () => request<RestockRecord[]>('/restock-requests/'),
  createRestock: (payload: Record<string, unknown>) => request<RestockRecord>('/restock-requests/', { method: 'POST', body: JSON.stringify(payload) }),
  updateRestock: (id: number, payload: Record<string, unknown>) => request<RestockRecord>(`/restock-requests/${id}/`, { method: 'PATCH', body: JSON.stringify(payload) }),
  transitionRestock: (id: number, action: string) => request<RestockRecord>(`/restock-requests/${id}/${action}/`, { method: 'POST', body: JSON.stringify({}) }),
  members: () => request<MemberRecord[]>('/organizations/members/'),
  invitations: () => request<InvitationRecord[]>('/organizations/invitations/'),
  permissions: () => request<PermissionMatrixRecord[]>('/organizations/permissions/'),
  inviteMember: (payload: { email: string; role: string }) => request<InvitationRecord>('/organizations/invitations/', { method: 'POST', body: JSON.stringify(payload) }),
  updateMemberRole: (id: number, role: string) => request<MemberRecord>(`/organizations/members/${id}/`, { method: 'PATCH', body: JSON.stringify({ role }) }),
  removeMember: (id: number) => request<void>(`/organizations/members/${id}/`, { method: 'DELETE' }),
  cancelInvitation: (id: number) => request<InvitationRecord>(`/organizations/invitations/${id}/cancel/`, { method: 'POST' }),
  resendInvitation: (id: number) => request<InvitationRecord>(`/organizations/invitations/${id}/resend/`, { method: 'POST' }),
  logout: async () => {
    const refresh = window.localStorage.getItem(REFRESH_KEY)
    if (refresh && authStore.access) await request<void>('/auth/logout/', { method: 'POST', body: JSON.stringify({ refresh }) }, false).catch(() => undefined)
    authStore.clear()
  },
}
