import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useAuth } from './AuthContext'
import { toast } from 'sonner'
import * as api from '../services/api'

export interface Conversation {
  id: string
  user_id: number
  bot_type: string
  title: string
  created_at: string
  updated_at: string
}

interface ConversationContextType {
  conversations: Conversation[]
  activeConversationId: string | null
  loading: boolean
  loadConversations: () => Promise<void>
  createNewConversation: (botType: string, title?: string) => Promise<string>
  switchConversation: (conversationId: string) => void
  deleteConversation: (conversationId: string) => Promise<void>
  updateConversationTitle: (conversationId: string, title: string) => Promise<void>
  getActiveConversation: () => Conversation | null
}

const ConversationContext = createContext<ConversationContextType | undefined>(undefined)

export function ConversationProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Carregar conversas quando usuário logar
  useEffect(() => {
    if (user) {
      loadConversations()
      
      // Restaurar conversa ativa do localStorage
      const savedConversationId = localStorage.getItem('alpha_active_conversation')
      if (savedConversationId) {
        setActiveConversationId(savedConversationId)
      }
    } else {
      // Limpar ao fazer logout
      setConversations([])
      setActiveConversationId(null)
    }
  }, [user])

  const loadConversations = async () => {
    if (!user) return

    try {
      setLoading(true)
      const data = await api.getConversations(user.id)
      setConversations(data)
    } catch (error) {
      console.error('Erro ao carregar conversas:', error)
      toast.error('Erro ao carregar histórico de conversas')
    } finally {
      setLoading(false)
    }
  }

  const createNewConversation = async (botType: string, title: string = 'Nova Conversa'): Promise<string> => {
    if (!user) throw new Error('Usuário não autenticado')

    try {
      const response = await api.createConversation(user.id, botType, title)
      const conversationId = response.conversation_id

      // Recarregar lista de conversas
      await loadConversations()

      // Ativar nova conversa
      setActiveConversationId(conversationId)
      localStorage.setItem('alpha_active_conversation', conversationId)

      toast.success('Nova conversa criada! 💬')
      return conversationId
    } catch (error) {
      console.error('Erro ao criar conversa:', error)
      toast.error('Erro ao criar conversa')
      throw error
    }
  }

  const switchConversation = (conversationId: string) => {
    setActiveConversationId(conversationId)
    localStorage.setItem('alpha_active_conversation', conversationId)
  }

  const deleteConversation = async (conversationId: string) => {
    if (!user) return

    try {
      await api.deleteConversation(conversationId, user.id)
      
      // Remover da lista local
      setConversations(prev => prev.filter(c => c.id !== conversationId))

      // Se estava ativa, desativar
      if (activeConversationId === conversationId) {
        setActiveConversationId(null)
        localStorage.removeItem('alpha_active_conversation')
      }

      toast.success('Conversa deletada')
    } catch (error) {
      console.error('Erro ao deletar conversa:', error)
      toast.error('Erro ao deletar conversa')
    }
  }

  const updateConversationTitle = async (conversationId: string, title: string) => {
    if (!user) return

    try {
      await api.updateConversationTitle(conversationId, user.id, title)
      
      // Atualizar lista local
      setConversations(prev => 
        prev.map(c => c.id === conversationId ? { ...c, title } : c)
      )

      toast.success('Título atualizado')
    } catch (error) {
      console.error('Erro ao atualizar título:', error)
      toast.error('Erro ao atualizar título')
    }
  }

  const getActiveConversation = (): Conversation | null => {
    if (!activeConversationId) return null
    return conversations.find(c => c.id === activeConversationId) || null
  }

  return (
    <ConversationContext.Provider
      value={{
        conversations,
        activeConversationId,
        loading,
        loadConversations,
        createNewConversation,
        switchConversation,
        deleteConversation,
        updateConversationTitle,
        getActiveConversation
      }}
    >
      {children}
    </ConversationContext.Provider>
  )
}

export function useConversation() {
  const context = useContext(ConversationContext)
  if (context === undefined) {
    throw new Error('useConversation deve ser usado dentro de um ConversationProvider')
  }
  return context
}
