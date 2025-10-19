/**
 * API Service
 * Cliente TypeScript para comunicação com o backend Alpha Bot
 */

import type {
  AlphabotUploadResponse,
  AlphabotChatResponse,
  AlphabotSessionInfo,
  AlphabotChatRequest,
  DrivebotChatResponse,
  DrivebotChatRequest,
  DrivebotConversationInfo,
  HealthResponse,
  ErrorResponse,
} from '../types'

// Configuração da URL da API
// Em produção (Vercel): usa '' (vazio) para caminhos relativos (ex: /api/...)
// Em desenvolvimento: usa variável de ambiente ou http://localhost:5000
const API_BASE_URL = import.meta.env.PROD 
  ? '' // Produção: usa caminhos relativos, Vercel roteia /api/* para backend
  : (import.meta.env.VITE_API_URL || 'http://localhost:5000') // Dev: localhost

/**
 * Classe de erro customizada para erros da API
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: ErrorResponse
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Helper para fazer requisições HTTP
 */
async function fetchWithErrorHandling<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(url, options)

    // Tentar parsear JSON
    const data = await response.json()

    // Se não for 2xx, lançar erro
    if (!response.ok) {
      const errorMsg = (data as ErrorResponse).error || 'Erro desconhecido'
      throw new ApiError(errorMsg, response.status, data as ErrorResponse)
    }

    return data as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    
    if (error instanceof Error) {
      throw new ApiError(
        `Erro de rede: ${error.message}. Verifique se o backend está rodando.`,
        0
      )
    }
    
    throw new ApiError('Erro desconhecido ao comunicar com o servidor', 0)
  }
}

// ============================================================================
// ALPHABOT API
// ============================================================================

/**
 * Faz upload de arquivos para o AlphaBot
 * @param files - Array de arquivos (CSV, XLSX)
 * @param onProgress - Callback para progresso do upload (opcional)
 * @returns Informações da sessão criada
 */
export async function uploadAlphabotFiles(
  files: File[],
  onProgress?: (progress: { loaded: number; total: number; percentage: number }) => void
): Promise<AlphabotUploadResponse> {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()

    // Listener de progresso
    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress({
            loaded: e.loaded,
            total: e.total,
            percentage: Math.round((e.loaded / e.total) * 100),
          })
        }
      })
    }

    // Listener de conclusão
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const data = JSON.parse(xhr.responseText) as AlphabotUploadResponse
          resolve(data)
        } catch (error) {
          reject(new ApiError('Erro ao parsear resposta do servidor', xhr.status))
        }
      } else {
        try {
          const errorData = JSON.parse(xhr.responseText) as ErrorResponse
          reject(new ApiError(errorData.error || 'Erro ao fazer upload', xhr.status, errorData))
        } catch {
          reject(new ApiError('Erro ao fazer upload', xhr.status))
        }
      }
    })

    // Listener de erro
    xhr.addEventListener('error', () => {
      reject(new ApiError('Erro de rede ao fazer upload', 0))
    })

    // Enviar requisição
    xhr.open('POST', `${API_BASE_URL}/api/alphabot/upload`)
    xhr.send(formData)
  })
}

/**
 * Envia mensagem para o AlphaBot
 * @param sessionId - ID da sessão (obtido no upload)
 * @param message - Mensagem do usuário
 * @returns Resposta do bot
 */
export async function sendAlphabotMessage(
  sessionId: string,
  message: string
): Promise<AlphabotChatResponse> {
  const body: AlphabotChatRequest = {
    session_id: sessionId,
    message,
  }

  return fetchWithErrorHandling<AlphabotChatResponse>(
    `${API_BASE_URL}/api/alphabot/chat`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }
  )
}

/**
 * Obtém informações sobre uma sessão do AlphaBot
 * @param sessionId - ID da sessão
 * @returns Informações da sessão
 */
export async function getAlphabotSession(
  sessionId: string
): Promise<AlphabotSessionInfo> {
  return fetchWithErrorHandling<AlphabotSessionInfo>(
    `${API_BASE_URL}/api/alphabot/session/${sessionId}`
  )
}

/**
 * Remove uma sessão do AlphaBot
 * @param sessionId - ID da sessão
 * @returns Mensagem de confirmação
 */
export async function deleteAlphabotSession(
  sessionId: string
): Promise<{ message: string; session_id: string }> {
  return fetchWithErrorHandling<{ message: string; session_id: string }>(
    `${API_BASE_URL}/api/alphabot/session/${sessionId}`,
    {
      method: 'DELETE',
    }
  )
}

/**
 * 🚀 SPRINT 2: Exporta dados da sessão como arquivo Excel
 * @param sessionId - ID da sessão
 * @returns Promise que resolve quando o download inicia
 */
export async function exportAlphabotToExcel(sessionId: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/alphabot/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new ApiError(
        errorData.error || 'Erro ao exportar dados',
        response.status
      )
    }

    // Obter blob do arquivo
    const blob = await response.blob()
    
    // Extrair nome do arquivo do header (se disponível)
    const contentDisposition = response.headers.get('content-disposition')
    let filename = 'alpha_insights_export.xlsx'
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    // Criar URL temporária e forçar download
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    
    // Limpeza
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError('Erro ao fazer download do arquivo', 0)
  }
}

/**
 * 🚀 SPRINT 2: Exporta dados do DriveBot como arquivo Excel
 * @param conversationId - ID da conversação
 * @returns Promise que resolve quando o download inicia
 */
export async function exportDrivebotToExcel(conversationId: string): Promise<void> {
  try {
    console.log('[EXPORT DRIVEBOT] Iniciando export com conversationId:', conversationId)
    console.log('[EXPORT DRIVEBOT] URL:', `${API_BASE_URL}/api/drivebot/export`)
    
    const response = await fetch(`${API_BASE_URL}/api/drivebot/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ conversation_id: conversationId }),
    })

    console.log('[EXPORT DRIVEBOT] Response status:', response.status)
    console.log('[EXPORT DRIVEBOT] Response ok:', response.ok)

    if (!response.ok) {
      const errorData = await response.json()
      console.log('[EXPORT DRIVEBOT] Error data:', errorData)
      throw new ApiError(
        errorData.error || 'Erro ao exportar dados',
        response.status
      )
    }

    // Obter blob do arquivo
    const blob = await response.blob()
    
    // Extrair nome do arquivo do header (se disponível)
    const contentDisposition = response.headers.get('content-disposition')
    let filename = 'drivebot_export.xlsx'
    
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    // Criar URL temporária e forçar download
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    
    // Limpeza
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError('Erro ao fazer download do arquivo', 0)
  }
}

// ============================================================================
// DRIVEBOT API
// ============================================================================

/**
 * Envia mensagem para o DriveBot
 * @param message - Mensagem do usuário
 * @param conversationId - ID da conversação (opcional)
 * @returns Resposta do bot com conversation_id
 */
export async function sendDrivebotMessage(
  message: string,
  conversationId?: string
): Promise<DrivebotChatResponse> {
  const body: DrivebotChatRequest = {
    message,
  }

  if (conversationId) {
    body.conversation_id = conversationId
  }

  return fetchWithErrorHandling<DrivebotChatResponse>(
    `${API_BASE_URL}/api/drivebot/chat`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }
  )
}

/**
 * Obtém informações sobre uma conversação do DriveBot
 * @param conversationId - ID da conversação
 * @returns Informações da conversação
 */
export async function getDrivebotConversation(
  conversationId: string
): Promise<DrivebotConversationInfo> {
  return fetchWithErrorHandling<DrivebotConversationInfo>(
    `${API_BASE_URL}/api/drivebot/conversation/${conversationId}`
  )
}

/**
 * Remove uma conversação do DriveBot
 * @param conversationId - ID da conversação
 * @returns Mensagem de confirmação
 */
export async function deleteDrivebotConversation(
  conversationId: string
): Promise<{ message: string; conversation_id: string }> {
  return fetchWithErrorHandling<{ message: string; conversation_id: string }>(
    `${API_BASE_URL}/api/drivebot/conversation/${conversationId}`,
    {
      method: 'DELETE',
    }
  )
}

// ============================================================================
// 🚀 SPRINT 2 - FEATURE 5: CACHE MANAGEMENT
// ============================================================================

export interface CacheStats {
  total_entries: number
  total_requests: number
  hits: number
  misses: number
  hit_rate: number
  sets: number
  expired: number
  clears: number
  cache_size_mb: number
  ttl_seconds: number
  max_entries: number
}

/**
 * Obtém estatísticas do cache
 */
export async function getCacheStats(): Promise<CacheStats> {
  return fetchWithErrorHandling<CacheStats>(`${API_BASE_URL}/api/cache/stats`, {
    method: 'GET',
  })
}

/**
 * Limpa todo o cache
 */
export async function clearCache(): Promise<{ message: string; entries_cleared: number }> {
  return fetchWithErrorHandling<{ message: string; entries_cleared: number }>(
    `${API_BASE_URL}/api/cache/clear`,
    {
      method: 'POST',
    }
  )
}

// ============================================================================
// HEALTH CHECK
// ============================================================================

/**
 * Verifica se o backend está respondendo
 * @returns Status do servidor
 */
export async function checkHealth(): Promise<HealthResponse> {
  return fetchWithErrorHandling<HealthResponse>(`${API_BASE_URL}/api/health`)
}
