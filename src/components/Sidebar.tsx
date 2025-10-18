import React, { useEffect, useState } from 'react'
import { Sun, Moon, Menu, BarChart2, Gem } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useBot, BotId } from '../contexts/BotContext'

const bots: { id: BotId; name: string; icon: React.ReactNode }[] = [
  { id: 'alphabot', name: 'ALPHABOT', icon: <BarChart2 size={18} /> },
  { id: 'drivebot', name: 'DRIVEBOT', icon: <Gem size={18} /> },
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
        className={`transition-slow z-20 flex flex-col fixed md:static h-full ${collapsed ? 'w-16 min-w-16' : 'w-72 min-w-72'} p-4 border-r border-[var(--border)] bg-[var(--sidebar)] text-[var(--text)] ${mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'} overflow-hidden shrink-0`}
        aria-label="Sidebar de navegação"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            {/* Botão de menu (3 traços) no lugar do logo */}
            <button
              className="w-8 h-8 rounded-md grid place-items-center hover:bg-white/10 transition-fast focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
              aria-label="Alternar menu"
              title="Menu"
              onClick={() => {
                if (window.matchMedia('(min-width: 768px)').matches) {
                  setCollapsed((s) => !s)
                } else {
                  setMobileOpen((o) => !o)
                }
              }}
            >
              <Menu size={18} />
            </button>
            {!collapsed && (
              <div>
                <div className="text-lg font-extrabold tracking-tight">ALPHA</div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--muted)] -mt-1">INSIGHTS</div>
              </div>
            )}
          </div>
          {/* Sem controles do lado direito - apenas o menu do lado esquerdo */}
        </div>

        {/* Bots */}
        <div className="mt-5">
          {!collapsed && <h4 className="text-[10px] font-semibold text-[var(--muted)] tracking-[0.16em]">BOTS</h4>}
          <div className="mt-3 flex flex-col gap-2">
            {bots.map(b => {
              const isActive = active === b.id
              const iconClass = collapsed
                ? `w-11 h-11 rounded-xl grid place-items-center transition-transform ${isActive ? 'bg-[var(--accent)] text-white ring-1 ring-[var(--accent)]/40' : 'bg-white/5 hover:bg-white/10 hover:scale-[1.02]'}`
                : `w-8 h-8 rounded-md grid place-items-center ${isActive ? 'bg-white/10 text-[var(--text)]' : 'bg-white/5 text-[var(--muted)]'}`
              const buttonClass = collapsed
                ? 'pressable p-1 rounded-lg transition-fast focus:outline-none focus:ring-2 focus:ring-[var(--ring)] grid place-items-center'
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
                  aria-current={isActive ? 'true' : undefined}
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
