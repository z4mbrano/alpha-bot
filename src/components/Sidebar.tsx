import React, { useEffect, useState } from 'react'
import { Sun, Moon, ChevronLeft, Menu } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useBot, BotId } from '../contexts/BotContext'

const bots: { id: BotId; name: string; icon: string }[] = [
  { id: 'alphabot', name: 'ALPHABOT', icon: '📊' },
  { id: 'drivebot', name: 'DRIVEBOT', icon: '💎' },
]

export default function Sidebar() {
  const { theme, toggle } = useTheme()
  const { active, setActive } = useBot()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  // Listen to global events to control sidebar on mobile
  useEffect(() => {
    const toggleHandler = () => setMobileOpen(o => !o)
    const openHandler = () => setMobileOpen(true)
    const closeHandler = () => setMobileOpen(false)
    window.addEventListener('alpha:toggle-sidebar', toggleHandler)
    window.addEventListener('alpha:open-sidebar', openHandler)
    window.addEventListener('alpha:close-sidebar', closeHandler)
    return () => {
      window.removeEventListener('alpha:toggle-sidebar', toggleHandler)
      window.removeEventListener('alpha:open-sidebar', openHandler)
      window.removeEventListener('alpha:close-sidebar', closeHandler)
    }
  }, [])

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="overlay md:hidden" onClick={() => setMobileOpen(false)} aria-hidden />
      )}

      <aside
        className={`transition-slow z-20 flex flex-col fixed md:static h-full ${collapsed ? 'w-16' : 'w-72'} p-4 border-r border-[var(--border)] bg-[var(--sidebar)] text-[var(--text)] ${mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}
        aria-label="Sidebar de navegação"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            {/* Logo alpha */}
            <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{background: 'var(--accent-gradient)'}}>
              <span className="text-white font-black">α</span>
            </div>
            {!collapsed && (
              <div>
                <div className="text-lg font-extrabold tracking-tight">ALPHA</div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--muted)] -mt-1">INSIGHTS</div>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Toggle collapse (desktop) */}
            <button className="p-2 rounded hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-[var(--ring)] hidden md:inline-flex" onClick={() => setCollapsed(s => !s)} aria-label="Alternar largura da barra lateral">
              <ChevronLeft size={18} className={`${collapsed ? 'rotate-180' : ''} transition-transform`} />
            </button>
            {/* Mobile hamburger */}
            <button className="p-2 rounded hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-[var(--ring)] md:hidden" aria-label="Fechar menu" onClick={() => setMobileOpen(o => !o)}>
              <Menu size={18} />
            </button>
          </div>
        </div>

        {/* Bots */}
        <div className="mt-5">
          {!collapsed && <h4 className="text-[10px] font-semibold text-[var(--muted)] tracking-[0.16em]">BOTS</h4>}
          <div className="mt-3 flex flex-col gap-2">
            {bots.map(b => {
              const isActive = active === b.id
              const iconClass = collapsed
                ? `w-10 h-10 rounded-xl flex items-center justify-center ${isActive ? 'bg-[var(--accent)] text-white' : 'bg-white/5'}`
                : `w-8 h-8 rounded-md flex items-center justify-center ${isActive ? 'bg-white/10' : 'bg-white/5'}`
              const buttonClass = collapsed
                ? 'pressable grid place-items-center p-2 rounded-lg hover:bg-white/5 transition-fast focus:outline-none focus:ring-2 focus:ring-[var(--ring)]'
                : `pressable flex items-center gap-3 p-3 rounded-lg transition-fast focus:outline-none focus:ring-2 focus:ring-[var(--ring)] ${isActive ? 'bg-[var(--accent)] text-white' : 'hover:bg-white/5 text-[var(--text)]'}`
              return (
                <button
                  key={b.id}
                  onClick={() => {
                    setActive(b.id)
                    setMobileOpen(false)
                  }}
                  className={buttonClass}
                  title={b.name}
                  aria-label={b.name}
                >
                  <div className={iconClass}>{b.icon}</div>
                  {!collapsed && (
                    <div className="flex-1 text-left font-semibold tracking-wide truncate whitespace-nowrap">
                      {b.name}
                    </div>
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* spacer + history */}
        <div className="mt-auto pt-4">
          {!collapsed && (
            <>
              <h4 className="text-[10px] font-semibold text-[var(--muted)] tracking-[0.16em]">HISTÓRICO</h4>
              <div className="mt-2 text-xs text-[var(--muted)]">EM MANUTENÇÃO</div>
            </>
          )}

          <div className={`mt-6 flex items-center gap-3 border-t border-[var(--border)] pt-4 ${collapsed ? 'justify-center' : ''}`}>
            {!collapsed && <div className="flex-1 text-sm text-[var(--muted)]">Tema</div>}
            <button onClick={toggle} className="p-2 rounded-md bg-white/5 hover:bg-white/10 transition-fast focus:outline-none focus:ring-2 focus:ring-[var(--ring)]" aria-label="Alternar tema">
              {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}
