/**
 * useChat Hook
 * Hook para gerenciar comunicação com os bots (AlphaBot e DriveBot)
 */

import { useState, useCallback } from 'react'
import { sendAlphabotMessage, sendDrivebotMessage } from '../services/api'
import type { BotId, Message } from '../types'

interface UseChatOptions {
  botId: BotId
  sessionId?: string // Para AlphaBot
  conversationId?: string // Para DriveBot
  onConversationIdChange?: (newId: string) => void
}

export function useChat(options: UseChatOptions) {
  const { botId, sessionId, conversationId, onConversationIdChange } = options
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Envia uma mensagem para o bot
   * @param message - Texto da mensagem
   * @returns Mensagem de resposta do bot ou null em caso de erro
   */
  const sendMessage = useCallback(
    async (message: string): Promise<Message | null> => {
      if (!message.trim()) {
        setError('Mensagem vazia')
        return null
      }

      setIsLoading(true)
      setError(null)

      try {
        if (botId === 'alphabot') {
          // AlphaBot requer session_id
          if (!sessionId) {
            throw new Error(
              'Por favor, anexe planilhas (.csv, .xlsx) primeiro usando o botão de anexo.'
            )
          }

          const response = await sendAlphabotMessage(sessionId, message)

          // Criar mensagem do bot
          const botMessage: Message = {
            id: 'b-' + Date.now(),
            author: 'bot',
            botId: 'alphabot',
            text: response.answer,
            time: Date.now(),
          }

          return botMessage
        } else {
          // DriveBot
          const response = await sendDrivebotMessage(message, conversationId)

          // Atualizar conversation_id se mudou
          if (
            response.conversation_id &&
            response.conversation_id !== conversationId &&
            onConversationIdChange
          ) {
            onConversationIdChange(response.conversation_id)
          }

          // Criar mensagem do bot
          const botMessage: Message = {
            id: 'b-' + Date.now(),
            author: 'bot',
            botId: 'drivebot',
            text: response.response,
            time: Date.now(),
          }

          return botMessage
        }
      } catch (err) {
        const errorMsg =
          err instanceof Error
            ? err.message
            : 'Erro desconhecido ao enviar mensagem'

        setError(errorMsg)

        // Criar mensagem de erro
        const errorMessage: Message = {
          id: 'e-' + Date.now(),
          author: 'bot',
          botId,
          text: `Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, verifique se o backend está rodando.\n\nErro: ${errorMsg}`,
          time: Date.now(),
        }

        return errorMessage
      } finally {
        setIsLoading(false)
      }
    },
    [botId, sessionId, conversationId, onConversationIdChange]
  )

  /**
   * Limpa o erro atual
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  return {
    sendMessage,
    isLoading,
    error,
    clearError,
  }
}
