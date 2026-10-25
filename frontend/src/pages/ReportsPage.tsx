import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts'
import {
  Activity, AlertTriangle, ArrowDownToLine, ArrowRight, BarChart3, Boxes,
  Download, FileSpreadsheet, FileText, Loader2,
  Package, PackageX, RefreshCw, ShieldAlert, TrendingDown, TrendingUp,
  Warehouse, X,
  type LucideIcon,
} from 'lucide-react'
import { api, authStore } from '../lib/api'
import type {
  AnalyticsOverview, MovementTrends, HubAnalytics,
  StockHealthResponse, LowStockProduct, RestockRecommendation,
} from '../lib/api'

const REPORT_TYPES = [
  { key: 'inventory_health', label: 'Inventory Health', icon: Activity, color: 'emerald', description: 'Overall stock health breakdown across all products' },
  { key: 'low_stock', label: 'Low Stock', icon: AlertTriangle, color: 'amber', description: 'Products below reorder threshold requiring attention' },
  { key: 'stockout', label: 'Stockout', icon: PackageX, color: 'red', description: 'Products with zero inventory across all hubs' },
  { key: 'inventory_valuation', label: 'Inventory Valuation', icon: BarChart3, color: 'blue', description: 'Cost-based valuation of all inventory positions' },
  { key: 'slow_moving', label: 'Slow Moving', icon: TrendingDown, color: 'violet', description: 'Products with no movement in the lookback period' },
  { key: 'hub_performance', label: 'Hub Performance', icon: Warehouse, color: 'indigo', description: 'Stock distribution and health metrics per hub' },
  { key: 'stock_movements', label: 'Stock Movements', icon: ArrowDownToLine, color: 'sky', description: 'Detailed log of receipts, issues, and adjustments' },
  { key: 'transfers', label: 'Transfers', icon: RefreshCw, color: 'teal', description: 'Inter-hub transfer history and status' },
  { key: 'restocking', label: 'Restocking', icon: Package, color: 'orange', description: 'Restock request history and completion rates' },
] as const

const HEALTH_COLORS: Record<string, string> = {
  healthy: '#10b981',
  low_stock: '#f59e0b',
  out_of_stock: '#ef4444',
  excess: '#8b5cf6',
  slow_moving: '#6366f1',
}

export default function ReportsPage() {
  const enabled = Boolean(authStore.access)
  const [activeTab, setActiveTab] = useState<'dashboard' | 'reports'>('dashboard')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <div className="eyebrow">Workspace / Reports</div>
          <h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-ink sm:text-4xl">
            Reports & Analytics
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">
            Deterministic insights from your verified inventory data. Every metric is calculated from actual records.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition ${activeTab === 'dashboard' ? 'bg-slate-900 text-white shadow-md' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <BarChart3 size={15} className="mr-1.5 inline" /> Dashboard
          </button>
          <button
            className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition ${activeTab === 'reports' ? 'bg-slate-900 text-white shadow-md' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200'}`}
            onClick={() => setActiveTab('reports')}
          >
            <FileText size={15} className="mr-1.5 inline" /> Generate Reports
          </button>
        </div>
      </div>

      {!enabled ? (
        <div className="notice-card">
          <p className="font-semibold text-ink">Sign in to access analytics</p>
          <p className="mt-1 text-sm leading-6 text-slate-500">
            Analytics require an authenticated organization context.
          </p>
        </div>
      ) : activeTab === 'dashboard' ? (
        <AnalyticsDashboard />
      ) : (
        <ReportGenerator />
      )}
    </div>
  )
}

/* ─── Analytics Dashboard ─── */

function AnalyticsDashboard() {
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: api.analyticsOverview,
    retry: false,
  })
  const { data: movements } = useQuery({
    queryKey: ['analytics-movements'],
    queryFn: () => api.analyticsMovements(30),
    retry: false,
  })
  const { data: hubs } = useQuery({
    queryKey: ['analytics-hubs'],
    queryFn: api.analyticsHubs,
    retry: false,
  })
  const { data: stockHealth } = useQuery({
    queryKey: ['analytics-stock-health'],
    queryFn: () => api.analyticsStockHealth(30),
    retry: false,
  })
  const { data: lowStock } = useQuery({
    queryKey: ['analytics-low-stock'],
    queryFn: () => api.analyticsLowStock(),
    retry: false,
  })
  const { data: restockRecs } = useQuery({
    queryKey: ['analytics-restock-recommendations'],
    queryFn: api.analyticsRestockRecommendations,
    retry: false,
  })

  if (overviewLoading) return <DashboardSkeleton />

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      {overview && <KPIGrid overview={overview} />}

      {/* Charts Row */}
      <div className="grid gap-5 xl:grid-cols-[1.4fr_0.6fr]">
        <MovementChart movements={movements} />
        <StockHealthChart health={stockHealth} />
      </div>

      {/* Hub Performance + Low Stock */}
      <div className="grid gap-5 xl:grid-cols-2">
        <HubPerformanceTable hubs={hubs ?? []} />
        <LowStockTable items={lowStock ?? []} />
      </div>

      {/* Restock Recommendations */}
      {restockRecs && restockRecs.length > 0 && (
        <RestockRecommendationsTable items={restockRecs} />
      )}
    </div>
  )
}

function KPIGrid({ overview }: { overview: AnalyticsOverview }) {
  const kpis: Array<{ label: string; value: string; sub: string; icon: LucideIcon; tone: string }> = [
    { label: 'Active Products', value: String(overview.active_products), sub: overview.data_status === 'live' ? 'Live records' : 'No records', icon: Package, tone: 'blue' },
    { label: 'Total Units', value: Number(overview.total_units).toLocaleString(), sub: `${overview.active_hubs} active hubs`, icon: Boxes, tone: 'emerald' },
    { label: 'Inventory Value', value: `$${Number(overview.inventory_value).toLocaleString()}`, sub: 'Cost-based valuation', icon: BarChart3, tone: 'violet' },
    { label: 'Low Stock', value: String(overview.low_stock_products), sub: `${overview.out_of_stock_products} out of stock`, icon: AlertTriangle, tone: 'amber' },
    { label: 'Movement Volume', value: String(overview.movement_volume_30d), sub: 'Last 30 days', icon: Activity, tone: 'sky' },
    { label: 'Active Hubs', value: String(overview.active_hubs), sub: 'Operating locations', icon: Warehouse, tone: 'indigo' },
  ]

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      {kpis.map((kpi, i) => (
        <motion.div
          key={kpi.label}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          className="metric-card group"
        >
          <div className="flex items-start justify-between">
            <span className={`flex h-9 w-9 items-center justify-center rounded-xl bg-${kpi.tone}-50 text-${kpi.tone}-500`}>
              <kpi.icon size={17} />
            </span>
          </div>
          <p className="mt-4 text-sm font-medium text-slate-500">{kpi.label}</p>
          <p className="mt-1 text-2xl font-semibold tracking-[-0.03em] text-ink">{kpi.value}</p>
          <p className="mt-1 text-xs font-medium text-slate-400">{kpi.sub}</p>
        </motion.div>
      ))}
    </div>
  )
}

function MovementChart({ movements }: { movements?: MovementTrends }) {
  const hasData = movements?.data_status === 'live' && movements.trends.length > 0

  return (
    <div className="panel-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-ink">Movement Trends</p>
          <p className="mt-1 text-xs text-slate-400">
            {hasData ? `Last ${movements!.period_days} days` : 'Awaiting movement data'}
          </p>
        </div>
        <span className={`status-pill ${hasData ? 'status-success' : 'status-neutral'}`}>
          <span className="status-dot" />
          {hasData ? 'Live' : 'No data'}
        </span>
      </div>
      {hasData ? (
        <div className="mt-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={movements!.trends} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
              <defs>
                <linearGradient id="recGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="issGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#94a3b8" tickFormatter={(v) => v.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }} />
              <Area type="monotone" dataKey="receipts" stroke="#10b981" fill="url(#recGrad)" strokeWidth={2} name="Receipts" />
              <Area type="monotone" dataKey="issues" stroke="#f59e0b" fill="url(#issGrad)" strokeWidth={2} name="Issues" />
              <Area type="monotone" dataKey="adjustments" stroke="#6366f1" fill="transparent" strokeWidth={1.5} strokeDasharray="4 3" name="Adjustments" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="empty-chart">
          <div className="empty-chart-grid" />
          <div className="relative z-10 flex flex-col items-center">
            <span className="signal-icon signal-blue"><BarChart3 size={17} /></span>
            <p className="mt-3 text-sm font-semibold text-slate-600">No movement data yet</p>
            <p className="mt-1 text-xs text-slate-400">Receive or issue stock to start seeing trends.</p>
          </div>
        </div>
      )}
    </div>
  )
}

function StockHealthChart({ health }: { health?: StockHealthResponse }) {
  if (!health || health.summary.total_products === 0) {
    return (
      <div className="panel-card flex flex-col items-center justify-center text-center">
        <span className="signal-icon signal-blue"><ShieldAlert size={17} /></span>
        <p className="mt-3 text-sm font-semibold text-slate-600">No products to analyze</p>
        <p className="mt-1 text-xs text-slate-400">Add products to see stock health.</p>
      </div>
    )
  }

  const { summary } = health
  const pieData = [
    { name: 'Healthy', value: summary.healthy, color: HEALTH_COLORS.healthy },
    { name: 'Low Stock', value: summary.low_stock, color: HEALTH_COLORS.low_stock },
    { name: 'Out of Stock', value: summary.out_of_stock, color: HEALTH_COLORS.out_of_stock },
    { name: 'Excess', value: summary.excess, color: HEALTH_COLORS.excess },
    { name: 'Slow Moving', value: summary.slow_moving, color: HEALTH_COLORS.slow_moving },
  ].filter(d => d.value > 0)

  return (
    <div className="panel-card">
      <p className="text-sm font-semibold text-ink">Stock Health</p>
      <p className="mt-1 text-xs text-slate-400">{summary.total_products} products analyzed</p>
      <div className="mt-4 h-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={75} dataKey="value" paddingAngle={2}>
              {pieData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex flex-wrap gap-3 text-xs">
        {pieData.map((d) => (
          <span key={d.name} className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: d.color }} />
            {d.name}: {d.value}
          </span>
        ))}
      </div>
    </div>
  )
}

function HubPerformanceTable({ hubs }: { hubs: HubAnalytics[] }) {
  if (hubs.length === 0) {
    return (
      <div className="panel-card flex flex-col items-center justify-center py-10 text-center">
        <span className="feature-icon"><Warehouse size={20} /></span>
        <p className="mt-4 text-sm font-semibold text-slate-600">No hubs configured</p>
        <p className="mt-1 text-xs text-slate-400">Add hubs to see performance metrics.</p>
      </div>
    )
  }

  return (
    <div className="panel-card overflow-hidden">
      <p className="text-sm font-semibold text-ink">Hub Performance</p>
      <p className="mt-1 text-xs text-slate-400">{hubs.length} active hubs</p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400">
              <th className="pb-3 pr-4">Hub</th>
              <th className="pb-3 pr-4 text-right">Products</th>
              <th className="pb-3 pr-4 text-right">Units</th>
              <th className="pb-3 pr-4 text-right">Value</th>
              <th className="pb-3 text-right">Alerts</th>
            </tr>
          </thead>
          <tbody>
            {hubs.map((hub) => (
              <tr key={hub.hub_id} className="border-b border-slate-50 transition hover:bg-slate-25">
                <td className="py-3 pr-4">
                  <p className="font-semibold text-ink">{hub.hub_name}</p>
                  <p className="text-xs text-slate-400">{hub.hub_code}</p>
                </td>
                <td className="py-3 pr-4 text-right font-medium">{hub.product_count}</td>
                <td className="py-3 pr-4 text-right font-medium">{Number(hub.total_units).toLocaleString()}</td>
                <td className="py-3 pr-4 text-right font-medium">${Number(hub.total_value).toLocaleString()}</td>
                <td className="py-3 text-right">
                  {(hub.low_stock_count + hub.out_of_stock_count) > 0 ? (
                    <span className="inline-flex items-center gap-1 rounded-lg bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-600">
                      <AlertTriangle size={12} />
                      {hub.low_stock_count + hub.out_of_stock_count}
                    </span>
                  ) : (
                    <span className="text-xs text-emerald-500">✓</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function LowStockTable({ items }: { items: LowStockProduct[] }) {
  if (items.length === 0) {
    return (
      <div className="panel-card flex flex-col items-center justify-center py-10 text-center">
        <span className="feature-icon h-12 w-12"><Boxes size={20} /></span>
        <p className="mt-4 text-sm font-semibold text-slate-600">All products are stocked</p>
        <p className="mt-1 text-xs text-slate-400">No products below reorder threshold.</p>
      </div>
    )
  }

  return (
    <div className="panel-card overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-ink">Low Stock Alert</p>
          <p className="mt-1 text-xs text-slate-400">{items.length} products need attention</p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-xl bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-600">
          <AlertTriangle size={13} /> {items.length}
        </span>
      </div>
      <div className="mt-4 space-y-2">
        {items.slice(0, 8).map((item) => (
          <div key={item.product_id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-25 px-4 py-3 transition hover:border-slate-200">
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-ink">{item.product_name}</p>
              <p className="text-xs text-slate-400">{item.sku} · {item.category ?? 'Uncategorized'}</p>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-amber-600">{Number(item.on_hand).toLocaleString()} / {Number(item.reorder_threshold).toLocaleString()}</p>
              <p className="text-xs text-slate-400">Deficit: {Number(item.deficit).toLocaleString()}</p>
            </div>
          </div>
        ))}
        {items.length > 8 && (
          <p className="text-center text-xs text-slate-400">and {items.length - 8} more…</p>
        )}
      </div>
    </div>
  )
}

function RestockRecommendationsTable({ items }: { items: RestockRecommendation[] }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="panel-card overflow-hidden">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-ink">Restock Recommendations</p>
          <p className="mt-1 text-xs text-slate-400">
            Deterministic: target_stock_level − on_hand. Not an AI prediction.
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-xl bg-blue-50 px-3 py-1.5 text-xs font-bold text-blue-600">
          <TrendingUp size={13} /> {items.length}
        </span>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400">
              <th className="pb-3 pr-4">Product</th>
              <th className="pb-3 pr-4 text-right">On Hand</th>
              <th className="pb-3 pr-4 text-right">Target</th>
              <th className="pb-3 pr-4 text-right">Order Qty</th>
              <th className="pb-3 pr-4 text-right">Est. Cost</th>
              <th className="pb-3 text-center">Priority</th>
            </tr>
          </thead>
          <tbody>
            {items.slice(0, 15).map((item) => (
              <tr key={item.product_id} className="border-b border-slate-50 transition hover:bg-slate-25">
                <td className="py-3 pr-4">
                  <p className="font-semibold text-ink">{item.product_name}</p>
                  <p className="text-xs text-slate-400">{item.sku}</p>
                </td>
                <td className="py-3 pr-4 text-right font-medium">{Number(item.on_hand).toLocaleString()}</td>
                <td className="py-3 pr-4 text-right font-medium">{Number(item.target_stock_level).toLocaleString()}</td>
                <td className="py-3 pr-4 text-right font-bold text-blue-600">{Number(item.recommended_quantity).toLocaleString()}</td>
                <td className="py-3 pr-4 text-right font-medium">${Number(item.estimated_cost).toLocaleString()}</td>
                <td className="py-3 text-center">
                  <span className={`inline-block rounded-lg px-2.5 py-1 text-xs font-bold ${
                    item.priority === 'critical' ? 'bg-red-50 text-red-600' :
                    item.priority === 'high' ? 'bg-amber-50 text-amber-600' :
                    'bg-slate-100 text-slate-500'
                  }`}>
                    {item.priority}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}

/* ─── Report Generator ─── */

function ReportGenerator() {
  const [selectedType, setSelectedType] = useState<string | null>(null)
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'pdf'>('csv')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = async (reportType: string) => {
    setGenerating(true)
    setError(null)
    try {
      const resp = await api.generateReport({
        report_type: reportType,
        format: selectedFormat,
      })
      // Download the file
      const blob = await resp.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const disposition = resp.headers.get('Content-Disposition')
      const filename = disposition?.match(/filename="(.+)"/)?.[1] ?? `report.${selectedFormat}`
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Report generation failed')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Format Selector */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold text-slate-500">Export format:</span>
        <div className="inline-flex rounded-xl border border-slate-200 bg-white p-1">
          <button
            className={`flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-semibold transition ${selectedFormat === 'csv' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:text-slate-700'}`}
            onClick={() => setSelectedFormat('csv')}
          >
            <FileSpreadsheet size={14} /> CSV
          </button>
          <button
            className={`flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-semibold transition ${selectedFormat === 'pdf' ? 'bg-slate-900 text-white' : 'text-slate-500 hover:text-slate-700'}`}
            onClick={() => setSelectedFormat('pdf')}
          >
            <FileText size={14} /> PDF
          </button>
        </div>
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="notice-card border-red-100 bg-red-50/70"
          >
            <div className="flex items-center justify-between">
              <p className="font-semibold text-red-700">{error}</p>
              <button className="icon-button" onClick={() => setError(null)}><X size={16} /></button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Report Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {REPORT_TYPES.map(({ key, label, icon: Icon, color, description }) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className={`group relative overflow-hidden rounded-2xl border bg-white p-5 shadow-soft transition-all hover:shadow-card hover:-translate-y-0.5 cursor-pointer ${
              selectedType === key ? 'border-blue-300 ring-2 ring-blue-100' : 'border-slate-200/80'
            }`}
            onClick={() => setSelectedType(selectedType === key ? null : key)}
          >
            <div className="flex items-start justify-between">
              <span className={`flex h-10 w-10 items-center justify-center rounded-xl bg-${color}-50 text-${color}-500`}>
                <Icon size={19} />
              </span>
              {generating && selectedType === key ? (
                <Loader2 size={18} className="animate-spin text-blue-500" />
              ) : (
                <ArrowRight size={16} className="text-slate-300 transition group-hover:text-slate-500" />
              )}
            </div>
            <h3 className="mt-4 text-sm font-bold text-ink">{label}</h3>
            <p className="mt-1.5 text-xs leading-5 text-slate-400">{description}</p>

            <AnimatePresence>
              {selectedType === key && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <button
                    className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50"
                    disabled={generating}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleGenerate(key)
                    }}
                  >
                    {generating ? (
                      <><Loader2 size={15} className="animate-spin" /> Generating…</>
                    ) : (
                      <><Download size={15} /> Download {selectedFormat.toUpperCase()}</>
                    )}
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

/* ─── Skeleton ─── */

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="metric-card animate-pulse">
            <div className="h-9 w-9 rounded-xl bg-slate-100" />
            <div className="mt-4 h-4 w-20 rounded bg-slate-100" />
            <div className="mt-2 h-7 w-16 rounded bg-slate-100" />
            <div className="mt-2 h-3 w-24 rounded bg-slate-100" />
          </div>
        ))}
      </div>
      <div className="grid gap-5 xl:grid-cols-[1.4fr_0.6fr]">
        <div className="panel-card h-80 animate-pulse" />
        <div className="panel-card h-80 animate-pulse" />
      </div>
    </div>
  )
}
