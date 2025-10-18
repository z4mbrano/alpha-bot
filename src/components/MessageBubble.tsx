import React from 'react'
import { Message } from '../contexts/BotContext'

export default function MessageBubble({ m }: { m: Message }) {
  const isUser = m.author === 'user'
  return (
    <div className={`max-w-[70%] ${isUser ? 'self-end text-white' : 'self-start text-[var(--text)]'} my-1.5`}> 
      <div className={`${isUser 
          ? 'bg-[var(--accent)] rounded-tl-2xl rounded-bl-2xl rounded-br-xl p-3 shadow-sm'
          : 'bg-[var(--surface)] border border-[var(--border)]/60 text-[var(--text)] rounded-tr-2xl rounded-br-2xl rounded-bl-xl p-3 shadow-sm'}`}>
        <div className="text-sm whitespace-pre-wrap message-content">{m.text}</div>
      </div>
    </div>
  )
}
