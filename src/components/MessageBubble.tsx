import React from 'react'
import { Message } from '../contexts/BotContext'

export default function MessageBubble({ m }: { m: Message }) {
  const isUser = m.author === 'user'
  return (
    <div className={`max-w-[70%] ${isUser ? 'self-end text-white' : 'self-start text-[var(--text)]'} my-2`}> 
      <div className={`${isUser ? 'bg-[var(--accent)] rounded-tl-2xl rounded-bl-2xl rounded-br-xl p-3' : 'bg-[#f3f4f6] text-[#111827] rounded-tr-2xl rounded-br-2xl rounded-bl-xl p-3'}`}>
        <div className="text-sm">{m.text}</div>
      </div>
    </div>
  )
}
