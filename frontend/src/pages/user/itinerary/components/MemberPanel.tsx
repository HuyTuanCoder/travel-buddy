import React, { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import type {
  MemberListResponse,
  MemberRole,
} from '@/types/itineraryTypes'

// ==================== Props ====================

interface MemberPanelProps {
  members: MemberListResponse
  onInvite: (userId: string, role: MemberRole) => void
  onRemoveMember: (userId: string) => void
  onUpdateRole: (userId: string, role: string) => void
  onTransferOwnership: (userId: string) => void
}

// ==================== Role badge colors ====================

const roleStyles: Record<string, string> = {
  OWNER: 'bg-blue-50 text-blue-700 border-blue-200',
  EDITOR: 'bg-violet-50 text-violet-700 border-violet-200',
  VIEWER: 'bg-slate-50 text-slate-500 border-slate-200',
}

// ==================== Component ====================

export default function MemberPanel({ members, onInvite, onRemoveMember, onUpdateRole, onTransferOwnership }: MemberPanelProps) {
  // Local state for the invite form — simple enough to live here
  const [inviteUserId, setInviteUserId] = useState('')
  const [inviteRole, setInviteRole] = useState<MemberRole>('VIEWER')

  const handleInviteSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!inviteUserId.trim()) return
    onInvite(inviteUserId.trim(), inviteRole)
    setInviteUserId('')
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-5">
      <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wider">
        Members
      </h3>

      {/* --- Confirmed members list --- */}
      <div className="space-y-3">
        {members.members.map((member) => (
          <div
            key={member.userId}
            className="group flex items-center justify-between gap-2"
          >
            <div className="flex items-center gap-2 min-w-0">
              {/* Avatar placeholder — will integrate with user service later */}
              <div className="h-8 w-8 shrink-0 rounded-full bg-slate-100 flex items-center justify-center text-xs font-semibold text-slate-500">
                {member.userId.slice(0, 2).toUpperCase()}
              </div>
              <span className="text-sm text-slate-700 truncate">
                {member.userId}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {member.role !== 'OWNER' ? (
                <select
                  value={member.role}
                  onChange={(e) => onUpdateRole(member.userId, e.target.value)}
                  className={`text-[10px] font-semibold uppercase tracking-wider rounded-full px-2 py-0.5 border outline-none ${roleStyles[member.role] ?? ''}`}
                >
                  <option value="EDITOR">EDITOR</option>
                  <option value="VIEWER">VIEWER</option>
                </select>
              ) : (
                <Badge
                  variant="outline"
                  className={`text-[10px] ${roleStyles[member.role] ?? ''}`}
                >
                  owner
                </Badge>
              )}

              {/* Show Transfer Ownership button only if looking at an EDITOR */}
              {member.role === 'EDITOR' && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 px-2 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity text-blue-600 hover:text-blue-700 bg-blue-50"
                  onClick={() => {
                    if (window.confirm(`Are you sure you want to transfer ownership to ${member.userId}? You will be demoted to an EDITOR.`)) {
                      onTransferOwnership(member.userId)
                    }
                  }}
                >
                  Make Owner
                </Button>
              )}

              {member.role !== 'OWNER' && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-red-400 hover:text-red-600"
                  onClick={() => {
                    if (window.confirm(`Remove ${member.userId} from the itinerary?`)) {
                      onRemoveMember(member.userId)
                    }
                  }}
                >
                  ✕
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* --- Pending invitations --- */}
      {members.pendingInvitations.length > 0 && (
        <>
          <Separator />
          <div className="space-y-3">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Pending
            </p>
            {members.pendingInvitations.map((invite) => (
              <div
                key={invite.id}
                className="flex items-center justify-between gap-2"
              >
                <span className="text-sm text-slate-500 italic truncate">
                  {invite.userId}
                </span>
                <Badge
                  variant="outline"
                  className="text-[10px] bg-amber-50 text-amber-600 border-amber-200"
                >
                  pending
                </Badge>
              </div>
            ))}
          </div>
        </>
      )}

      {/* --- Invite form --- */}
      <Separator />
      <form className="space-y-3" onSubmit={handleInviteSubmit}>
        <p className="text-xs font-medium text-slate-600 uppercase tracking-wider">
          Invite
        </p>
        <Input
          placeholder="User ID"
          value={inviteUserId}
          onChange={(e) => setInviteUserId(e.target.value)}
          required
        />
        <select
          value={inviteRole}
          onChange={(e) => setInviteRole(e.target.value as MemberRole)}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
        >
          <option value="EDITOR">Editor</option>
          <option value="VIEWER">Viewer</option>
        </select>
        <Button type="submit" size="sm" className="w-full">
          Send invite
        </Button>
      </form>
    </div>
  )
}


