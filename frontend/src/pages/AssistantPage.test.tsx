import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AssistantPage from './AssistantPage'
import { api, authStore } from '../lib/api'

const renderAssistant = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <AssistantPage />
    </QueryClientProvider>
  )
}

describe('StockPilot AI Operations Assistant UI', () => {
  let mockAiConversations: ReturnType<typeof vi.spyOn>
  let mockAiConversation: ReturnType<typeof vi.spyOn>
  let mockAiConfirmAction: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    vi.restoreAllMocks()
    window.HTMLElement.prototype.scrollIntoView = vi.fn()
    window.localStorage.clear()
    authStore.setTokens({ access: 'mock-access', refresh: 'mock-refresh' })

    mockAiConversations = vi.spyOn(api, 'aiConversations').mockResolvedValue([
      {
        id: 1,
        title: 'Weekly Restock Review',
        is_active: true,
        created_at: '2026-10-25T10:00:00Z',
        updated_at: '2026-10-25T10:05:00Z',
        message_count: 2,
      },
    ])

    mockAiConversation = vi.spyOn(api, 'aiConversation' as any).mockResolvedValue({
      id: 1,
      title: 'Weekly Restock Review',
      is_active: true,
      created_at: '2026-10-25T10:00:00Z',
      updated_at: '2026-10-25T10:05:00Z',
      messages: [
        {
          id: 101,
          role: 'user',
          content: 'Which products are low in stock?',
          tool_calls: [],
          tool_results: [],
          created_at: '2026-10-25T10:00:00Z',
        },
        {
          id: 102,
          role: 'assistant',
          content: 'Widget A is below the reorder threshold.',
          tool_calls: [
            {
              id: 'call_1',
              name: 'get_low_stock_products',
              arguments: {},
            },
          ],
          tool_results: [
            {
              tool_call_id: 'call_1',
              name: 'get_low_stock_products',
              result: [
                {
                  product_id: 5,
                  product_name: 'Widget A',
                  sku: 'WGT-001',
                  on_hand: '12',
                  reorder_threshold: '20',
                },
              ],
            },
          ],
          created_at: '2026-10-25T10:01:00Z',
        },
      ],
    })

    mockAiConfirmAction = vi.spyOn(api, 'aiConfirmAction' as any).mockResolvedValue({
      status: 'success',
      action: 'receive_stock',
      message: 'Successfully executed action.',
    })

    vi.spyOn(api, 'aiPreferences').mockResolvedValue([
      { key: 'preferred_hub', value: 'Alpha Central', updated_at: '2026-10-25T09:00:00Z' },
    ])
  })

  it('renders the assistant header and active conversation', async () => {
    renderAssistant()

    expect(screen.getByText(/Grounded AI Assistant/i)).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getAllByText('Weekly Restock Review').length).toBeGreaterThanOrEqual(1)
    })
    expect(await screen.findByText('Which products are low in stock?')).toBeInTheDocument()
    expect(screen.getByText('Widget A is below the reorder threshold.')).toBeInTheDocument()
    expect(screen.getByText('get_low_stock_products')).toBeInTheDocument()
  })

  it('renders confirmation card for proposed write action', async () => {
    mockAiConversations.mockResolvedValue([
      { id: 2, title: 'Receive Stock Proposal', is_active: true, created_at: '2026-10-25', updated_at: '2026-10-25' },
    ])
    mockAiConversation.mockResolvedValue({
      id: 2,
      title: 'Receive Stock Proposal',
      is_active: true,
      created_at: '2026-10-25T10:10:00Z',
      updated_at: '2026-10-25T10:11:00Z',
      messages: [
        {
          id: 201,
          role: 'user',
          content: 'Receive 50 units of Precision Sensor into Alpha Central',
          tool_calls: [],
          tool_results: [],
          created_at: '2026-10-25T10:10:00Z',
        },
        {
          id: 202,
          role: 'assistant',
          content: 'I have prepared a confirmation proposal for your review.',
          tool_calls: [{ id: 'tc_write', name: 'receive_stock', arguments: {} }],
          tool_results: [
            {
              tool_call_id: 'tc_write',
              name: 'receive_stock',
              result: {
                requires_confirmation: true,
                action: 'receive_stock',
                operation_label: 'Receive Stock',
                parameters: {
                  product_id: 10,
                  product_name: 'Precision Sensor',
                  product_sku: 'SEN-001',
                  hub_id: 1,
                  hub_name: 'Alpha Central',
                  quantity: '50',
                  reason: 'Arrival inspection passed',
                },
                current_state: {
                  on_hand: '10',
                  available: '10',
                },
                proposed_action: 'Receive 50 units of Precision Sensor into Alpha Central',
                message: 'Action validated.',
              },
            },
          ],
          created_at: '2026-10-25T10:11:00Z',
        },
      ],
    })

    renderAssistant()

    await waitFor(() => {
      expect(screen.getByText('Receive Stock')).toBeInTheDocument()
    })
    expect(screen.getByText(/Awaiting Confirmation/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Precision Sensor/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('50 units')).toBeInTheDocument()
    expect(screen.getByText(/On-hand: 10/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Confirm & Execute/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument()
  })

  it('confirms and executes proposed write action via server API', async () => {
    mockAiConfirmAction.mockResolvedValue({
      status: 'success',
      action: 'receive_stock',
      message: 'Successfully received 50 units of Precision Sensor.',
    })

    mockAiConversations.mockResolvedValue([
      { id: 2, title: 'Receive Stock Proposal', is_active: true, created_at: '2026-10-25', updated_at: '2026-10-25' },
    ])
    mockAiConversation.mockResolvedValue({
      id: 2,
      title: 'Receive Stock Proposal',
      is_active: true,
      created_at: '2026-10-25T10:10:00Z',
      updated_at: '2026-10-25T10:11:00Z',
      messages: [
        {
          id: 202,
          role: 'assistant',
          content: 'Proposal ready.',
          tool_calls: [],
          tool_results: [
            {
              tool_call_id: 'tc_write',
              name: 'receive_stock',
              result: {
                requires_confirmation: true,
                action: 'receive_stock',
                operation_label: 'Receive Stock',
                parameters: {
                  product_id: 10,
                  product_name: 'Precision Sensor',
                  quantity: '50',
                },
                proposed_action: 'Receive 50 units',
                message: 'Confirm to execute',
              },
            },
          ],
          created_at: '2026-10-25T10:11:00Z',
        },
      ],
    })

    renderAssistant()

    const confirmBtn = await screen.findByRole('button', { name: /Confirm & Execute/i })
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(mockAiConfirmAction).toHaveBeenCalledWith({
        action: 'receive_stock',
        parameters: { product_id: 10, product_name: 'Precision Sensor', quantity: '50' },
      })
    })

    await waitFor(() => {
      expect(screen.getByText('Successfully received 50 units of Precision Sensor.')).toBeInTheDocument()
    })
  })

  it('cancels proposed action without calling confirmation API', async () => {
    mockAiConversations.mockResolvedValue([
      { id: 2, title: 'Cancel Test', is_active: true, created_at: '2026-10-25', updated_at: '2026-10-25' },
    ])
    mockAiConversation.mockResolvedValue({
      id: 2,
      title: 'Cancel Test',
      is_active: true,
      created_at: '2026-10-25T10:10:00Z',
      updated_at: '2026-10-25T10:11:00Z',
      messages: [
        {
          id: 202,
          role: 'assistant',
          content: 'Proposal ready.',
          tool_calls: [],
          tool_results: [
            {
              tool_call_id: 'tc_write',
              name: 'adjust_stock',
              result: {
                requires_confirmation: true,
                action: 'adjust_stock',
                operation_label: 'Adjust Stock',
                parameters: { product_id: 10, quantity: '-5' },
                proposed_action: 'Adjust by -5',
                message: 'Confirm to execute',
              },
            },
          ],
          created_at: '2026-10-25T10:11:00Z',
        },
      ],
    })

    renderAssistant()

    const cancelBtn = await screen.findByRole('button', { name: /Cancel/i })
    fireEvent.click(cancelBtn)

    expect(mockAiConfirmAction).not.toHaveBeenCalled()
    await waitFor(() => {
      expect(screen.getByText(/Action cancelled\. No changes were made to inventory\./i)).toBeInTheDocument()
    })
  })

  it('renders unauthenticated state when not signed in', () => {
    authStore.clear()
    renderAssistant()

    expect(screen.getByText(/Sign in to use StockPilot AI Operations Assistant/i)).toBeInTheDocument()
  })
})
