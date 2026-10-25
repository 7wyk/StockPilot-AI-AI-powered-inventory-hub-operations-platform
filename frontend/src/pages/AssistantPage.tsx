import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Sparkles,
  ArrowRight,
  Plus,
  Trash2,
  Check,
  X,
  AlertCircle,
  Loader2,
  CheckCircle2,
  Warehouse,
  Package,
  Truck,
  MessageSquare,
  Database,
  Sliders,
} from 'lucide-react'
import { api, authStore, type AIMessage, type AIWriteProposal } from '../lib/api'

const QUICK_PROMPTS = [
  { label: 'Current inventory value', prompt: 'What is my current inventory value?' },
  { label: 'Low stock products', prompt: 'Which products are low in stock?' },
  { label: 'Stockouts review', prompt: 'Which products are out of stock?' },
  { label: 'Hub inventory breakdown', prompt: 'Which hub has the most inventory?' },
  { label: 'Recent movements', prompt: 'Show me recent inventory movements.' },
  { label: 'Restock recommendations', prompt: 'Which products should I restock?' },
  { label: 'Inventory health report', prompt: 'Generate an inventory health report.' },
  { label: 'Propose stock receipt', prompt: 'Receive 50 units of Precision Sensor into Alpha Central' },
]

export default function AssistantPage() {
  const queryClient = useQueryClient()
  const enabled = Boolean(authStore.access)

  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [inputText, setInputText] = useState('')
  const [showPreferences, setShowPreferences] = useState(false)
  const sidebarOpen = true
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 1. Load conversations list
  const { data: conversations = [], isLoading: loadingConversations } = useQuery({
    queryKey: ['ai-conversations'],
    queryFn: api.aiConversations,
    enabled,
    retry: false,
  })

  const selectedConversationId = activeConversationId ?? (conversations.length > 0 ? conversations[0].id : null)

  // 2. Load active conversation details & messages
  const {
    data: activeConversation,
    isLoading: loadingMessages,
    refetch: refetchActiveConversation,
  } = useQuery({
    queryKey: ['ai-conversation', selectedConversationId],
    queryFn: () => (selectedConversationId ? api.aiConversation(selectedConversationId) : null),
    enabled: enabled && Boolean(selectedConversationId),
    retry: false,
  })

  // 3. User preferences query
  const { data: preferences = [], refetch: refetchPreferences } = useQuery({
    queryKey: ['ai-preferences'],
    queryFn: api.aiPreferences,
    enabled,
    retry: false,
  })

  const scrollToBottom = () => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [activeConversation?.messages])

  // Mutation: Send Chat Message
  const chatMutation = useMutation({
    mutationFn: (msg: string) =>
      api.aiChat({
        message: msg,
        conversation_id: activeConversationId,
      }),
    onSuccess: (data) => {
      setInputText('')
      if (!activeConversationId || activeConversationId !== data.conversation_id) {
        setActiveConversationId(data.conversation_id)
      }
      queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
      queryClient.invalidateQueries({ queryKey: ['ai-conversation', data.conversation_id] })
    },
  })

  // Mutation: Create New Conversation
  const newConversationMutation = useMutation({
    mutationFn: () => api.createAiConversation('New conversation'),
    onSuccess: (newConv) => {
      setActiveConversationId(newConv.id)
      queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
    },
  })

  // Mutation: Delete Conversation
  const deleteConversationMutation = useMutation({
    mutationFn: (id: number) => api.deleteAiConversation(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
      if (activeConversationId === deletedId) {
        const remaining = conversations.filter((c) => c.id !== deletedId)
        setActiveConversationId(remaining.length > 0 ? remaining[0].id : null)
      }
    },
  })

  // Mutation: Set Preference
  const setPreferenceMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) => api.setAiPreference(key, value),
    onSuccess: () => refetchPreferences(),
  })

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    const trimmed = inputText.trim()
    if (!trimmed || chatMutation.isPending) return
    chatMutation.mutate(trimmed)
  }

  const handlePromptClick = (prompt: string) => {
    setInputText(prompt)
    chatMutation.mutate(prompt)
  }

  if (!enabled) {
    return (
      <div className="notice-card">
        <p className="font-semibold text-ink">Sign in to use StockPilot AI Operations Assistant</p>
        <p className="mt-1 text-sm leading-6 text-slate-500">
          Sign in with an active workspace to chat with the assistant, query verified metrics, and execute confirmation-driven workflows.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="eyebrow flex items-center gap-1.5">
            <Sparkles size={13} className="text-indigo-600" />
            Intelligence / Operations Assistant
          </div>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-ink sm:text-3xl">Grounded AI Assistant</h2>
          <p className="text-xs text-slate-500 sm:text-sm">
            Answers from verified database records. Proposes consequential write operations for explicit user confirmation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="button-secondary px-3 py-2 text-xs font-semibold"
            onClick={() => setShowPreferences((v) => !v)}
            title="Configure memory preferences"
          >
            <Sliders size={14} /> Preferences
          </button>
          <button
            type="button"
            className="button-primary px-3.5 py-2 text-xs font-semibold"
            onClick={() => newConversationMutation.mutate()}
            disabled={newConversationMutation.isPending}
          >
            <Plus size={15} /> New chat
          </button>
        </div>
      </div>

      {/* Preferences Drawer / Modal */}
      {showPreferences && (
        <div className="rounded-2xl border border-indigo-100 bg-indigo-50/60 p-4">
          <div className="flex items-center justify-between pb-3 border-b border-indigo-100">
            <div className="flex items-center gap-2">
              <Sliders size={16} className="text-indigo-600" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-950">
                Workspace AI Preferences (Memory)
              </h4>
            </div>
            <button
              type="button"
              className="text-slate-400 hover:text-ink"
              onClick={() => setShowPreferences(false)}
            >
              <X size={16} />
            </button>
          </div>
          <p className="mt-2 text-xs text-indigo-900/70">
            Scoped to your user and active organization. The assistant incorporates these into operational responses.
          </p>
          <div className="mt-3 flex flex-wrap gap-3">
            <div className="flex items-center gap-2 rounded-xl bg-white px-3 py-1.5 border border-slate-200">
              <span className="text-xs font-semibold text-slate-600">Preferred Report:</span>
              <select
                className="text-xs font-bold text-ink bg-transparent focus:outline-none"
                value={
                  (preferences.find((p) => p.key === 'preferred_report_format')?.value as string) ?? 'csv'
                }
                onChange={(e) =>
                  setPreferenceMutation.mutate({ key: 'preferred_report_format', value: e.target.value })
                }
              >
                <option value="csv">CSV (Detailed Raw Data)</option>
                <option value="pdf">PDF (Formatted Document)</option>
              </select>
            </div>
            <div className="flex items-center gap-2 rounded-xl bg-white px-3 py-1.5 border border-slate-200">
              <span className="text-xs font-semibold text-slate-600">Preferred Hub:</span>
              <input
                type="text"
                placeholder="e.g. Alpha Central"
                defaultValue={
                  (preferences.find((p) => p.key === 'preferred_hub')?.value as string) ?? ''
                }
                onBlur={(e) => {
                  if (e.target.value.trim()) {
                    setPreferenceMutation.mutate({ key: 'preferred_hub', value: e.target.value.trim() })
                  }
                }}
                className="text-xs font-bold text-ink bg-transparent focus:outline-none w-32"
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Container */}
      <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
        {/* Sidebar: Conversation History */}
        <aside
          className={`panel-card flex flex-col h-[700px] p-3 transition-all ${
            sidebarOpen ? 'block' : 'hidden lg:flex'
          }`}
        >
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 px-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Conversations</span>
            <span className="text-[11px] font-semibold text-slate-400">{conversations.length}</span>
          </div>

          <div className="mt-2 flex-1 overflow-y-auto space-y-1 pr-1 scrollbar-thin">
            {loadingConversations ? (
              <div className="p-4 text-center text-xs text-slate-400">Loading conversations…</div>
            ) : conversations.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400">No conversations yet.</div>
            ) : (
              conversations.map((conv) => {
                const isActive = conv.id === activeConversationId
                return (
                  <div
                    key={conv.id}
                    className={`group flex items-center justify-between rounded-xl px-2.5 py-2 text-xs transition cursor-pointer ${
                      isActive ? 'bg-indigo-50/80 text-indigo-950 font-semibold' : 'text-slate-600 hover:bg-slate-50'
                    }`}
                    onClick={() => setActiveConversationId(conv.id)}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <MessageSquare size={14} className={isActive ? 'text-indigo-600' : 'text-slate-400'} />
                      <span className="truncate">{conv.title || 'Untitled Conversation'}</span>
                    </div>
                    <button
                      type="button"
                      aria-label="Delete conversation"
                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-600 p-1 transition"
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteConversationMutation.mutate(conv.id)
                      }}
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                )
              })
            )}
          </div>
        </aside>

        {/* Chat Area */}
        <div className="panel-card flex flex-col h-[700px] overflow-hidden p-0">
          {/* Chat Header */}
          <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 px-5 py-3">
            <div className="flex items-center gap-3">
              <span className="ai-icon">
                <Sparkles size={16} />
              </span>
              <div>
                <h3 className="text-sm font-bold text-ink">
                  {activeConversation?.title || 'StockPilot Assistant'}
                </h3>
                <p className="text-[11px] text-slate-400">Grounded Operations Engine</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="status-pill status-success text-[11px]">
                <span className="status-dot" /> Verified Tools Active
              </span>
            </div>
          </div>

          {/* Messages Window */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-thin">
            {loadingMessages ? (
              <div className="flex h-full items-center justify-center">
                <Loader2 size={24} className="animate-spin text-indigo-600" />
              </div>
            ) : !activeConversation || activeConversation.messages?.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="ai-orb">
                  <Sparkles size={24} />
                </div>
                <h3 className="mt-4 text-base font-bold text-ink">How can I assist your operations?</h3>
                <p className="mt-1 max-w-md text-xs text-slate-500">
                  Ask quantitative questions about stock balances, hub movements, and restock priorities, or propose verified stock transactions.
                </p>

                <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2 max-w-xl w-full">
                  {QUICK_PROMPTS.map(({ label, prompt }) => (
                    <button
                      key={label}
                      type="button"
                      className="flex items-center justify-between rounded-xl border border-slate-200/80 bg-white p-2.5 text-left text-xs font-medium text-slate-700 shadow-soft transition hover:border-indigo-300 hover:bg-indigo-50/40"
                      onClick={() => handlePromptClick(prompt)}
                    >
                      <span className="truncate">{label}</span>
                      <ArrowRight size={13} className="text-slate-400 shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              activeConversation.messages?.map((msg) => (
                <MessageBubble key={msg.id} message={msg} onRefreshNeeded={() => refetchActiveConversation()} />
              ))
            )}

            {chatMutation.isPending && (
              <div className="flex items-start gap-3">
                <span className="ai-icon shrink-0">
                  <Sparkles size={15} />
                </span>
                <div className="rounded-2xl bg-indigo-50/70 border border-indigo-100 p-3.5 text-xs text-indigo-900 flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin text-indigo-600" />
                  <span>Querying verified database records…</span>
                </div>
              </div>
            )}

            {chatMutation.isError && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 flex items-center gap-2">
                <AlertCircle size={15} className="shrink-0" />
                <span>
                  {chatMutation.error instanceof Error
                    ? chatMutation.error.message
                    : 'An error occurred while contacting the assistant.'}
                </span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <div className="border-t border-slate-200/80 bg-white p-3">
            <form onSubmit={handleSubmit} className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Ask about inventory, hubs, movements, or propose an action…"
                className="flex-1 rounded-xl border border-slate-200 bg-canvas px-3.5 py-2.5 text-xs font-medium text-ink focus:border-indigo-500 focus:bg-white focus:outline-none transition"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={chatMutation.isPending}
              />
              <button
                type="submit"
                disabled={!inputText.trim() || chatMutation.isPending}
                className="button-primary px-3.5 py-2.5 text-xs font-semibold shrink-0 disabled:opacity-40"
              >
                {chatMutation.isPending ? <Loader2 size={15} className="animate-spin" /> : <ArrowRight size={15} />}
              </button>
            </form>
            <p className="mt-1.5 text-center text-[10px] text-slate-400">
              StockPilot AI answers from verified measurements. Write operations require explicit confirmation.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message, onRefreshNeeded }: { message: AIMessage; onRefreshNeeded: () => void }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-xl rounded-2xl bg-ink px-4 py-2.5 text-xs font-medium text-white shadow-soft">
          {message.content}
        </div>
      </div>
    )
  }

  // Assistant Message
  return (
    <div className="flex items-start gap-3">
      <span className="ai-icon shrink-0 mt-0.5">
        <Sparkles size={15} />
      </span>

      <div className="flex-1 space-y-2.5 max-w-2xl">
        {/* Tool indicators */}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {message.tool_calls.map((tc) => (
              <span
                key={tc.id}
                className="inline-flex items-center gap-1 rounded-lg bg-slate-100 border border-slate-200/70 px-2 py-0.5 text-[10px] font-mono text-slate-600"
              >
                <Database size={11} className="text-indigo-500" />
                {tc.name}
              </span>
            ))}
          </div>
        )}

        {/* Text Content */}
        {message.content && (
          <div className="rounded-2xl border border-slate-200/70 bg-white p-4 text-xs leading-relaxed text-ink shadow-soft whitespace-pre-wrap">
            {formatContent(message.content)}
          </div>
        )}

        {/* Confirmation Cards for Write Proposals */}
        {message.tool_results?.map((tr) => {
          const res = tr.result as Record<string, unknown>
          if (res && res.requires_confirmation) {
            return (
              <ConfirmationCard
                key={tr.tool_call_id}
                proposal={res as unknown as AIWriteProposal}
                onExecuted={onRefreshNeeded}
              />
            )
          }
          return null
        })}
      </div>
    </div>
  )
}

function ConfirmationCard({
  proposal,
  onExecuted,
}: {
  proposal: AIWriteProposal
  onExecuted: () => void
}) {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<'pending' | 'executing' | 'confirmed' | 'cancelled' | 'error'>('pending')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [resultMessage, setResultMessage] = useState<string | null>(null)

  const confirmMutation = useMutation({
    mutationFn: () =>
      api.aiConfirmAction({
        action: proposal.action,
        parameters: proposal.parameters,
      }),
    onMutate: () => setStatus('executing'),
    onSuccess: (res) => {
      setStatus('confirmed')
      setResultMessage(res.message || 'Operation executed successfully.')

      // Invalidate affected data queries across the application
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-overview'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-movements'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-stock-health'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-hubs'] })
      queryClient.invalidateQueries({ queryKey: ['transfers'] })
      queryClient.invalidateQueries({ queryKey: ['restocks'] })

      onExecuted()
    },
    onError: (err: Error) => {
      setStatus('error')
      setErrorMessage(err.message || 'Failed to execute proposed action.')
    },
  })

  const p = proposal.parameters

  return (
    <div className="rounded-2xl border-2 border-indigo-200 bg-gradient-to-b from-indigo-50/60 to-white p-4 shadow-card">
      <div className="flex items-center justify-between pb-3 border-b border-indigo-100">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-soft">
            {proposal.action === 'create_transfer' ? (
              <Truck size={14} />
            ) : proposal.action === 'create_restock_request' ? (
              <Package size={14} />
            ) : (
              <Warehouse size={14} />
            )}
          </span>
          <div>
            <h4 className="text-xs font-bold text-indigo-950">
              {proposal.operation_label || 'Proposed Write Action'}
            </h4>
            <p className="text-[10px] text-indigo-700/80">Requires Explicit User Approval</p>
          </div>
        </div>

        <span
          className={`status-pill ${
            status === 'confirmed'
              ? 'status-success'
              : status === 'cancelled'
              ? 'status-muted'
              : status === 'error'
              ? 'status-danger'
              : 'status-amber'
          } text-[10px]`}
        >
          <span className="status-dot" />
          {status === 'confirmed'
            ? 'Executed'
            : status === 'cancelled'
            ? 'Cancelled'
            : status === 'executing'
            ? 'Executing…'
            : status === 'error'
            ? 'Failed'
            : 'Awaiting Confirmation'}
        </span>
      </div>

      {/* Proposal Details Grid */}
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div className="rounded-xl bg-white p-2 border border-slate-100">
          <span className="text-[10px] font-semibold text-slate-400 block">Product</span>
          <span className="font-bold text-ink">
            {String(p.product_name ?? 'Product')}
            {p.product_sku ? ` (${p.product_sku})` : ''}
          </span>
        </div>

        <div className="rounded-xl bg-white p-2 border border-slate-100">
          <span className="text-[10px] font-semibold text-slate-400 block">
            {p.source_hub_name ? 'Source → Destination' : 'Target Hub'}
          </span>
          <span className="font-bold text-ink">
            {p.source_hub_name
              ? `${p.source_hub_name} → ${p.destination_hub_name}`
              : String(p.hub_name ?? 'Primary Hub')}
          </span>
        </div>

        <div className="rounded-xl bg-white p-2 border border-slate-100">
          <span className="text-[10px] font-semibold text-slate-400 block">Quantity</span>
          <span className="font-bold text-indigo-700">{String(p.quantity ?? '0')} units</span>
        </div>

        <div className="rounded-xl bg-white p-2 border border-slate-100">
          <span className="text-[10px] font-semibold text-slate-400 block">Current Database State</span>
          <span className="font-medium text-slate-700">
            {proposal.current_state?.on_hand != null
              ? `On-hand: ${String(proposal.current_state.on_hand)}`
              : 'Verified'}
            {proposal.current_state?.available != null ? ` | Available: ${String(proposal.current_state.available)}` : ''}
          </span>
        </div>
      </div>

      {Boolean(p.reason) && (
        <div className="mt-2 rounded-xl bg-white px-3 py-1.5 border border-slate-100 text-[11px] text-slate-600">
          <span className="font-semibold text-slate-400">Reason: </span>
          {String(p.reason)}
        </div>
      )}

      {/* Outcome Feedback */}
      {status === 'confirmed' && (
        <div className="mt-3 rounded-xl bg-emerald-50 border border-emerald-200 p-2.5 text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
          <span>{resultMessage}</span>
        </div>
      )}

      {status === 'cancelled' && (
        <div className="mt-3 rounded-xl bg-slate-100 border border-slate-200 p-2.5 text-xs text-slate-600 flex items-center gap-2">
          <X size={15} className="text-slate-500 shrink-0" />
          <span>Action cancelled. No changes were made to inventory.</span>
        </div>
      )}

      {status === 'error' && (
        <div className="mt-3 rounded-xl bg-rose-50 border border-rose-200 p-2.5 text-xs text-rose-800 flex items-center gap-2">
          <AlertCircle size={15} className="text-rose-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Buttons */}
      {status === 'pending' && (
        <div className="mt-3 flex items-center justify-end gap-2 pt-2 border-t border-indigo-100/70">
          <button
            type="button"
            className="button-secondary px-3 py-1.5 text-xs font-semibold"
            onClick={() => setStatus('cancelled')}
          >
            <X size={14} /> Cancel
          </button>
          <button
            type="button"
            className="button-primary px-4 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700"
            onClick={() => confirmMutation.mutate()}
            disabled={confirmMutation.isPending}
          >
            <Check size={14} /> Confirm & Execute
          </button>
        </div>
      )}
    </div>
  )
}

function formatContent(content: string) {
  // Simple clean formatting for markdown-style code blocks and lines
  return content
}
