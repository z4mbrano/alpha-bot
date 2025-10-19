import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { Copy, Check, Sparkles, Download } from 'lucide-react'
import { Message } from '../contexts/BotContext'
import { exportAlphabotToExcel } from '../services/api'

export default function MessageBubble({ m, onSendMessage }: { m: Message; onSendMessage?: (text: string) => void }) {
  const isUser = m.author === 'user'
  const [copied, setCopied] = useState(false)
  const [downloading, setDownloading] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(m.text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Erro ao copiar:', err)
    }
  }

  const handleDownload = async () => {
    if (!m.sessionId) return
    
    try {
      setDownloading(true)
      await exportAlphabotToExcel(m.sessionId)
    } catch (err) {
      console.error('Erro ao fazer download:', err)
      alert('Erro ao exportar dados. Tente novamente.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <div className={`max-w-[70%] ${isUser ? 'self-end text-white' : 'self-start text-[var(--text)]'} my-1.5 group`}> 
      <div className="relative">
        <div
          className={
            isUser
              ? 'bg-[var(--accent)] bg-[image:var(--accent-gradient)] rounded-tl-2xl rounded-bl-2xl rounded-br-xl p-3 shadow-sm'
              : 'bg-[var(--surface)]/95 backdrop-blur border border-[var(--border)]/60 text-[var(--text)] rounded-tr-2xl rounded-br-2xl rounded-bl-xl p-3 shadow-sm'
          }
        >
          {isUser ? (
            // Mensagens do usuário: texto simples
            <div className="text-sm whitespace-pre-wrap message-content">{m.text}</div>
          ) : (
            // Mensagens do bot: renderizar Markdown
            <div className="text-sm message-content markdown-body">
              <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={{
                // Customizar componentes Markdown
                p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-4 first:mt-0">{children}</h1>,
                h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3 first:mt-0">{children}</h2>,
                h3: ({ children }) => <h3 className="text-base font-bold mb-2 mt-2 first:mt-0">{children}</h3>,
                ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="ml-2">{children}</li>,
                strong: ({ children }) => <strong className="font-bold text-[var(--accent)]">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                code: ({ children, className }) => {
                  const isInline = !className
                  return isInline ? (
                    <code className="bg-[var(--bg)]/50 px-1.5 py-0.5 rounded text-xs font-mono border border-[var(--border)]/40">
                      {children}
                    </code>
                  ) : (
                    <code className="block bg-[var(--bg)]/50 p-3 rounded text-xs font-mono border border-[var(--border)]/40 overflow-x-auto my-2">
                      {children}
                    </code>
                  )
                },
                pre: ({ children }) => <pre className="my-2 overflow-x-auto">{children}</pre>,
                table: ({ children }) => (
                  <div className="overflow-x-auto my-3">
                    <table className="min-w-full border-collapse border border-[var(--border)]">
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => <thead className="bg-[var(--bg)]/30">{children}</thead>,
                tbody: ({ children }) => <tbody>{children}</tbody>,
                tr: ({ children }) => <tr className="border-b border-[var(--border)]">{children}</tr>,
                th: ({ children }) => (
                  <th className="border border-[var(--border)] px-4 py-2 text-left font-bold text-sm">
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td className="border border-[var(--border)] px-4 py-2 text-sm">
                    {children}
                  </td>
                ),
                a: ({ children, href }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[var(--accent)] hover:underline"
                  >
                    {children}
                  </a>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-[var(--accent)] pl-4 my-2 italic text-[var(--text)]/80">
                    {children}
                  </blockquote>
                ),
                hr: () => <hr className="my-4 border-[var(--border)]" />,
              }}
            >
              {m.text}
            </ReactMarkdown>
          </div>
        )}
        </div>
        
        {/* Botões de ação - apenas para mensagens do bot */}
        {!isUser && (
          <div className="absolute -right-10 top-2 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
            {/* Botão de copiar */}
            <button
              onClick={handleCopy}
              className="p-1.5 rounded bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--bg)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
              title={copied ? 'Copiado!' : 'Copiar resposta'}
            >
              {copied ? (
                <Check size={14} className="text-green-400" />
              ) : (
                <Copy size={14} className="text-[var(--muted)]" />
              )}
            </button>
            
            {/* 🚀 SPRINT 2: Botão de download Excel (apenas AlphaBot com sessionId) */}
            {m.botId === 'alphabot' && m.sessionId && (
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="p-1.5 rounded bg-[var(--surface)] border border-[var(--border)] hover:bg-[var(--bg)] focus:outline-none focus:ring-2 focus:ring-[var(--ring)] disabled:opacity-50 disabled:cursor-not-allowed"
                title={downloading ? 'Baixando...' : 'Baixar dados como Excel'}
              >
                <Download 
                  size={14} 
                  className={`text-[var(--muted)] ${downloading ? 'animate-bounce' : ''}`} 
                />
              </button>
            )}
          </div>
        )}
      </div>
      
      {/* 🚀 SPRINT 2: Sugestões de perguntas (apenas mensagens do bot com sugestões) */}
      {!isUser && m.suggestions && m.suggestions.length > 0 && (
        <div className="mt-3 space-y-2">
          <div className="flex items-center gap-2 text-xs text-[var(--muted)] mb-2">
            <Sparkles size={12} />
            <span>Perguntas sugeridas:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {m.suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => onSendMessage?.(suggestion)}
                className="text-xs px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)]/50 hover:bg-[var(--surface)] hover:border-[var(--accent)]/50 transition-all focus:outline-none focus:ring-2 focus:ring-[var(--ring)] text-left"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
