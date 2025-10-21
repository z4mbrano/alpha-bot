import React, { useEffect, useState } from 'react'
import { Sun, Moon, Menu, BarChart2, Gem, LogOut, User, Plus, Trash2, MessageSquare, Edit2 } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useBot, BotId } from '../contexts/BotContext'
import { useAuth } from '../contexts/AuthContext'
import { useConversation } from '../contexts/ConversationContext'

const bots: { id: BotId; name: string; icon: React.ReactNode }[] = [
  { id: 'alphabot', name: 'ALPHABOT', icon: <BarChart2 size={18} /> },
  { id: 'drivebot', name: 'DRIVEBOT', icon: <Gem size={18} /> },
]

export default function Sidebar() {
  const { theme, toggle } = useTheme()
  const { active, setActive } = useBot()
  const { user, logout } = useAuth()
  const { conversations, activeConversationId, loading, createNewConversation, switchConversation, deleteConversation, updateConversationTitle } = useConversation()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [newTitle, setNewTitle] = useState('')

  const startRenaming = (conv: any) => {
    setRenamingId(conv.id)
    setNewTitle(conv.title)
  }

  const cancelRenaming = () => {
    setRenamingId(null)
    setNewTitle('')
  }

  const confirmRename = async () => {
    if (renamingId && newTitle.trim()) {
      try {
        await updateConversationTitle(renamingId, newTitle.trim())
        setRenamingId(null)
        setNewTitle('')
      } catch (error) {
        // Erro já tratado no contexto
      }
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      confirmRename()
    } else if (e.key === 'Escape') {
      cancelRenaming()
    }
  }

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
                ? `w-11 h-11 rounded-xl grid place-items-center transition-all ${isActive ? 'bg-[var(--accent)]/10 text-[var(--accent)] ring-1 ring-[var(--accent)]/20' : 'bg-white/5 hover:bg-white/10 hover:scale-[1.02] text-[var(--muted)]'}`
                : `w-8 h-8 rounded-md grid place-items-center transition-all ${isActive ? 'bg-[var(--accent)]/10 text-[var(--accent)]' : 'bg-white/5 text-[var(--muted)] hover:text-[var(--text)]'}`
              const buttonClass = collapsed
                ? 'pressable p-1 rounded-lg transition-fast focus:outline-none focus:ring-2 focus:ring-[var(--ring)] grid place-items-center'
                : `pressable flex items-center gap-3 p-3 rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-[var(--ring)] ${isActive ? 'bg-white/5 text-[var(--accent)]' : 'hover:bg-white/5 text-[var(--text)]'}`
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
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-[10px] font-semibold text-[var(--muted)] tracking-[0.16em]">HISTÓRICO</h4>
                <button
                  onClick={async () => {
                    try {
                      await createNewConversation(active, 'Nova Conversa')
                    } catch (error) {
                      // Erro já tratado no contexto
                    }
                  }}
                  className="p-1.5 rounded-md bg-[var(--accent)]/10 hover:bg-[var(--accent)]/20 text-[var(--accent)] transition-fast"
                  title="Nova conversa"
                >
                  <Plus size={14} />
                </button>
              </div>
              
              {/* Lista de conversas */}
              <div className="space-y-1 max-h-48 overflow-y-auto pr-1 custom-scrollbar">
                {loading ? (
                  <div className="text-xs text-[var(--muted)] text-center py-4">Carregando...</div>
                ) : conversations.length === 0 ? (
                  <div className="text-xs text-[var(--muted)] text-center py-4">Nenhuma conversa ainda</div>
                ) : (
                  conversations
                    .filter(c => c.bot_type === active)
                    .slice(0, 10)
                    .map(conv => (
                      <div
                        key={conv.id}
                        className={`group flex items-center gap-2 p-2 rounded-md transition-fast ${
                          activeConversationId === conv.id
                            ? 'bg-[var(--accent)]/20 border border-[var(--accent)]/30'
                            : 'hover:bg-white/5 border border-transparent'
                        }`}
                      >
                        <MessageSquare size={14} className="text-[var(--muted)] shrink-0" />
                        <div 
                          className="flex-1 min-w-0 cursor-pointer"
                          onClick={() => renamingId !== conv.id && switchConversation(conv.id)}
                        >
                          {renamingId === conv.id ? (
                            <input
                              type="text"
                              value={newTitle}
                              onChange={(e) => setNewTitle(e.target.value)}
                              onKeyDown={handleKeyPress}
                              onBlur={confirmRename}
                              className="w-full text-xs font-medium bg-transparent border border-[var(--accent)] rounded px-1 py-0.5 text-[var(--text)] focus:outline-none"
                              autoFocus
                            />
                          ) : (
                            <div className="text-xs font-medium text-[var(--text)] truncate">
                              {conv.title}
                            </div>
                          )}
                          <div className="text-[10px] text-[var(--muted)]">
                            {new Date(conv.updated_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          {renamingId !== conv.id && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                startRenaming(conv)
                              }}
                              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--accent)]/20 text-[var(--accent)] transition-fast"
                              title="Renomear"
                            >
                              <Edit2 size={12} />
                            </button>
                          )}
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              if (confirm('Deletar esta conversa?')) {
                                deleteConversation(conv.id)
                              }
                            }}
                            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20 text-red-400 transition-fast"
                            title="Deletar"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                    ))
                )}
              </div>
            </>
          )}

          {/* Informações do usuário */}
          <div className={`mt-6 border-t border-[var(--border)] pt-4 ${collapsed ? '' : 'space-y-3'}`}>
            {/* Usuário */}
            {!collapsed && user && (
              <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-[var(--accent)]/10">
                <div className="w-8 h-8 rounded-full bg-[var(--accent)] text-white grid place-items-center font-bold text-sm">
                  {user.username[0].toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-[var(--text)] truncate">{user.username}</div>
                  <div className="text-xs text-[var(--muted)]">Conta Ativa</div>
                </div>
              </div>
            )}

            {/* Controles */}
            <div className={`flex items-center gap-2 ${collapsed ? 'flex-col' : ''}`}>
              {/* Tema */}
              <button 
                onClick={toggle} 
                className="p-2 rounded-md bg-white/5 hover:bg-white/10 transition-fast focus:outline-none focus:ring-2 focus:ring-[var(--ring)]" 
                aria-label="Alternar tema"
                title="Alternar tema"
              >
                {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
              </button>

              {/* Logout */}
              {!collapsed && (
                <button
                  onClick={() => {
                    if (confirm('Deseja fazer logout?')) {
                      logout()
                    }
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-fast focus:outline-none focus:ring-2 focus:ring-red-500/50"
                  title="Sair"
                >
                  <LogOut size={16} />
                  <span className="text-sm font-medium">Sair</span>
                </button>
              )}

              {collapsed && (
                <button
                  onClick={() => {
                    if (confirm('Deseja fazer logout?')) {
                      logout()
                    }
                  }}
                  className="p-2 rounded-md bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-fast focus:outline-none focus:ring-2 focus:ring-red-500/50"
                  aria-label="Sair"
                  title="Sair"
                >
                  <LogOut size={16} />
                </button>
              )}
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
