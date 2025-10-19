import React, { useEffect, useRef, useState } from 'react'
import { useBot } from '../contexts/BotContext'
import MessageBubble from './MessageBubble'
import { Paperclip, Send, X, Menu, BarChart2, Gem, Loader2, Trash2 } from 'lucide-react'

// Mapa de mensagens de erro amigáveis para upload
const UPLOAD_ERROR_MESSAGES: Record<string, string> = {
  'Failed to fetch': '🔴 Não foi possível conectar ao servidor. Verifique sua internet.',
  'NetworkError': '🔴 Erro de conexão. Tente novamente.',
  'File too large': '📦 Um ou mais arquivos são muito grandes (máx 10MB cada).',
  'Invalid file': '📄 Arquivo inválido. Use apenas .csv, .xlsx, .xls, .ods ou .tsv.',
  '500': '⚠️ Erro no servidor ao processar arquivos. Tente novamente.',
  '413': '📦 Arquivos muito grandes. Reduza o tamanho ou envie menos arquivos.',
}

function getUploadErrorMessage(error: unknown): string {
  const errorText = error instanceof Error ? error.message : String(error)
  
  for (const [key, msg] of Object.entries(UPLOAD_ERROR_MESSAGES)) {
    if (errorText.includes(key)) {
      return msg
    }
  }
  
  return `❌ Erro ao enviar arquivos: ${errorText}`
}

// API Base URL - Em produção usa caminhos relativos, em dev usa localhost
const API_BASE_URL = import.meta.env.PROD 
  ? '' // Produção: caminhos relativos (Vercel roteia /api/* para backend)
  : (import.meta.env.VITE_API_URL || 'http://localhost:5000') // Dev: localhost

export default function ChatArea() {
  const { active, messages, send, addMessage, clearConversation, isTyping } = useBot()
  const [text, setText] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const feedRef = useRef<HTMLDivElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    // scroll to bottom when messages change
    const el = feedRef.current
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages, active, isTyping])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return
    
    // Filtrar apenas .csv e .xlsx
    const validFiles = Array.from(files).filter(file => {
      const ext = file.name.toLowerCase().split('.').pop()
      return ext === 'csv' || ext === 'xlsx'
    })
    
    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles])
    }
    
    // Limpar input para permitir re-seleção do mesmo arquivo
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleRemoveFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleUploadFiles = async () => {
    if (selectedFiles.length === 0) return
    
    setIsUploading(true)
    
    const formData = new FormData()
    selectedFiles.forEach(file => {
      formData.append('files', file)
    })
    
    try {
      // Adicionar mensagem de upload manualmente (sem chamar o backend)
      addMessage({
        id: 'u-' + Date.now(),
        author: 'user',
        text: `📎 Enviando ${selectedFiles.length} arquivo(s): ${selectedFiles.map(f => f.name).join(', ')}`,
        time: Date.now(),
      })
      
      // Upload para backend
      const response = await fetch(`${API_BASE_URL}/api/alphabot/upload`, {
        method: 'POST',
        body: formData,
      })
      
      const data = await response.json()
      
      // Limpar arquivos selecionados
      setSelectedFiles([])
      
      if (response.ok) {
        // Armazenar session_id globalmente
        localStorage.setItem('alphabot_session_id', data.session_id)
        
        // CORREÇÃO #3: Formatar relatório de diagnóstico no frontend (sem chamar LLM)
        const { metadata } = data
        
        // Criar lista de arquivos bem-sucedidos
        const successFiles = metadata.files_success.map((f: string) => `  - \`${f}\``).join('\n')
        
        // Criar lista de arquivos com falha (se houver)
        let failureSection = ''
        if (metadata.files_failed && metadata.files_failed.length > 0) {
          const failedFiles = metadata.files_failed.map((f: any) => `  - \`${f.filename}\` (Motivo: ${f.reason})`).join('\n')
          failureSection = `- **Falha (${metadata.files_failed.length} de ${metadata.files_success.length + metadata.files_failed.length}):**\n${failedFiles}\n`
        }
        
        // Identificar colunas numéricas, categóricas e temporais
        const numericCols = metadata.columns.filter((c: string) => 
          !c.includes('_Ano') && !c.includes('_Mes') && !c.includes('_Trimestre') && 
          (c.toLowerCase().includes('preco') || c.toLowerCase().includes('valor') || c.toLowerCase().includes('quantidade'))
        )
        const dateCols = metadata.date_columns || []
        const categoricalCols = metadata.columns.filter((c: string) => 
          !numericCols.includes(c) && !dateCols.includes(c) && 
          !c.includes('_Ano') && !c.includes('_Mes') && !c.includes('_Trimestre')
        )
        
        // Período identificado (se houver)
        const periodSection = metadata.date_range 
          ? `- **Período Identificado:** ${metadata.date_range.min} até ${metadata.date_range.max}\n` 
          : ''
        
        // Montar relatório completo
        const diagnosticReport = `## 🔍 Relatório de Diagnóstico dos Anexos

**Status:** Leitura, consolidação e diagnóstico finalizados ✅

### � Arquivos Processados
- **Sucesso (${metadata.files_success.length} de ${metadata.files_success.length + (metadata.files_failed?.length || 0)}):**
${successFiles}
${failureSection}
### 📊 Estrutura do Dataset Consolidado
- **Registros Totais:** ${metadata.total_records.toLocaleString('pt-BR')}
- **Colunas Identificadas:** ${metadata.total_columns}
${periodSection}
### 🔬 Qualidade e Capacidades
- **✅ Campos Numéricos (prontos para cálculos):** ${numericCols.length > 0 ? numericCols.map((c: string) => `\`${c}\``).join(', ') : 'Nenhum identificado'}
- **📝 Campos Categóricos (prontos para agrupamento):** ${categoricalCols.length > 0 ? categoricalCols.slice(0, 5).map((c: string) => `\`${c}\``).join(', ') : 'Nenhum identificado'}
- **📅 Campos Temporais (prontos para filtros de período):** ${dateCols.length > 0 ? dateCols.map((c: string) => `\`${c}\``).join(', ') : 'Nenhum identificado'}

**Diagnóstico Concluído.** Estou pronto para responder às suas perguntas sobre os dados consolidados.`
        
        // Adicionar relatório formatado como mensagem do bot
        addMessage({
          id: 'b-' + Date.now(),
          author: 'bot',
          botId: active,
          text: diagnosticReport,
          time: Date.now(),
        })
      } else {
        addMessage({
          id: 'b-' + Date.now(),
          author: 'bot',
          botId: active,
          text: `❌ **Erro no upload**\n\n${data.message}\n\n💡 Verifique se os arquivos estão no formato correto (.csv, .xlsx, .xls, .ods, .tsv).`,
          time: Date.now(),
        })
      }
    } catch (error) {
      const friendlyMessage = getUploadErrorMessage(error)
      
      addMessage({
        id: 'b-' + Date.now(),
        author: 'bot',
        botId: active,
        text: friendlyMessage,
        time: Date.now(),
      })
      setSelectedFiles([])
    } finally {
      setIsUploading(false)
    }
  }

  const onSend = () => {
    if (!text.trim()) return
    send(text.trim())
    setText('')
  }

  const botName = active === 'alphabot' ? 'ALPHABOT' : 'DRIVEBOT'
  const placeholderText = active === 'alphabot'
    ? 'Descreva sua análise ou anexe planilhas...'
    : 'Cole o ID ou URL da pasta do Google Drive...'
  const hasMessages = messages.length > 0
  const botIcon = active === 'alphabot' ? <BarChart2 size={16} /> : <Gem size={16} />
  const botTagline = active === 'alphabot'
    ? 'Envie .csv ou .xlsx e faça perguntas sobre seus dados.'
    : 'Cole o ID/URL da pasta do Google Drive para explorar arquivos.'

  return (
    <main className="flex-1 flex flex-col">
      {/* Header when there are messages */}
      {hasMessages && (
        <header className="sticky top-0 z-10 px-4 md:px-8 py-3 md:py-4 border-b border-[var(--border)] bg-[var(--sidebar)]/90 backdrop-blur app-shell">
          <div className="max-w-[900px] mx-auto flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <button
                className="md:hidden p-2 rounded hover:bg-white/5 focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                aria-label="Abrir menu"
                onClick={() => window.dispatchEvent(new Event('alpha:toggle-sidebar'))}
              >
                <Menu size={18} />
              </button>
              <div className="w-8 h-8 rounded-md grid place-items-center bg-white/5" aria-hidden>
                {botIcon}
              </div>
              <div>
                <div className="leading-none font-extralight text-[var(--accent)]">{botName}</div>
                <div className="text-xs text-[var(--muted)] leading-none mt-1">{botTagline}</div>
              </div>
            </div>
            
            {/* Botão Limpar Conversa */}
            <button
              onClick={() => {
                if (confirm('Deseja limpar toda a conversa? Esta ação não pode ser desfeita.')) {
                  clearConversation()
                }
              }}
              className="p-2 rounded hover:bg-red-500/10 text-red-400 transition-fast focus:outline-none focus:ring-2 focus:ring-red-500/50"
              title="Limpar conversa"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </header>
      )}

      {/* Welcome area (no messages) */}
      {messages.length === 0 ? (
        <div className="flex-1 grid place-items-center px-6 bg-[var(--bg-2)]">
          <div className="text-center max-w-xl">
            <h1 className="tracking-tight font-extralight" style={{fontSize: 'clamp(28px,4vw,40px)'}}>
              <span style={{ color: 'var(--accent)' }}>Welcome to the {botName}</span>
              {/*<span style={{ color: 'var(--text)' }}>{botName}</span>*/}
            </h1>
            <div className="mt-8 bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-6 shadow-xl text-left">
              {active === 'alphabot' ? (
                <>
                  <p className="text-sm md:text-base">Olá, eu sou o <strong>ALPHABOT</strong>. Use o botão de anexo para enviar planilhas (<code>.csv</code>, <code>.xlsx</code>) que você deseja analisar.</p>
                  <ul className="mt-3 text-sm list-disc pl-5 text-[var(--muted)]">
                    <li>Depois do upload, faça perguntas como “Liste os 3 produtos mais caros…”.</li>
                    <li>Campos numéricos e temporais são detectados automaticamente.</li>
                  </ul>
                </>
              ) : (
                <>
                  <p className="text-sm md:text-base">Olá, eu sou o <strong>DRIVEBOT</strong>. Cole o <em>ID</em> ou a <em>URL</em> da pasta do Google Drive para começar.</p>
                  <ul className="mt-3 text-sm list-disc pl-5 text-[var(--muted)]">
                    <li>Suporte a múltiplos arquivos e subpastas.</li>
                    <li>Peça insights, rankings e sumarizações após a indexação.</li>
                  </ul>
                </>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div ref={feedRef} className="flex-1 overflow-auto px-4 md:px-8 py-6 flex flex-col gap-3 transition-fast">
          <div className="max-w-[900px] w-full mx-auto flex flex-col gap-3">
            {messages.map(m => (
              <MessageBubble key={m.id} m={m} />
            ))}
            {isTyping && (
              <div className="max-w-[70%] self-start my-2">
                <div className="bg-[var(--surface)] text-[var(--text)] rounded-tr-2xl rounded-br-2xl rounded-bl-xl p-3 shadow-sm border border-[var(--border)]/60">
                  <div className="flex items-center gap-2 text-[var(--muted)]">
                    <div className="text-sm">
                      {active === 'alphabot' ? 'ALPHABOT' : 'DRIVEBOT'} está digitando
                    </div>
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 bg-[var(--muted)] rounded-full animate-bounce"></div>
                      <div className="w-1.5 h-1.5 bg-[var(--muted)] rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-1.5 h-1.5 bg-[var(--muted)] rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <footer className="px-4 md:px-8 py-3 md:py-5 border-t border-[var(--border)] bg-[var(--bg)]/70 backdrop-blur">
        {/* Arquivos selecionados */}
        {selectedFiles.length > 0 && (
          <div className="mb-3 p-3 bg-[var(--surface)] rounded-lg border border-[var(--border)] max-w-[900px] mx-auto">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-[var(--muted)]">
                {selectedFiles.length} arquivo(s) selecionado(s)
              </span>
              <button
                onClick={handleUploadFiles}
                disabled={isTyping}
                className="px-3 py-1 text-sm rounded bg-[var(--accent)] hover:bg-[var(--accent-hover)] transition-fast text-white disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
              >
                Enviar Arquivos
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 px-3 py-1 bg-[var(--bg)] rounded border border-[var(--border)] text-sm"
                >
                  <span className="truncate max-w-[200px]">{file.name}</span>
                  <button
                    onClick={() => handleRemoveFile(index)}
                    className="hover:bg-white/5 rounded p-1 transition-fast focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Input de mensagem */}
        <div className="max-w-[900px] mx-auto flex items-center gap-3 input-shell px-3 md:px-4 py-2 md:py-2.5 bg-[var(--surface)]">
          {/* Botão de anexo - apenas para AlphaBot */}
          {active === 'alphabot' && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".csv,.xlsx"
                onChange={handleFileSelect}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isTyping || isUploading}
                className="p-2 rounded hover:bg-white/5 transition-fast disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
                title="Anexar planilhas (.csv, .xlsx)"
              >
                <Paperclip size={18} />
              </button>
            </>
          )}
          
          {/* Botão de upload - aparece quando há arquivos selecionados */}
          {active === 'alphabot' && selectedFiles.length > 0 && (
            <button
              onClick={handleUploadFiles}
              disabled={isUploading}
              className="px-3 py-2 rounded-md bg-[var(--accent)] text-white text-sm hover:bg-[var(--accent-hover)] transition-fast disabled:opacity-50 flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
            >
              {isUploading ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>Enviando...</span>
                </>
              ) : (
                <span>📎 Enviar {selectedFiles.length}</span>
              )}
            </button>
          )}
          
          <input 
            value={text} 
            onChange={e => setText(e.target.value)} 
            onKeyDown={e => e.key === 'Enter' && !isTyping && onSend()} 
            placeholder={placeholderText} 
            disabled={isTyping || isUploading}
            className="flex-1 bg-transparent outline-none placeholder:text-[var(--muted)] text-[var(--text)] px-2 py-2 md:py-2 disabled:opacity-50" 
          />
          <button 
            onClick={onSend} 
            disabled={isTyping || isUploading || !text.trim()}
            className={`p-2.5 rounded-md text-white transition-fast focus:outline-none focus:ring-2 focus:ring-[var(--ring)] flex items-center gap-2 ${text.trim() && !isTyping && !isUploading ? 'bg-[var(--accent)] hover:bg-[var(--accent-hover)]' : 'bg-[var(--border)] text-gray-400 cursor-not-allowed'}`}
          >
            {isTyping ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={16} />
            )}
          </button>
        </div>
      </footer>
    </main>
  )
}
