import React, { useEffect, useRef, useState } from 'react'
import { useBot } from '../contexts/BotContext'
import MessageBubble from './MessageBubble'
import { Paperclip, Send } from 'lucide-react'

export default function ChatArea() {
  const { active, messages, send, isTyping } = useBot()
  const [text, setText] = useState('')
  const feedRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    // scroll to bottom when messages change
    const el = feedRef.current
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages, active, isTyping])

  const onSend = () => {
    if (!text.trim()) return
    send(text.trim())
    setText('')
  }

  const botName = active === 'alphabot' ? 'Analista de Planilhas' : 'DriveBot'
  const placeholderText = active === 'alphabot' 
    ? 'Descreva sua análise ou anexe planilhas...' 
    : 'Cole o ID ou URL da pasta do Google Drive...'

  return (
    <main className="flex-1 flex flex-col">
      <header className="p-6 border-b border-[rgba(255,255,255,0.04)] flex flex-col">
        <div className="text-2xl font-bold">HELLO, USER</div>
        <div className="text-sm text-[var(--muted)] mt-1">WELCOME TO THE {botName.toUpperCase()}</div>
      </header>

      <div ref={feedRef} className="flex-1 overflow-auto p-6 flex flex-col gap-2 bg-[var(--bg-2)] transition-fast">
        {messages.map(m => (
          <MessageBubble key={m.id} m={m} />
        ))}
        {isTyping && (
          <div className="max-w-[70%] self-start my-2">
            <div className="bg-[#f3f4f6] text-[#111827] rounded-tr-2xl rounded-br-2xl rounded-bl-xl p-3">
              <div className="flex items-center gap-2">
                <div className="text-sm text-gray-500">
                  {active === 'alphabot' ? 'Analista de Planilhas' : 'DriveBot'} está digitando
                </div>
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <footer className="p-4 border-t border-[rgba(255,255,255,0.03)] flex items-center gap-3">
        <button className="p-2 rounded hover:bg-white/5 transition-fast"><Paperclip size={18} /></button>
        <input 
          value={text} 
          onChange={e => setText(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && !isTyping && onSend()} 
          placeholder={placeholderText} 
          disabled={isTyping}
          className="flex-1 p-3 rounded bg-[var(--bg)] border border-[rgba(255,255,255,0.04)] outline-none focus:ring-2 focus:ring-[var(--accent)] transition-fast disabled:opacity-50" 
        />
        <button 
          onClick={onSend} 
          disabled={isTyping || !text.trim()}
          className="p-3 rounded bg-[var(--accent)] hover:brightness-90 transition-fast text-white disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send size={16} />
        </button>
      </footer>
    </main>
  )
}
