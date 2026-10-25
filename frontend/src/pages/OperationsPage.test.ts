import { beforeEach, describe, expect, it, vi } from 'vitest'

import { api, authStore } from '../lib/api'
import { permissionByMode, productSchema } from '../lib/mutationContracts'

beforeEach(() => {
  vi.restoreAllMocks()
  window.localStorage.clear()
  authStore.setTokens({ access: 'test-access', refresh: 'test-refresh' })
})

describe('mutation contracts', () => {
  it('rejects an invalid product before any API call', () => {
    const result = productSchema.safeParse({ name: 'x', sku: '', unit_of_measure: '', cost_price: -1, reorder_threshold: 0, target_stock_level: 0 })
    expect(result.success).toBe(false)
    if (!result.success) expect(result.error.issues.map((issue) => issue.path[0])).toEqual(expect.arrayContaining(['name', 'sku', 'unit_of_measure', 'cost_price']))
  })

  it('maps each resource mutation to an explicit server capability', () => {
    expect(permissionByMode.products).toBe('inventory.products.create')
    expect(permissionByMode.hubs).toBe('hubs.manage')
    expect(permissionByMode.transfers).toBe('transfers.initiate')
  })

  it('sends a validated product creation through the typed client', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ id: 7, name: 'Widget', sku: 'W-7' }), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    const result = await api.createProduct({ name: 'Widget', sku: 'W-7', unit_of_measure: 'unit', cost_price: 10, reorder_threshold: 2, target_stock_level: 5 })
    expect(result.id).toBe(7)
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/products/', expect.objectContaining({ method: 'POST', body: expect.stringContaining('W-7') }))
  })

  it('surfaces a Django mutation error instead of pretending success', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ detail: 'SKU already exists in this organization.' }), { status: 400, headers: { 'Content-Type': 'application/json' } }))
    await expect(api.createProduct({ name: 'Duplicate', sku: 'DUP-1' })).rejects.toThrow('SKU already exists in this organization.')
  })
})
