import { FormEvent, useState } from 'react'
import { ArrowRight, LoaderCircle, LockKeyhole, Mail, Sparkles } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { api } from '../lib/api'

export default function AuthPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [organizationName, setOrganizationName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'register') {
        await api.register({ email, password, first_name: firstName, organization_name: organizationName })
      }
      await api.login(email, password)
      navigate('/app')
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to authenticate right now.')
    } finally {
      setLoading(false)
    }
  }

  return <main className="min-h-screen bg-canvas px-5 py-8 text-ink sm:px-8"><div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-5xl items-center justify-center"><div className="grid w-full overflow-hidden rounded-[30px] border border-slate-200/80 bg-white shadow-card lg:grid-cols-[0.86fr_1.14fr]"><section className="hidden bg-ink p-10 text-white lg:block"><div className="flex items-center gap-2.5"><span className="brand-mark"><span /><span /><span /></span><span className="text-[15px] font-bold">StockPilot <span className="text-blue-300">AI</span></span></div><div className="mt-24 max-w-sm"><span className="ai-icon"><Sparkles size={15} /></span><h1 className="mt-6 text-4xl font-semibold leading-tight tracking-[-0.04em]">Make the next operational decision feel obvious.</h1><p className="mt-5 text-sm leading-7 text-blue-100/65">Sign in to a permission-aware workspace where every metric is grounded in your records.</p></div></section><section className="p-7 sm:p-10"><button className="text-sm font-semibold text-slate-500 transition hover:text-ink" onClick={() => navigate('/')}>← Back to StockPilot</button><div className="mt-12 max-w-md"><p className="eyebrow">{mode === 'login' ? 'Secure workspace access' : 'Create your operating workspace'}</p><h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em] text-ink">{mode === 'login' ? 'Welcome back.' : 'Start with a clean workspace.'}</h2><p className="mt-3 text-sm leading-6 text-slate-500">{mode === 'login' ? 'Use your work email to continue to verified inventory context.' : 'Your first organization and owner membership are created transactionally.'}</p><form className="mt-8 space-y-4" onSubmit={submit}>{mode === 'register' && <><label className="field-label">First name<input className="text-input" value={firstName} onChange={(event) => setFirstName(event.target.value)} required /></label><label className="field-label">Organization name<input className="text-input" value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} required /></label></>}<label className="field-label">Work email<div className="input-with-icon"><Mail size={16} /><input value={email} type="email" onChange={(event) => setEmail(event.target.value)} required placeholder="you@company.com" /></div></label><label className="field-label">Password<div className="input-with-icon"><LockKeyhole size={16} /><input value={password} type="password" onChange={(event) => setPassword(event.target.value)} required minLength={8} placeholder="At least 8 characters" /></div></label>{error && <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">{error}</p>}<button className="button-primary w-full justify-center py-3" disabled={loading}>{loading ? <LoaderCircle size={17} className="animate-spin" /> : <ArrowRight size={17} />}{loading ? 'Connecting…' : mode === 'login' ? 'Sign in' : 'Create workspace'}</button></form><button className="mt-6 text-sm font-semibold text-signal-600 hover:text-signal-700" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>{mode === 'login' ? 'Need a workspace? Create one' : 'Already have access? Sign in'}</button></div></section></div></div></main>
}
