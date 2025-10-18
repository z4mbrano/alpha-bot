import React, { useState } from 'react'
import { Sun, Moon, ChevronLeft, Menu } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useBot, BotId } from '../contexts/BotContext'

const bots: { id: BotId; name: string; icon: string }[] = [
  { id: 'alphabot', name: 'ANALISTA PLANILHAS', icon: '📊' },
  { id: 'drivebot', name: 'DRIVEBOT', icon: '�️' },
]

export default function Sidebar() {
  const { theme, toggle } = useTheme()
  const { active, setActive } = useBot()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <aside className={`transition-fast flex flex-col ${collapsed ? 'w-16' : 'w-72'} bg-[var(--sidebar)] p-4`}> 
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-2xl font-extrabold">ALPHA</div>
          {!collapsed && <div className="font-bold uppercase">INSIGHTS</div>}
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 rounded hover:bg-slate-600 transition-fast" onClick={() => setCollapsed(s => !s)} aria-label="toggle sidebar">
            <ChevronLeft size={18} className={`${collapsed ? 'rotate-180' : ''} transition-transform`} />
          </button>
          <button className="p-2 rounded hover:bg-slate-600 transition-fast md:hidden" aria-label="open menu" onClick={() => setMobileOpen(o => !o)}>
            <Menu size={18} />
          </button>
        </div>
      </div>

      <div className="mt-6">
        {!collapsed && <h4 className="text-sm text-[var(--muted)]">BOTS:</h4>}
        <div className="mt-3 flex flex-col gap-2">
          {bots.map(b => (
            <button key={b.id} onClick={() => { setActive(b.id); setMobileOpen(false); }} className={`flex items-center gap-3 p-2 rounded hover:bg-[rgba(255,255,255,0.03)] transition-fast ${active===b.id? 'bg-[var(--accent)]/20 ring-1 ring-[var(--accent)]':' '}`}>
              <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-sm">{b.icon}</div>
              {!collapsed && <div className="flex-1 text-left font-medium">{b.name}</div>}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-auto">
        <h4 className="text-xs text-[var(--muted)]">HISTORICO:</h4>
        <div className="mt-2 text-sm text-[var(--muted)]">EM MANUTENÇÃO</div>

        <div className="mt-6 flex items-center gap-3">
          <div className="flex-1 text-sm text-[var(--muted)]">Tema</div>
          <button onClick={toggle} className="p-2 rounded bg-white/5 hover:bg-white/10 transition-fast">
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </div>
    </aside>
  )
}
