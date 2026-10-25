import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, MailPlus, RefreshCw, Shield, Trash2, UserRound, X } from 'lucide-react'

import { api, authStore, type InvitationRecord, type MemberRecord } from '../lib/api'

const ROLE_OPTIONS = [
  ['administrator', 'Administrator'],
  ['inventory_manager', 'Inventory Manager'],
  ['hub_operator', 'Hub Operator'],
  ['analyst', 'Analyst'],
  ['viewer', 'Read-only Viewer'],
] as const

const MANAGE_MEMBERS = 'organization.members.manage'
const MANAGE_ROLES = 'organization.roles.manage'

function displayName(member: MemberRecord) {
  return [member.first_name, member.last_name].filter(Boolean).join(' ') || member.email
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value))
}

export default function TeamPage() {
  const enabled = Boolean(authStore.access)
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('viewer')
  const [feedback, setFeedback] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const meQuery = useQuery({ queryKey: ['me'], queryFn: api.me, enabled, retry: false })
  const membersQuery = useQuery({ queryKey: ['members'], queryFn: api.members, enabled, retry: false })
  const invitationsQuery = useQuery({ queryKey: ['invitations'], queryFn: api.invitations, enabled, retry: false })
  const permissionsQuery = useQuery({ queryKey: ['organization-permissions'], queryFn: api.permissions, enabled, retry: false })

  const activeOrganizationId = meQuery.data?.active_organization?.id
  const currentMembership = meQuery.data?.memberships.find((item) => item.organization === activeOrganizationId && item.is_active)
  const permissions = useMemo(() => new Set(permissionsQuery.data?.find((item) => item.role === currentMembership?.role)?.permissions ?? []), [currentMembership?.role, permissionsQuery.data])
  const canManageMembers = permissions.has(MANAGE_MEMBERS)
  const canManageRoles = permissions.has(MANAGE_ROLES)

  const inviteMutation = useMutation({
    mutationFn: api.inviteMember,
    onSuccess: (result) => {
      setEmail('')
      setToken(result.invitation_token ?? null)
      setFeedback({ tone: 'success', text: `Invitation prepared for ${result.email}.` })
      void queryClient.invalidateQueries({ queryKey: ['invitations'] })
    },
    onError: (error) => setFeedback({ tone: 'error', text: error instanceof Error ? error.message : 'The invitation could not be created.' }),
  })

  const roleMutation = useMutation({
    mutationFn: ({ id, nextRole }: { id: number; nextRole: string }) => api.updateMemberRole(id, nextRole),
    onSuccess: () => {
      setFeedback({ tone: 'success', text: 'Member role updated.' })
      void queryClient.invalidateQueries({ queryKey: ['members'] })
      void queryClient.invalidateQueries({ queryKey: ['me'] })
    },
    onError: (error) => setFeedback({ tone: 'error', text: error instanceof Error ? error.message : 'The role could not be updated.' }),
  })

  const removeMutation = useMutation({
    mutationFn: api.removeMember,
    onSuccess: () => {
      setFeedback({ tone: 'success', text: 'Member removed from this organization.' })
      void queryClient.invalidateQueries({ queryKey: ['members'] })
    },
    onError: (error) => setFeedback({ tone: 'error', text: error instanceof Error ? error.message : 'The member could not be removed.' }),
  })

  const invitationMutation = useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'cancel' | 'resend' }) => action === 'cancel' ? api.cancelInvitation(id) : api.resendInvitation(id),
    onSuccess: (result, variables) => {
      setToken(result.invitation_token ?? null)
      setFeedback({ tone: 'success', text: variables.action === 'resend' ? `Invitation refreshed for ${result.email}.` : 'Invitation canceled.' })
      void queryClient.invalidateQueries({ queryKey: ['invitations'] })
    },
    onError: (error) => setFeedback({ tone: 'error', text: error instanceof Error ? error.message : 'The invitation could not be updated.' }),
  })

  if (!enabled) return <div className="notice-card"><p className="font-semibold text-ink">Sign in to manage your team</p><p className="mt-1 text-sm leading-6 text-slate-500">Team access is always scoped to the active organization and is never loaded from placeholder data.</p></div>
  if (membersQuery.isLoading || invitationsQuery.isLoading || permissionsQuery.isLoading || meQuery.isLoading) return <div className="panel-card animate-pulse"><div className="h-6 w-48 rounded bg-slate-100" /><div className="mt-5 h-24 rounded-2xl bg-slate-100" /><div className="mt-3 h-24 rounded-2xl bg-slate-100" /></div>
  if (membersQuery.error || invitationsQuery.error || permissionsQuery.error || meQuery.error) return <div className="notice-card border-amber-100 bg-amber-50/70"><p className="font-semibold text-ink">Team data is not available</p><p className="mt-1 text-sm leading-6 text-slate-600">{(membersQuery.error ?? invitationsQuery.error ?? permissionsQuery.error ?? meQuery.error) instanceof Error ? (membersQuery.error ?? invitationsQuery.error ?? permissionsQuery.error ?? meQuery.error)?.message : 'The API did not return organization-scoped team data.'}</p></div>

  const members = membersQuery.data ?? []
  const invitations = invitationsQuery.data ?? []
  const pendingInvitations = invitations.filter((item) => item.status === 'pending')
  const busy = inviteMutation.isPending || roleMutation.isPending || removeMutation.isPending || invitationMutation.isPending

  function submitInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFeedback(null)
    setToken(null)
    inviteMutation.mutate({ email: email.trim(), role })
  }

  function updateRole(member: MemberRecord, nextRole: string) {
    if (nextRole === member.role || !window.confirm(`Change ${displayName(member)} to ${ROLE_OPTIONS.find(([value]) => value === nextRole)?.[1] ?? nextRole}?`)) return
    roleMutation.mutate({ id: member.id, nextRole })
  }

  function removeMember(member: MemberRecord) {
    if (window.confirm(`Remove ${displayName(member)} from this organization? This revokes their active access.`)) removeMutation.mutate(member.id)
  }

  return <div className="space-y-8">
    <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><div className="eyebrow">Manage / Team</div><h2 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-ink sm:text-4xl">People and access</h2><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">Invite the right operators, keep roles intentional, and leave a clear audit trail for every access change.</p></div><div className="status-pill status-success"><span className="status-dot" />Server-enforced access</div></div>
    {feedback && <div className={`notice-card ${feedback.tone === 'error' ? 'border-rose-100 bg-rose-50/70' : 'border-emerald-100 bg-emerald-50/70'}`}><div className="flex items-start gap-3"><span className={`signal-icon ${feedback.tone === 'error' ? 'signal-danger' : 'signal-success'}`}>{feedback.tone === 'error' ? <X size={15} /> : <Check size={15} />}</span><p className="text-sm leading-6 text-slate-700">{feedback.text}</p><button className="icon-button ml-auto" aria-label="Dismiss message" onClick={() => setFeedback(null)}><X size={15} /></button></div></div>}
    {token && <div className="notice-card border-indigo-100 bg-indigo-50/70"><p className="font-semibold text-indigo-950">Invitation token ready for delivery</p><p className="mt-1 text-sm leading-6 text-indigo-900/70">No email provider is configured, so the API returned the one-time token for a trusted delivery workflow. It will not be shown again.</p><code className="mt-3 block overflow-x-auto rounded-xl bg-white/80 p-3 text-xs text-indigo-950">{token}</code></div>}
    {!canManageMembers && <div className="notice-card"><div className="flex items-start gap-3"><span className="signal-icon signal-blue"><Shield size={16} /></span><div><p className="font-semibold text-ink">View-only team access</p><p className="mt-1 text-sm leading-6 text-slate-500">Your {currentMembership?.role ?? 'current'} role can view members but cannot invite, remove, or change access.</p></div></div></div>}
    {canManageMembers && <form className="panel-card" onSubmit={submitInvite}><div className="flex items-start gap-3"><span className="feature-icon"><MailPlus size={18} /></span><div><h3 className="font-semibold text-ink">Invite a teammate</h3><p className="mt-1 text-xs leading-5 text-slate-400">The invitation is scoped to this organization and expires in seven days.</p></div></div><div className="mt-5 grid gap-3 md:grid-cols-[1fr_220px_auto]"><label className="sr-only" htmlFor="invite-email">Email address</label><input id="invite-email" className="input-field" type="email" required placeholder="operator@company.com" value={email} onChange={(event) => setEmail(event.target.value)} /><label className="sr-only" htmlFor="invite-role">Role</label><select id="invite-role" className="input-field" value={role} onChange={(event) => setRole(event.target.value)}>{ROLE_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><button className="button-primary justify-center px-4 py-2.5 text-sm" disabled={busy}><MailPlus size={16} /> Invite</button></div></form>}
    <section className="panel-card"><div className="flex items-center justify-between"><div><h3 className="font-semibold text-ink">Active members</h3><p className="mt-1 text-xs text-slate-400">{members.length} member{members.length === 1 ? '' : 's'} in the active organization</p></div><UserRound size={18} className="text-slate-300" /></div><div className="mt-5 overflow-x-auto"><table className="w-full min-w-[680px] text-left text-sm"><thead className="border-b border-slate-100 text-xs uppercase tracking-[0.12em] text-slate-400"><tr><th className="pb-3 font-semibold">Person</th><th className="pb-3 font-semibold">Role</th><th className="pb-3 font-semibold">Joined</th><th className="pb-3 text-right font-semibold">Actions</th></tr></thead><tbody className="divide-y divide-slate-100">{members.map((member) => <tr key={member.id}><td className="py-4"><div className="flex items-center gap-3"><span className="avatar avatar-small">{(member.first_name || member.email).slice(0, 2).toUpperCase()}</span><div><p className="font-semibold text-ink">{displayName(member)}</p><p className="text-xs text-slate-400">{member.email}</p></div></div></td><td className="py-4">{canManageRoles && member.role !== 'owner' ? <select className="input-field max-w-[190px] py-2 text-xs" value={member.role} disabled={busy} onChange={(event) => updateRole(member, event.target.value)}>{ROLE_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select> : <span className="status-pill">{member.role_label}</span>}</td><td className="py-4 text-xs text-slate-500">{formatDate(member.joined_at)}</td><td className="py-4 text-right">{canManageMembers && member.role !== 'owner' && member.user_id !== meQuery.data?.id && <button className="icon-button text-rose-500 hover:bg-rose-50" aria-label={`Remove ${displayName(member)}`} disabled={busy} onClick={() => removeMember(member)}><Trash2 size={16} /></button>}</td></tr>)}</tbody></table>{members.length === 0 && <div className="empty-state mt-4"><UserRound size={20} /><p>No active members found.</p></div>}</div></section>
    <section className="panel-card"><div className="flex items-center justify-between"><div><h3 className="font-semibold text-ink">Invitations</h3><p className="mt-1 text-xs text-slate-400">Pending invites are visible only inside this organization.</p></div><MailPlus size={18} className="text-slate-300" /></div><div className="mt-5 space-y-2">{pendingInvitations.map((invitation: InvitationRecord) => <div key={invitation.id} className="flex flex-col gap-3 rounded-2xl border border-slate-100 bg-slate-50/60 p-3 sm:flex-row sm:items-center"><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-ink">{invitation.email}</p><p className="mt-1 text-xs text-slate-400">{invitation.role_label} · expires {formatDate(invitation.expires_at)}</p></div>{canManageMembers && <div className="flex items-center gap-2"><button className="button-secondary px-3 py-2 text-xs" disabled={busy} onClick={() => invitationMutation.mutate({ id: invitation.id, action: 'resend' })}><RefreshCw size={14} /> Resend</button><button className="button-secondary px-3 py-2 text-xs text-rose-600" disabled={busy} onClick={() => { if (window.confirm(`Cancel the invitation for ${invitation.email}?`)) invitationMutation.mutate({ id: invitation.id, action: 'cancel' }) }}><X size={14} /> Cancel</button></div>}</div>)}{pendingInvitations.length === 0 && <div className="empty-state"><MailPlus size={20} /><p>No pending invitations.</p></div>}</div></section>
  </div>
}
