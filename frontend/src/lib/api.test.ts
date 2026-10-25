import { beforeEach, describe, expect, it } from 'vitest'

import { authStore } from './api'

describe('authStore', () => {
  beforeEach(() => window.localStorage.clear())

  it('persists and clears access tokens', () => {
    authStore.setTokens({ access: 'access-token', refresh: 'refresh-token' })
    expect(authStore.access).toBe('access-token')
    authStore.clear()
    expect(authStore.access).toBeNull()
  })
})
