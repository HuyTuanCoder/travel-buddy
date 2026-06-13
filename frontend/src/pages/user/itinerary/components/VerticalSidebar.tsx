import type { LucideIcon } from 'lucide-react'

export default function VerticalSidebar({
  icon: Icon,
  label,
  onClick,
  position,
  tabs
}: {
  icon?: LucideIcon
  label?: string
  onClick?: () => void
  position: 'left' | 'right'
  tabs: { id: string; icon: LucideIcon; label: string; onClick: () => void; isActive?: boolean }[]
}) {
  return (
    <div 
      className="w-14 shrink-0 border-r border-slate-200 flex flex-col items-center py-4 bg-white z-10 space-y-4"
    >
      {tabs.map(tab => (
        <div 
          key={tab.id}
          className={`w-10 h-10 flex items-center justify-center rounded-xl cursor-pointer transition-colors ${
            tab.isActive 
              ? 'bg-blue-50 text-blue-600' 
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
          }`}
          onClick={tab.onClick}
          title={tab.label}
        >
          <tab.icon size={20} />
        </div>
      ))}
    </div>
  )
}
