import React, { createContext, useContext, useEffect, useState } from 'react'

// API Base URL - usa variável de ambiente ou localhost para desenvolvimento
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export type BotId = 'alphabot' | 'drivebot'

export type Message = {
  id: string
  author: 'bot' | 'user'
  botId?: BotId
  text: string
  time: number
  isTyping?: boolean
}

const initialMessages: Record<BotId, Message[]> = {
  alphabot: [],
  drivebot: [],
}

type BotContextType = {
  active: BotId
  setActive: (b: BotId) => void
  messages: Message[]
  send: (text: string) => void
  addMessage: (message: Message) => void
  isTyping: boolean
}

const BotContext = createContext<BotContextType | undefined>(undefined)

export function BotProvider({ children }: { children: React.ReactNode }) {
  const [active, setActive] = useState<BotId>('alphabot')
  const [store, setStore] = useState<Record<BotId, Message[]>>(initialMessages)
  const [isTyping, setIsTyping] = useState(false)
  const storageKey = 'alpha-bot:conversation-ids'

  const generateId = () => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID()
    }
    return Math.random().toString(36).slice(2) + Date.now().toString(36)
  }

  const getInitialConversationIds = (): Record<BotId, string> => {
    if (typeof window === 'undefined') {
      return {
        alphabot: generateId(),
        drivebot: generateId(),
      }
    }
    try {
      const stored = window.localStorage.getItem(storageKey)
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<Record<BotId, string>>
        return {
          alphabot: parsed.alphabot ?? generateId(),
          drivebot: parsed.drivebot ?? generateId(),
        }
      }
    } catch (error) {
      console.warn('Não foi possível recuperar os conversation_ids armazenados.', error)
    }
    const fallback = {
      alphabot: generateId(),
      drivebot: generateId(),
    }
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(storageKey, JSON.stringify(fallback))
    }
    return fallback
  }

  const [conversationIds, setConversationIds] = useState<Record<BotId, string>>(() => getInitialConversationIds())

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(storageKey, JSON.stringify(conversationIds))
    }
  }, [conversationIds])

  const addMessage = (message: Message) => {
    // Adiciona mensagem localmente sem chamar o backend
    setStore((s) => ({ ...s, [active]: [...s[active], message] }))
  }

  const send = async (text: string) => {
    const userMsg: Message = {
      id: 'u-' + Date.now(),
      author: 'user',
      text,
      time: Date.now(),
    }
    setStore((s) => ({ ...s, [active]: [...s[active], userMsg] }))

    // Mostrar indicador de digitação
    setIsTyping(true)

    try {
      // AlphaBot usa endpoint diferente
      if (active === 'alphabot') {
        // Verificar se há session_id (arquivos já foram enviados)
        const sessionId = localStorage.getItem('alphabot_session_id')
        
        if (!sessionId) {
          throw new Error('Por favor, anexe planilhas (.csv, .xlsx) primeiro usando o botão de anexo.')
        }

        const response = await fetch(`${API_BASE_URL}/api/alphabot/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            message: text,
          }),
        })

        const data = await response.json()
        
        if (data.error) {
          throw new Error(data.error)
        }

        // Adicionar resposta do bot
        const botMsg: Message = {
          id: 'b-' + Date.now(),
          author: 'bot',
          botId: active,
          text: data.answer,
          time: Date.now(),
        }
        setStore((s) => ({ ...s, [active]: [...s[active], botMsg] }))
        
      } else {
        // DriveBot usa endpoint original
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            bot_id: active,
            message: text,
            conversation_id: conversationIds[active],
          }),
        })

        const data = await response.json()
        
        if (data.error) {
          throw new Error(data.error)
        }

        if (data.conversation_id && data.conversation_id !== conversationIds[active]) {
          setConversationIds((prev) => {
            const next = { ...prev, [active]: data.conversation_id as string }
            return next
          })
        }

        // Adicionar resposta do bot
        const botMsg: Message = {
          id: 'b-' + Date.now(),
          author: 'bot',
          botId: active,
          text: data.response,
          time: Date.now(),
        }
        setStore((s) => ({ ...s, [active]: [...s[active], botMsg] }))
      }

    } catch (error) {
      // Em caso de erro, mostrar mensagem de fallback
      const errorMsg: Message = {
        id: 'e-' + Date.now(),
        author: 'bot',
        botId: active,
        text: `Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, verifique se o backend está rodando.\n\nErro: ${error instanceof Error ? error.message : 'Erro desconhecido'}`,
        time: Date.now(),
      }
      setStore((s) => ({ ...s, [active]: [...s[active], errorMsg] }))
    } finally {
      setIsTyping(false)
    }
  }

  const messages = store[active]

  return (
    <BotContext.Provider value={{ active, setActive, messages, send, addMessage, isTyping }}>{children}</BotContext.Provider>
  )
}export const useBot = () => {
  const c = useContext(BotContext)
  if (!c) throw new Error('useBot must be used inside BotProvider')
  return c
}
