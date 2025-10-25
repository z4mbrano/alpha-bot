import React, { createContext, useContext, useEffect, useState } from 'react'
import { toast } from 'sonner'
import type { ChartData } from '../types'
import { useAuth } from './AuthContext'
import { useConversation } from './ConversationContext'
import * as api from '../services/api'

// Mapa de mensagens de erro amigáveis
const ERROR_MESSAGES: Record<string, string> = {
  // Erros de rede
  'Failed to fetch': '🔴 Sem conexão com o servidor. Verifique sua internet e tente novamente.',
  'NetworkError': '🔴 Erro de rede. Verifique sua conexão e tente novamente.',
  'TypeError: Failed to fetch': '🔴 Não foi possível conectar ao servidor. Verifique se o backend está rodando.',
  
  // Erros específicos do AlphaBot
  'Por favor, anexe planilhas': '📎 **Primeiro passo:** Clique no botão de anexo 📎 e envie sua planilha (.csv ou .xlsx).\n\nDepois você poderá fazer perguntas sobre os dados!',
  'Sessão não encontrada': '⏱️ Sua sessão expirou. Por favor, envie os arquivos novamente usando o botão de anexo 📎.',
  'session_id': '📁 Sessão não encontrada. Envie seus arquivos novamente para continuar.',
  
  // Erros de autenticação
  'API key not valid': '🔑 Erro de autenticação. Entre em contato com o suporte.',
  'Unauthorized': '🔑 Acesso não autorizado. Verifique suas credenciais.',
  
  // Erros de arquivo
  'File too large': '📦 Arquivo muito grande. O tamanho máximo é 10MB.',
  'Invalid file format': '📄 Formato de arquivo inválido. Use apenas .csv ou .xlsx.',
  'Unsupported file': '❌ Tipo de arquivo não suportado. Use .csv, .xlsx, .xls, .ods ou .tsv.',
  
  // Erros do servidor
  '500': '⚠️ Erro no servidor. Tente novamente em alguns segundos.',
  '503': '🔧 Servidor temporariamente indisponível. Aguarde alguns instantes.',
  '429': '⏸️ Muitas requisições. Aguarde um momento antes de tentar novamente.',
  
  // Erros gerais
  'timeout': '⏱️ Tempo limite excedido. O servidor está demorando para responder.',
  'parse': '🔧 Erro ao processar resposta do servidor. Tente novamente.',
}

/**
 * Função para traduzir erros técnicos em mensagens amigáveis
 */
function getFriendlyErrorMessage(error: unknown): string {
  const errorText = error instanceof Error ? error.message : String(error)
  
  // Verificar se há uma mensagem específica no mapa
  for (const [key, friendlyMsg] of Object.entries(ERROR_MESSAGES)) {
    if (errorText.includes(key)) {
      return friendlyMsg
    }
  }
  
  // Mensagem genérica se não encontrar correspondência
  return `❌ **Algo deu errado**\n\n${errorText}\n\n💡 **Dica:** Tente novamente ou recarregue a página.`
}

// API Base URL - Usa variável de ambiente VITE_API_URL (Railway em produção) ou localhost em dev
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

export type BotId = 'alphabot' | 'drivebot'

export type Message = {
  id: string
  author: 'bot' | 'user'
  botId?: BotId
  text: string
  time: number
  isTyping?: boolean
  suggestions?: string[]  // 🚀 SPRINT 2: Sugestões de perguntas
  sessionId?: string  // 🚀 SPRINT 2: ID da sessão do AlphaBot (para exportar dados)
  conversationId?: string  // 🚀 SPRINT 2: ID da conversa do DriveBot (para exportar dados)
  chart?: ChartData  // 🚀 SPRINT 2: Dados para gráfico automático
  metadata?: {  // 🚀 Metadados da análise (arquivos, registros, etc.)
    files_used?: string[]
    records_analyzed?: number
    columns_available?: number
    date_columns?: string[]
    total_files?: number
  }
}

const initialMessages: Record<BotId, Message[]> = {
  alphabot: [],
  drivebot: [],
}

// Carregar histórico do localStorage
const loadHistoryFromStorage = (): Record<BotId, Message[]> => {
  if (typeof window === 'undefined') return initialMessages
  
  try {
    const stored = window.localStorage.getItem('alpha-bot:message-history')
    if (stored) {
      return JSON.parse(stored) as Record<BotId, Message[]>
    }
  } catch (error) {
    console.warn('Erro ao carregar histórico:', error)
  }
  
  return initialMessages
}

type BotContextType = {
  active: BotId
  setActive: (b: BotId) => void
  messages: Message[]
  send: (text: string) => void
  addMessage: (message: Message) => void
  clearConversation: () => void
  isTyping: boolean
}

const BotContext = createContext<BotContextType | undefined>(undefined)

export function BotProvider({ children }: { children: React.ReactNode }) {
  const [active, setActiveBot] = useState<BotId>('alphabot')
  const [store, setStore] = useState<Record<BotId, Message[]>>(() => loadHistoryFromStorage())
  const [isTyping, setIsTyping] = useState(false)
  const storageKey = 'alpha-bot:conversation-ids'
  
  // 🆕 MULTI-USUÁRIO: Integração com autenticação e conversas
  const { user } = useAuth()
  const { activeConversationId, createNewConversation, switchConversation, getActiveConversation } = useConversation()

  // 🆕 CORREÇÃO: Wrapper para setActive que limpa mensagens ao trocar de bot
  const setActive = (newBotId: BotId) => {
    if (newBotId !== active) {
      console.log(`🔄 Trocando de ${active} → ${newBotId}`)
      
      // Limpar mensagens do NOVO bot antes de trocar
      setStore((s) => ({ ...s, [newBotId]: [] }))
      
      // Se houver conversa ativa mas for do bot errado, limpar também
      const activeConv = getActiveConversation()
      if (activeConv && activeConv.bot_type !== newBotId) {
        console.log(`⚠️ Conversa ativa é do bot "${activeConv.bot_type}", mas você está trocando para "${newBotId}". Limpando tela.`)
      }
    }
    setActiveBot(newBotId)
  }

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

  // Salvar histórico no localStorage sempre que mudar
  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('alpha-bot:message-history', JSON.stringify(store))
    }
  }, [store])
  
  // 🆕 MULTI-USUÁRIO: Carregar mensagens antigas quando trocar de conversa
  useEffect(() => {
    if (activeConversationId && user) {
      const loadMessages = async () => {
        try {
          // 🔍 Verificar se a conversa ativa é do bot correto
          const activeConv = getActiveConversation()
          
          if (!activeConv) {
            console.log('⚠️ Conversa ativa não encontrada')
            setStore((s) => ({ ...s, [active]: [] }))
            return
          }
          
          // 🔒 CORREÇÃO: Só carregar mensagens se a conversa for do bot ativo
          if (activeConv.bot_type !== active) {
            console.log(`🔄 Conversa ${activeConversationId} é do bot "${activeConv.bot_type}", mas você está em "${active}". Limpando mensagens.`)
            setStore((s) => ({ ...s, [active]: [] }))
            return
          }
          
          // 🎯 Usar endpoint específico para AlphaBot
          let messages: any[]
          if (active === 'alphabot') {
            messages = await api.getAlphabotConversationMessages(activeConversationId)
            console.log(`📥 Carregando mensagens do AlphaBot (conversa ${activeConversationId})`)
          } else {
            messages = await api.getConversationMessages(activeConversationId, user.id)
            console.log(`📥 Carregando mensagens do DriveBot (conversa ${activeConversationId})`)
          }
          
          // Converter mensagens do banco para o formato Message
          const convertedMessages: Message[] = messages.map(msg => ({
            id: msg.id,
            author: msg.author === 'user' ? 'user' : 'bot',
            botId: activeConv.bot_type as BotId, // Usar o bot_type da conversa
            text: msg.text,
            time: msg.time,
            suggestions: msg.suggestions,
            chart: msg.chart
          }))
          
          // Atualizar store com mensagens carregadas
          setStore((s) => ({ ...s, [active]: convertedMessages }))
          console.log(`✅ ${convertedMessages.length} mensagens carregadas da conversa ${activeConversationId} (${activeConv.bot_type})`)
        } catch (error) {
          console.error('Erro ao carregar mensagens:', error)
          setStore((s) => ({ ...s, [active]: [] }))
        }
      }
      
      loadMessages()
    } else if (!activeConversationId) {
      // Limpar mensagens se não houver conversa ativa
      setStore((s) => ({ ...s, [active]: [] }))
    }
  }, [activeConversationId, user, active, getActiveConversation])

  const addMessage = (message: Message) => {
    // Adiciona mensagem localmente sem chamar o backend
    setStore((s) => ({ ...s, [active]: [...s[active], message] }))
  }

  const clearConversation = () => {
    // Limpar histórico do bot ativo
    setStore((s) => ({ ...s, [active]: [] }))
    
    // Limpar session_id do AlphaBot se for o bot ativo
    if (active === 'alphabot') {
      localStorage.removeItem('alphabot_session_id')
    }
    
    // Gerar novo conversation_id para DriveBot
    if (active === 'drivebot') {
      const newId = generateId()
      setConversationIds((prev) => ({ ...prev, [active]: newId }))
    }
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
      // 🆕 MULTI-USUÁRIO: Criar conversa automaticamente se não existir
      let conversationId = activeConversationId
      
      if (user && !activeConversationId) {
        // Criar nova conversa automaticamente
        const newConvId = await createNewConversation(active, 'Nova Conversa')
        conversationId = newConvId
        console.log(`✅ Conversa criada automaticamente: ${newConvId}`)
      }
      
      // AlphaBot usa endpoint diferente
      if (active === 'alphabot') {
        // 🆕 MULTI-USUÁRIO: Buscar session_id específico da conversa
        let sessionId = null
        
        if (conversationId) {
          // Buscar session vinculado à conversa
          sessionId = localStorage.getItem(`alphabot_session_${conversationId}`)
        }
        
        // Fallback: buscar session global
        if (!sessionId) {
          sessionId = localStorage.getItem('alphabot_session_id')
        }
        
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
            conversation_id: conversationId,  // 🆕 MULTI-USUÁRIO
            user_id: user?.id  // 🆕 MULTI-USUÁRIO
          }),
        })

        const data = await response.json()
        
        if (data.error) {
          throw new Error(data.error)
        }

        // Adicionar resposta do bot com sugestões (SPRINT 2)
        const botMsg: Message = {
          id: 'b-' + Date.now(),
          author: 'bot',
          botId: active,
          text: data.answer,
          time: Date.now(),
          suggestions: data.suggestions || [],  // 🚀 Sugestões de perguntas
          sessionId: data.session_id,  // 🚀 SPRINT 2: ID da sessão para exportar
          chart: data.chart,  // 🚀 SPRINT 2: Gráfico automático
          metadata: data.metadata  // 🚀 Metadados da análise (arquivos, registros, etc.)
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
            conversation_id: conversationId,  // 🆕 USA conversa ativa
            user_id: user?.id  // 🆕 MULTI-USUÁRIO
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
          suggestions: data.suggestions || [],  // 🚀 Sugestões para DriveBot
          conversationId: data.conversation_id,  // 🚀 SPRINT 2: ID da conversa para export
          chart: data.chart  // 🚀 SPRINT 2: Gráfico automático para DriveBot
        }
        setStore((s) => ({ ...s, [active]: [...s[active], botMsg] }))
      }

    } catch (error) {
      // Em caso de erro, mostrar mensagem amigável
      const friendlyMessage = getFriendlyErrorMessage(error)
      
      // 🚀 SPRINT 2: Toast notification para erros
      toast.error('Erro ao processar mensagem', {
        description: friendlyMessage.substring(0, 100)
      })
      
      const errorMsg: Message = {
        id: 'e-' + Date.now(),
        author: 'bot',
        botId: active,
        text: friendlyMessage,
        time: Date.now(),
      }
      setStore((s) => ({ ...s, [active]: [...s[active], errorMsg] }))
    } finally {
      setIsTyping(false)
    }
  }

  const messages = store[active]

  return (
    <BotContext.Provider value={{ active, setActive, messages, send, addMessage, clearConversation, isTyping }}>{children}</BotContext.Provider>
  )
}export const useBot = () => {
  const c = useContext(BotContext)
  if (!c) throw new Error('useBot must be used inside BotProvider')
  return c
}
