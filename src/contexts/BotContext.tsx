import React, { createContext, useContext, useState } from 'react'

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
  alphabot: [
    {
      id: 'a-welcome',
      author: 'bot',
      botId: 'alphabot',
      text: 'Olá, eu sou o AlphaBot. Por favor, use o botão de anexo para enviar as planilhas (.csv, .xlsx) que você deseja analisar.',
      time: Date.now() - 1000,
    },
  ],
  drivebot: [
    {
      id: 'd-welcome',
      author: 'bot',
      botId: 'drivebot',
      text: 'Olá! Eu sou o DriveBot. Para começar, por favor, siga estes dois passos:\n\n1. Envie aqui o ID da pasta do Google Drive que você deseja que eu analise.\n2. Compartilhe a pasta comigo, adicionando o e-mail id-spreadsheet-reader-robot@data-analytics-gc-475218.iam.gserviceaccount.com como Editor.\n\nFicarei aguardando sua confirmação para iniciar a análise.',
      time: Date.now() - 1000,
    },
  ],
}

type BotContextType = {
  active: BotId
  setActive: (b: BotId) => void
  messages: Message[]
  send: (text: string) => void
  isTyping: boolean
}

const BotContext = createContext<BotContextType | undefined>(undefined)

export function BotProvider({ children }: { children: React.ReactNode }) {
  const [active, setActive] = useState<BotId>('alphabot')
  const [store, setStore] = useState<Record<BotId, Message[]>>(initialMessages)
  const [isTyping, setIsTyping] = useState(false)

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
      // Chamar API do backend
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          bot_id: active,
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
        text: data.response,
        time: Date.now(),
      }
      setStore((s) => ({ ...s, [active]: [...s[active], botMsg] }))

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
    <BotContext.Provider value={{ active, setActive, messages, send, isTyping }}>{children}</BotContext.Provider>
  )
}export const useBot = () => {
  const c = useContext(BotContext)
  if (!c) throw new Error('useBot must be used inside BotProvider')
  return c
}
