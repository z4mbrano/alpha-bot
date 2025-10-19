import React, { useState, useEffect } from 'react'
import { X, RefreshCw, Trash2, Activity, Clock, Database } from 'lucide-react'
import { toast } from 'sonner'
import { getCacheStats, clearCache, type CacheStats } from '../services/api'

interface CacheSettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function CacheSettingsModal({ isOpen, onClose }: CacheSettingsModalProps) {
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [clearing, setClearing] = useState(false)

  const loadStats = async () => {
    try {
      setLoading(true)
      const data = await getCacheStats()
      setStats(data)
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error)
      toast.error('Erro ao carregar estatísticas do cache')
    } finally {
      setLoading(false)
    }
  }

  const handleClearCache = async () => {
    if (!confirm('Tem certeza que deseja limpar todo o cache? As próximas perguntas serão mais lentas.')) {
      return
    }

    try {
      setClearing(true)
      const result = await clearCache()
      toast.success(`✅ Cache limpo: ${result.entries_cleared} entradas removidas`)
      await loadStats() // Recarregar estatísticas
    } catch (error) {
      console.error('Erro ao limpar cache:', error)
      toast.error('Erro ao limpar cache')
    } finally {
      setClearing(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      loadStats()
    }
  }, [isOpen])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Overlay */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-[var(--accent)]/10">
              <Activity size={24} className="text-[var(--accent)]" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-[var(--text)]">Configurações de Cache</h2>
              <p className="text-sm text-[var(--muted)]">Métricas e gerenciamento</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-[var(--bg)] transition-colors"
          >
            <X size={20} className="text-[var(--muted)]" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="animate-spin text-[var(--accent)]" size={32} />
            </div>
          ) : stats ? (
            <div className="space-y-6">
              {/* Métricas principais */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-[var(--bg)] border border-[var(--border)]">
                  <div className="flex items-center gap-2 mb-2">
                    <Database size={16} className="text-[var(--accent)]" />
                    <span className="text-xs text-[var(--muted)]">Entradas</span>
                  </div>
                  <p className="text-2xl font-bold text-[var(--text)]">{stats.total_entries}</p>
                  <p className="text-xs text-[var(--muted)] mt-1">de {stats.max_entries} máx</p>
                </div>

                <div className="p-4 rounded-xl bg-[var(--bg)] border border-[var(--border)]">
                  <div className="flex items-center gap-2 mb-2">
                    <Activity size={16} className="text-green-500" />
                    <span className="text-xs text-[var(--muted)]">Taxa de Acerto</span>
                  </div>
                  <p className="text-2xl font-bold text-[var(--text)]">{stats.hit_rate}%</p>
                  <p className="text-xs text-[var(--muted)] mt-1">{stats.hits} hits</p>
                </div>

                <div className="p-4 rounded-xl bg-[var(--bg)] border border-[var(--border)]">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock size={16} className="text-orange-500" />
                    <span className="text-xs text-[var(--muted)]">Requisições</span>
                  </div>
                  <p className="text-2xl font-bold text-[var(--text)]">{stats.total_requests}</p>
                  <p className="text-xs text-[var(--muted)] mt-1">{stats.misses} misses</p>
                </div>

                <div className="p-4 rounded-xl bg-[var(--bg)] border border-[var(--border)]">
                  <div className="flex items-center gap-2 mb-2">
                    <Database size={16} className="text-blue-500" />
                    <span className="text-xs text-[var(--muted)]">Tamanho</span>
                  </div>
                  <p className="text-2xl font-bold text-[var(--text)]">{stats.cache_size_mb}</p>
                  <p className="text-xs text-[var(--muted)] mt-1">MB</p>
                </div>
              </div>

              {/* Estatísticas detalhadas */}
              <div className="p-4 rounded-xl bg-[var(--bg)] border border-[var(--border)]">
                <h3 className="text-sm font-semibold text-[var(--text)] mb-3">Estatísticas Detalhadas</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-[var(--muted)]">Total de gravações:</span>
                    <span className="text-[var(--text)] font-medium">{stats.sets}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--muted)]">Entradas expiradas:</span>
                    <span className="text-[var(--text)] font-medium">{stats.expired}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--muted)]">Limpezas realizadas:</span>
                    <span className="text-[var(--text)] font-medium">{stats.clears}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--muted)]">Tempo de vida (TTL):</span>
                    <span className="text-[var(--text)] font-medium">{stats.ttl_seconds / 60} minutos</span>
                  </div>
                </div>
              </div>

              {/* Explicação */}
              <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                <p className="text-sm text-[var(--text)]">
                  <strong>💡 O que é o cache?</strong> O cache armazena respostas anteriores para acelerar consultas repetidas.
                  Uma taxa de acerto alta significa que o sistema está respondendo mais rápido usando respostas armazenadas.
                </p>
              </div>

              {/* Ações */}
              <div className="flex gap-3">
                <button
                  onClick={loadStats}
                  disabled={loading}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-[var(--bg)] border border-[var(--border)] hover:border-[var(--accent)] transition-colors disabled:opacity-50"
                >
                  <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                  <span className="font-medium">Atualizar</span>
                </button>

                <button
                  onClick={handleClearCache}
                  disabled={clearing || stats.total_entries === 0}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 transition-colors disabled:opacity-50"
                >
                  <Trash2 size={16} className="text-red-500" />
                  <span className="font-medium text-red-500">Limpar Cache</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-[var(--muted)]">
              Erro ao carregar estatísticas
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
