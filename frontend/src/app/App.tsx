import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ArrowRight,
  BarChart3,
  Bell,
  Boxes,
  Check,
  ChevronDown,
  CircleHelp,
  Clock3,
  Database,
  FileText,
  Filter,
  LayoutDashboard,
  Menu,
  MoreHorizontal,
  Package,
  PackageCheck,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  Settings,
  Sparkles,
  Truck,
  Users,
  Warehouse,
  X,
  Zap,
  type LucideIcon,
} from 'lucide-react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import AuthPage from '../pages/AuthPage'
import TeamPage from '../pages/TeamPage'
import OperationsPage from '../pages/OperationsPage'
import { api, authStore } from '../lib/api'

type NavItem = { label: string; path: string; icon: LucideIcon; badge?: string; accent?: boolean }

const navSections: Array<{ label: string; items: NavItem[] }> = [
  {
    label: 'Workspace',
    items: [
      { label: 'Overview', path: '/app', icon: LayoutDashboard },
      { label: 'Inventory', path: '/app/inventory', icon: Package },
      { label: 'Categories', path: '/app/categories', icon: Boxes },
      { label: 'Hubs', path: '/app/hubs', icon: Warehouse },
      { label: 'Restock', path: '/app/restock', icon: PackageCheck },
      { label: 'Transfers', path: '/app/transfers', icon: Truck },
      { label: 'Suppliers', path: '/app/suppliers', icon: Users },
      { label: 'Reports', path: '/app/reports', icon: FileText },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { label: 'AI Assistant', path: '/app/assistant', icon: Sparkles, accent: true },
      { label: 'Activity log', path: '/app/activity', icon: Clock3 },
    ],
  },
]

const attentionItems = [
  { title: 'Connect your database', description: 'Bring in your first live inventory records.', tone: 'blue', icon: Database },
  { title: 'Create your first hub', description: 'Set up the places where stock is stored.', tone: 'violet', icon: Warehouse },
  { title: 'Invite your team', description: 'Give operators the right level of access.', tone: 'amber', icon: Users },
]

const quickActions = [
  { label: 'Add product', icon: Package, path: '/app/inventory' },
  { label: 'Create transfer', icon: Truck, path: '/app/transfers' },
  { label: 'Ask AI', icon: Sparkles, path: '/app/assistant' },
]

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<AuthPage />} />
      <Route path="/app/*" element={<AppShell />} />
    </Routes>
  )
}

function LandingPage() {
  const navigate = useNavigate()
  return (
    <main className="min-h-screen overflow-hidden bg-canvas text-ink">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[620px] bg-[radial-gradient(circle_at_76%_0%,rgba(99,102,241,0.18),transparent_32%),radial-gradient(circle_at_24%_12%,rgba(37,99,235,0.14),transparent_28%)]" />
      <header className="relative mx-auto flex max-w-7xl items-center justify-between px-5 py-6 lg:px-8">
        <Brand />
        <nav className="hidden items-center gap-8 text-sm font-semibold text-slate-500 md:flex">
          <a href="#platform" className="transition hover:text-ink">Platform</a>
          <a href="#signals" className="transition hover:text-ink">Why StockPilot</a>
          <a href="#workflow" className="transition hover:text-ink">Workflow</a>
        </nav>
        <div className="flex items-center gap-3">
          <button className="hidden px-3 py-2 text-sm font-semibold text-slate-600 transition hover:text-ink sm:block" onClick={() => navigate('/login')}>Sign in</button>
          <button className="button-primary px-4 py-2.5 text-sm" onClick={() => navigate('/app')}>
            Open workspace <ArrowRight size={16} />
          </button>
        </div>
      </header>

      <section className="relative mx-auto grid max-w-7xl gap-14 px-5 pb-20 pt-14 lg:grid-cols-[0.95fr_1.05fr] lg:items-center lg:px-8 lg:pb-28 lg:pt-24">
        <div>
          <div className="eyebrow"><span className="pulse-dot" />Inventory intelligence for teams that move</div>
          <h1 className="mt-6 max-w-3xl text-5xl font-semibold leading-[1.04] tracking-[-0.05em] text-ink sm:text-6xl lg:text-[72px]">See the signal before it becomes a <span className="text-gradient">stockout.</span></h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-slate-500">StockPilot gives every hub, product, and movement a shared operating picture — then turns verified data into the next best action.</p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <button className="button-primary px-5 py-3.5" onClick={() => navigate('/app')}>Start with a clean workspace <ArrowRight size={17} /></button>
            <a className="button-secondary px-5 py-3.5" href="#platform">Explore the platform</a>
          </div>
          <div className="mt-10 flex flex-wrap items-center gap-x-7 gap-y-3 text-sm font-medium text-slate-500">
            {['Verified metrics', 'Permission-aware AI', 'Built for multiple hubs'].map((item) => <span key={item} className="inline-flex items-center gap-2"><Check size={15} className="text-emerald-500" />{item}</span>)}
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-[600px] lg:ml-auto">
          <div className="absolute -inset-8 rounded-[42px] bg-gradient-to-br from-blue-200/30 via-transparent to-violet-200/30 blur-2xl" />
          <div className="relative overflow-hidden rounded-[26px] border border-white/80 bg-white/85 p-3 shadow-card backdrop-blur-xl">
            <div className="rounded-[19px] border border-slate-200/80 bg-[#fbfcff] p-4 sm:p-5">
              <div className="flex items-center justify-between border-b border-slate-200/80 pb-4">
                <div className="flex items-center gap-3"><div className="mini-mark"><span /><span /><span /></div><div><p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Operations cockpit</p><p className="mt-1 text-sm font-semibold text-ink">Monday, 9:42 AM</p></div></div>
                <span className="status-pill status-success"><span className="status-dot" />Live view</span>
              </div>
              <div className="grid grid-cols-3 gap-2.5 py-5">
                <MetricCard label="Stock value" value="$248.6k" change="+8.4%" positive />
                <MetricCard label="At risk" value="14 SKUs" change="Needs review" />
                <MetricCard label="Hubs online" value="08 / 08" change="All connected" positive />
              </div>
              <div className="grid gap-3 sm:grid-cols-[1.18fr_0.82fr]">
                <div className="rounded-2xl border border-slate-200/80 bg-white p-4"><div className="flex items-center justify-between"><div><p className="text-xs font-semibold text-slate-500">Inventory movement</p><p className="mt-1 text-xl font-semibold tracking-tight text-ink">$32,840 <span className="text-xs font-medium text-emerald-500">this month</span></p></div><BarChart3 size={18} className="text-blue-500" /></div><MiniChart /></div>
                <div className="rounded-2xl border border-slate-200/80 bg-white p-4"><div className="flex items-center justify-between"><p className="text-xs font-semibold text-slate-500">Attention queue</p><MoreHorizontal size={17} className="text-slate-400" /></div><div className="mt-4 space-y-3">{['Stockout risk', 'Excess stock', 'Transfer pending'].map((item, index) => <div key={item} className="flex items-center gap-2.5"><span className={`signal-icon ${index === 0 ? 'signal-danger' : index === 1 ? 'signal-amber' : 'signal-blue'}`}><Zap size={13} /></span><div className="min-w-0"><p className="truncate text-xs font-semibold text-ink">{item}</p><p className="text-[10px] text-slate-400">{index + 2} items</p></div></div>)}</div></div>
              </div>
              <div className="mt-3 rounded-2xl border border-indigo-100 bg-gradient-to-r from-indigo-50 to-blue-50 p-4"><div className="flex items-start gap-3"><span className="ai-icon"><Sparkles size={14} /></span><div><p className="text-xs font-bold text-indigo-950">AI insight</p><p className="mt-1 text-xs leading-5 text-indigo-900/70">Bengaluru is carrying 18% more slow-moving stock than the network average. View suggested transfers.</p></div><ArrowRight size={15} className="ml-auto mt-0.5 shrink-0 text-indigo-500" /></div></div>
            </div>
          </div>
          <div className="float-card float-card-left"><span className="signal-icon signal-success"><Check size={13} /></span><div><p className="text-xs font-bold text-ink">Verified movement</p><p className="text-[10px] text-slate-400">Receipt #MOV-1048 posted</p></div></div>
          <div className="float-card float-card-right"><span className="ai-icon"><Sparkles size={13} /></span><div><p className="text-xs font-bold text-ink">Ask your data</p><p className="text-[10px] text-slate-400">“Where is risk rising?”</p></div></div>
        </div>
      </section>

      <section id="platform" className="relative border-y border-slate-200/70 bg-white/70 py-20 lg:py-28"><div className="mx-auto max-w-7xl px-5 lg:px-8"><div className="max-w-2xl"><div className="eyebrow">One operating picture</div><h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-ink sm:text-5xl">From scattered stock data to a <span className="text-gradient">decisive next move.</span></h2><p className="mt-5 text-lg leading-8 text-slate-500">StockPilot connects the daily mechanics of inventory with the clarity leaders need to keep operations moving.</p></div><div className="mt-12 grid gap-4 md:grid-cols-3">{[
        { icon: Boxes, title: 'Know every balance', text: 'See current, reserved, and available stock by product and hub with one source of truth.' },
        { icon: BarChart3, title: 'Spot risk earlier', text: 'Low-stock, stockout, excess, and movement signals rise to the surface before they become surprises.' },
        { icon: Sparkles, title: 'Act with context', text: 'Ask an assistant that can explain verified metrics, recommend actions, and respect your permissions.' },
      ].map(({ icon: Icon, title, text }) => <div key={title} className="feature-card"><span className="feature-icon"><Icon size={19} /></span><h3 className="mt-5 text-lg font-semibold text-ink">{title}</h3><p className="mt-2 leading-7 text-slate-500">{text}</p><span className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-signal-600">Learn more <ArrowRight size={14} /></span></div>)}</div></div></section>

      <section id="signals" className="mx-auto grid max-w-7xl gap-10 px-5 py-20 lg:grid-cols-[0.8fr_1.2fr] lg:items-center lg:px-8 lg:py-28"><div><div className="eyebrow">Grounded by design</div><h2 className="mt-4 text-4xl font-semibold tracking-[-0.04em] text-ink sm:text-5xl">The calm layer between <span className="text-gradient">data and action.</span></h2><p className="mt-5 max-w-lg text-lg leading-8 text-slate-500">Every recommendation is separated from verified measurement. Every consequential action is visible, permissioned, and confirmed.</p><button className="button-secondary mt-7 px-4 py-3 text-sm" onClick={() => navigate('/app/assistant')}>See the assistant <ArrowRight size={16} /></button></div><div className="grid gap-4 sm:grid-cols-2"><SignalCard number="01" title="No mystery metrics" text="Dashboard values come from your connected records — not hardcoded demo numbers." icon={BarChart3} /><SignalCard number="02" title="No silent changes" text="Receipts, issues, adjustments, and transfers create an auditable movement history." icon={Database} /><SignalCard number="03" title="No permission bypass" text="AI tools use the same server-side authorization as the rest of your workspace." icon={Users} /><SignalCard number="04" title="No dead-end screens" text="Empty states guide the next setup step instead of pretending the workspace is ready." icon={CircleHelp} /></div></section>

      <section id="workflow" className="bg-ink py-20 text-white lg:py-28"><div className="mx-auto grid max-w-7xl gap-12 px-5 lg:grid-cols-[1fr_1.1fr] lg:items-center lg:px-8"><div><div className="eyebrow eyebrow-dark">A better daily rhythm</div><h2 className="mt-4 max-w-xl text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">Make the next operational decision <span className="text-blue-300">feel obvious.</span></h2><p className="mt-5 max-w-lg text-lg leading-8 text-blue-100/70">Start with a clean workspace. Connect your records. Let the operating picture get sharper with every movement.</p><button className="button-light mt-8 px-5 py-3.5" onClick={() => navigate('/app')}>Open the workspace <ArrowRight size={17} /></button></div><div className="grid gap-3">{['Connect hubs and products', 'Watch verified signals', 'Move stock with confidence'].map((item, index) => <div key={item} className="flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-400/15 text-sm font-bold text-blue-200">0{index + 1}</span><div><p className="font-semibold">{item}</p><p className="mt-1 text-sm text-blue-100/55">{['Set your operating context and invite the right people.', 'See what needs attention without hunting through screens.', 'Review the detail, confirm the action, keep a clean trail.'][index]}</p></div><ArrowRight size={16} className="ml-auto text-blue-200/50" /></div>)}</div></div></section>
      <footer className="bg-ink px-5 pb-8 text-sm text-blue-100/45 lg:px-8"><div className="mx-auto flex max-w-7xl flex-col gap-4 border-t border-white/10 pt-7 sm:flex-row sm:items-center sm:justify-between"><Brand dark /><span>Built for the teams behind the movement.</span></div></footer>
    </main>
  )
}

function OrganizationSwitcher({ collapsed }: { collapsed: boolean }) {
  const [open, setOpen] = useState(false)
  const enabled = Boolean(authStore.access)
  const { data: me } = useQuery({ queryKey: ['me'], queryFn: api.me, enabled, retry: false })
  const { data: organizations = [] } = useQuery({ queryKey: ['organizations'], queryFn: api.organizations, enabled, retry: false })
  const active = me?.active_organization ?? organizations[0]
  async function switchOrganization(id: number) {
    await api.switchOrganization(id)
    window.location.reload()
  }
  return <div className="relative px-3 pb-3"><button className="workspace-switcher" disabled={!enabled} title={enabled ? 'Switch organization' : 'Sign in to switch organization'} onClick={() => setOpen((value) => !value)}><span className="workspace-avatar">{active?.name?.slice(0, 2).toUpperCase() ?? 'SP'}</span><span className={`min-w-0 flex-1 text-left ${collapsed ? 'lg:hidden' : ''}`}><span className="block truncate text-xs font-bold text-ink">{active?.name ?? 'Preview workspace'}</span><span className="mt-0.5 block truncate text-[11px] text-slate-400">{active ? 'Active organization' : 'Sign in to switch'}</span></span><ChevronDown size={14} className={`text-slate-400 ${collapsed ? 'lg:hidden' : ''}`} /></button>{open && enabled && <div className="absolute left-3 right-3 top-[58px] z-50 rounded-2xl border border-slate-200 bg-white p-2 shadow-card">{organizations.map((organization) => <button key={organization.id} className="flex w-full items-center gap-2 rounded-xl px-2.5 py-2 text-left transition hover:bg-slate-50" onClick={() => void switchOrganization(organization.id)}><span className="workspace-avatar h-7 w-7 rounded-lg text-[9px]">{organization.name.slice(0, 2).toUpperCase()}</span><span className="min-w-0 flex-1"><span className="block truncate text-xs font-semibold text-ink">{organization.name}</span><span className="block text-[10px] text-slate-400">{organization.role}</span></span></button>)}</div>}</div>
}

function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const pageTitle = useMemo(() => location.pathname === '/app' ? 'Overview' : navSections.flatMap((section) => section.items).find((item) => location.pathname.startsWith(item.path))?.label ?? 'Workspace', [location.pathname])
  return <div className="min-h-screen bg-canvas text-ink"><aside className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''} ${mobileOpen ? 'sidebar-mobile-open' : ''}`}><div className="flex h-full flex-col"><div className="flex h-[76px] items-center justify-between px-5"><Brand compact={collapsed} /><button className="icon-button hidden lg:inline-flex" aria-label="Collapse navigation" onClick={() => setCollapsed((value) => !value)}>{collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}</button><button className="icon-button lg:hidden" aria-label="Close navigation" onClick={() => setMobileOpen(false)}><X size={18} /></button></div><OrganizationSwitcher collapsed={collapsed} /><nav className="scrollbar-hide flex-1 space-y-7 overflow-y-auto px-3 py-3">{navSections.map((section) => <div key={section.label}><p className={`nav-section-label ${collapsed ? 'lg:hidden' : ''}`}>{section.label}</p><div className="mt-2 space-y-1">{section.items.map(({ label, path, icon: Icon, badge, accent }) => <NavLink key={path} to={path} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''} ${accent ? 'nav-link-accent' : ''}`}><Icon size={18} /><span className={`truncate ${collapsed ? 'lg:hidden' : ''}`}>{label}</span>{badge && <span className={`nav-badge ${collapsed ? 'lg:hidden' : ''}`}>{badge}</span>}</NavLink>)}</div></div>)}<div><p className={`nav-section-label ${collapsed ? 'lg:hidden' : ''}`}>Manage</p><div className="mt-2 space-y-1"><NavLink to="/app/team" className="nav-link"><Users size={18} /><span className={collapsed ? 'lg:hidden' : ''}>Team</span></NavLink><NavLink to="/app/settings" className="nav-link"><Settings size={18} /><span className={collapsed ? 'lg:hidden' : ''}>Settings</span></NavLink></div></div></nav><div className="border-t border-slate-200/80 p-3"><div className="flex items-center gap-3 rounded-2xl p-2.5"><div className="avatar">JD</div><div className={`min-w-0 flex-1 ${collapsed ? 'lg:hidden' : ''}`}><p className="truncate text-xs font-bold text-ink">Jordan Davis</p><p className="truncate text-[11px] text-slate-400">Administrator</p></div><button className={`icon-button ${collapsed ? 'lg:hidden' : ''}`} aria-label="More profile options"><MoreHorizontal size={16} /></button></div></div></div></aside><AnimatePresence>{mobileOpen && <motion.button initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="sidebar-scrim lg:hidden" aria-label="Close navigation overlay" onClick={() => setMobileOpen(false)} />}</AnimatePresence><div className={`app-main ${collapsed ? 'app-main-collapsed' : ''}`}><header className="topbar"><div className="flex min-w-0 items-center gap-3"><button className="icon-button lg:hidden" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Menu size={19} /></button><div className="hidden items-center gap-2 text-xs font-medium text-slate-400 sm:flex"><span>Workspace</span><span>/</span><span className="font-semibold text-slate-600">{pageTitle}</span></div><h1 className="truncate text-lg font-semibold tracking-[-0.02em] text-ink sm:hidden">{pageTitle}</h1></div><div className="flex items-center gap-2 sm:gap-3"><button className="search-trigger hidden sm:flex"><Search size={16} /><span>Search anything</span><kbd>⌘ K</kbd></button><button className="icon-button relative" aria-label="Notifications"><Bell size={18} /><span className="notification-dot" /></button><div className="avatar avatar-small">JD</div></div></header><main className="mx-auto max-w-[1600px] px-5 pb-12 pt-7 sm:px-7 lg:px-10"><Routes><Route index element={<OverviewPage />} /><Route path="inventory" element={<OperationsPage mode="products" title="Inventory" description="Create, edit, archive, and adjust products with live server validation." />} /><Route path="categories" element={<OperationsPage mode="categories" title="Categories" description="Organize products with server-validated categories and archive controls." />} /><Route path="hubs" element={<OperationsPage mode="hubs" title="Hubs" description="Manage the places where stock is stored across your network." />} /> <Route path="suppliers" element={<OperationsPage mode="suppliers" title="Suppliers" description="Maintain supplier records used by replenishment workflows." />} /><Route path="restock" element={<OperationsPage mode="restocks" title="Restock" description="Create and advance replenishment requests through the verified state machine." />} /><Route path="transfers" element={<OperationsPage mode="transfers" title="Transfers" description="Move stock between hubs with approval, dispatch, and receipt controls." />} /><Route path="reports" element={<WorkspacePage icon={FileText} title="Reports" description="Turn verified movements into operational reports and exports." action="Generate report" />} /><Route path="assistant" element={<AssistantPage />} /><Route path="activity" element={<WorkspacePage icon={Clock3} title="Activity log" description="A durable record of the actions that shape your inventory." />} /><Route path="team" element={<TeamPage />} /><Route path="settings" element={<WorkspacePage icon={Settings} title="Settings" description="Configure your workspace, team, and operational preferences." />} /></Routes></main></div></div>
}

function OverviewPage() {
  const [showNotice, setShowNotice] = useState(true)
  return <div className="space-y-8"><div className="flex flex-col justify-between gap-5 md:flex-row md:items-end"><div><div className="eyebrow">Monday, October 25, 2026</div><h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-ink sm:text-4xl">Good morning, Jordan <span className="text-slate-300">/</span> <span className="text-slate-500">let’s get oriented.</span></h2><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">Your operating picture will become more useful as you connect products, hubs, and movements.</p></div><div className="flex items-center gap-2"><button className="button-secondary px-3.5 py-2.5 text-sm"><Filter size={15} /> Last 30 days <ChevronDown size={14} /></button><button className="button-primary px-3.5 py-2.5 text-sm"><Plus size={16} /> <span className="hidden sm:inline">Quick action</span></button></div></div>{showNotice && <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} className="notice-card"><div className="flex items-start gap-3"><span className="signal-icon signal-blue"><Sparkles size={16} /></span><div><p className="font-semibold text-ink">This is a clean workspace</p><p className="mt-1 text-sm leading-6 text-slate-500">Connect your operational records or seed clearly marked demo data to unlock live KPIs, risk signals, and AI context. Nothing is being estimated behind the scenes.</p></div><button className="icon-button ml-auto shrink-0" aria-label="Dismiss notice" onClick={() => setShowNotice(false)}><X size={16} /></button></div></motion.div>}<LiveMetricGrid /><div className="grid gap-5 xl:grid-cols-[1.35fr_0.65fr]"><div className="panel-card"><div className="flex items-start justify-between"><div><p className="text-sm font-semibold text-ink">Movement & value trend</p><p className="mt-1 text-xs text-slate-400">Real movement history will appear here.</p></div><button className="icon-button" aria-label="More trend options"><MoreHorizontal size={17} /></button></div><div className="empty-chart"><div className="empty-chart-grid" /><div className="relative z-10 flex flex-col items-center"><span className="signal-icon signal-blue"><BarChart3 size={17} /></span><p className="mt-3 text-sm font-semibold text-slate-600">No movement data yet</p><p className="mt-1 text-xs text-slate-400">Receive or issue stock to start seeing the signal.</p></div></div></div><div className="panel-card"><div className="flex items-start justify-between"><div><p className="text-sm font-semibold text-ink">Attention queue</p><p className="mt-1 text-xs text-slate-400">The next best setup steps</p></div><button className="icon-button" aria-label="View all attention items"><ArrowRight size={16} /></button></div><div className="mt-5 space-y-2.5">{attentionItems.map(({ title, description, tone, icon: Icon }) => <button key={title} className="attention-row"><span className={`signal-icon signal-${tone}`}><Icon size={15} /></span><span className="min-w-0 flex-1 text-left"><span className="block text-sm font-semibold text-ink">{title}</span><span className="mt-0.5 block text-xs leading-5 text-slate-400">{description}</span></span><ArrowRight size={15} className="text-slate-300" /></button>)}</div></div></div><div><div className="mb-4 flex items-center justify-between"><div><p className="text-sm font-semibold text-ink">Start with a clear next step</p><p className="mt-1 text-xs text-slate-400">Everything here is designed to leave a clean trail.</p></div></div><div className="grid gap-3 md:grid-cols-3">{quickActions.map(({ label, icon: Icon, path }) => <Link key={label} to={path} className="quick-action"><span className="feature-icon"><Icon size={17} /></span><span className="flex-1 text-sm font-semibold text-ink">{label}</span><ArrowRight size={15} className="text-slate-300" /></Link>)}</div></div></div>
}

function LiveMetricGrid() {
  const enabled = Boolean(authStore.access)
  const { data, isLoading, error } = useQuery({ queryKey: ['dashboard-summary'], queryFn: api.dashboard, enabled, retry: false })
  if (!enabled) return <div className="notice-card"><p className="font-semibold text-ink">Sign in to load live KPIs</p><p className="mt-1 text-sm leading-6 text-slate-500">The shell is available for exploration. Sign in with an API-backed workspace to replace placeholders with verified records.</p><Link className="button-primary mt-4 px-3.5 py-2 text-sm" to="/login">Sign in <ArrowRight size={15} /></Link></div>
  if (isLoading) return <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{['Active products', 'Stock units', 'Inventory value', 'Attention items'].map((label) => <div key={label} className="metric-card animate-pulse"><div className="h-8 w-8 rounded-xl bg-slate-100" /><p className="mt-5 text-sm font-medium text-slate-400">{label}</p><div className="mt-2 h-8 w-24 rounded bg-slate-100" /><div className="mt-2 h-3 w-20 rounded bg-slate-100" /></div>)}</div>
  if (error || !data) return <div className="notice-card border-amber-100 bg-amber-50/70"><p className="font-semibold text-ink">Live data is not available yet</p><p className="mt-1 text-sm leading-6 text-slate-500">{error instanceof Error ? error.message : 'Connect the API and an organization-scoped dashboard will appear here.'}</p></div>
  const attention = data.low_stock_products + data.out_of_stock_products
  const cards: Array<[string, string, string, LucideIcon]> = [['Active products', String(data.active_products), data.data_status === 'live' ? 'Live records' : 'No records yet', Package], ['Stock units', data.stock_units, data.active_hubs ? `${data.active_hubs} active hubs` : 'No hubs yet', Boxes], ['Inventory value', `$${Number(data.inventory_value).toLocaleString()}`, data.data_status === 'live' ? 'From recorded cost' : 'No records yet', BarChart3], ['Attention items', String(attention), attention ? `${data.out_of_stock_products} out of stock` : 'Nothing needs review', Zap]]
  return <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([label, value, change, Icon], index) => <motion.div key={label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.06 }} className="metric-card"><div className="flex items-start justify-between"><span className="metric-icon"><Icon size={17} /></span><MoreHorizontal size={16} className="text-slate-300" /></div><p className="mt-5 text-sm font-medium text-slate-500">{label}</p><p className="mt-1 text-3xl font-semibold tracking-[-0.04em] text-ink">{value}</p><p className="mt-2 text-xs font-medium text-slate-400">{change}</p></motion.div>)}</div>
}


function WorkspacePage({ icon: Icon, title, description, action }: { icon: LucideIcon; title: string; description: string; action?: string }) {
  return <div className="space-y-8"><div className="flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><div className="eyebrow">Workspace / {title}</div><h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-ink sm:text-4xl">{title}</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">{description}</p></div>{action && <button className="button-primary px-4 py-2.5 text-sm"><Plus size={16} /> {action}</button>}</div><div className="panel-card flex min-h-[390px] flex-col items-center justify-center text-center"><span className="feature-icon h-14 w-14 rounded-2xl"><Icon size={24} /></span><h3 className="mt-5 text-xl font-semibold text-ink">Your {title.toLowerCase()} will appear here</h3><p className="mt-2 max-w-md text-sm leading-6 text-slate-500">This view is connected to the workspace shell. Add the first record to replace this empty state with live, permission-aware data.</p><button className="button-secondary mt-6 px-4 py-2.5 text-sm"><Plus size={15} /> Create your first record</button></div></div>
}

function AssistantPage() {
  return <div className="grid gap-6 xl:grid-cols-[0.72fr_1.28fr]"><div><div className="eyebrow">Intelligence / AI Assistant</div><h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-ink sm:text-4xl">Ask the operating picture.</h2><p className="mt-3 max-w-lg text-sm leading-6 text-slate-500">The assistant will answer from your verified records, explain its sources, and ask for confirmation before changing anything.</p><div className="mt-8 space-y-3">{['Which products need restocking?', 'Where is inventory risk rising?', 'Summarize this month’s movements.'].map((prompt) => <button key={prompt} className="prompt-card"><Sparkles size={16} className="text-indigo-500" /><span>{prompt}</span><ArrowRight size={15} className="ml-auto text-slate-300" /></button>)}</div></div><div className="assistant-panel"><div className="flex items-center justify-between border-b border-white/10 px-5 py-4"><div className="flex items-center gap-3"><span className="ai-icon"><Sparkles size={15} /></span><div><p className="text-sm font-semibold text-white">StockPilot AI</p><p className="mt-0.5 text-[11px] text-blue-100/50">Grounded operations assistant</p></div></div><span className="status-pill status-dark"><span className="status-dot" />Ready</span></div><div className="flex min-h-[420px] flex-col items-center justify-center px-6 text-center"><div className="ai-orb"><Sparkles size={22} /></div><h3 className="mt-5 text-lg font-semibold text-white">Your context is waiting</h3><p className="mt-2 max-w-sm text-sm leading-6 text-blue-100/60">Connect inventory records to ask grounded questions about products, hubs, movements, and risk.</p><div className="mt-7 flex w-full max-w-md items-center gap-2 rounded-2xl border border-white/10 bg-white/5 p-2"><span className="flex-1 px-2 text-left text-sm text-blue-100/35">Ask a question about your inventory…</span><button className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500 text-white"><ArrowRight size={16} /></button></div></div></div></div>
}

function Brand({ compact = false, dark = false }: { compact?: boolean; dark?: boolean }) {
  return <Link to="/" className={`flex items-center gap-2.5 ${dark ? 'text-white' : 'text-ink'}`}><span className="brand-mark"><span /><span /><span /></span>{!compact && <span className="text-[15px] font-bold tracking-[-0.03em]">StockPilot <span className="text-signal-600">AI</span></span>}</Link>
}
function MetricCard({ label, value, change, positive }: { label: string; value: string; change: string; positive?: boolean }) { return <div className="rounded-xl border border-slate-200/70 bg-white p-3"><p className="text-[10px] font-semibold text-slate-400">{label}</p><p className="mt-1 text-base font-bold text-ink">{value}</p><p className={`mt-1 text-[9px] font-semibold ${positive ? 'text-emerald-500' : 'text-amber-500'}`}>{change}</p></div> }
function MiniChart() { return <div className="mt-5 h-20"><svg viewBox="0 0 340 90" className="h-full w-full overflow-visible"><defs><linearGradient id="fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#60a5fa" stopOpacity="0.34" /><stop offset="1" stopColor="#60a5fa" stopOpacity="0" /></linearGradient></defs><path d="M0 72 C30 62 42 68 66 51 S105 59 126 42 S161 52 180 32 S218 47 240 26 S286 35 340 10 V90 H0 Z" fill="url(#fill)" /><path d="M0 72 C30 62 42 68 66 51 S105 59 126 42 S161 52 180 32 S218 47 240 26 S286 35 340 10" fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" /></svg></div> }
function SignalCard({ number, title, text, icon: Icon }: { number: string; title: string; text: string; icon: LucideIcon }) { return <div className="rounded-3xl border border-slate-200/70 bg-white p-6 shadow-soft"><div className="flex items-center justify-between"><span className="text-xs font-bold tracking-[0.18em] text-slate-300">{number}</span><span className="feature-icon"><Icon size={17} /></span></div><h3 className="mt-8 text-lg font-semibold text-ink">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-500">{text}</p></div> }

export default App
