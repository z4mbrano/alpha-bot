/**
 * useFileUpload Hook
 * Hook para gerenciar upload de arquivos para o AlphaBot
 */

import { useState, useCallback } from 'react'
import { uploadAlphabotFiles } from '../services/api'
import type { FileUploadState, AlphabotUploadResponse } from '../types'

export function useFileUpload() {
  const [state, setState] = useState<FileUploadState>({
    status: 'idle',
    progress: { loaded: 0, total: 0, percentage: 0 },
  })

  /**
   * Reseta o estado do upload
   */
  const reset = useCallback(() => {
    setState({
      status: 'idle',
      progress: { loaded: 0, total: 0, percentage: 0 },
    })
  }, [])

  /**
   * Faz upload de arquivos
   * @param files - Array de arquivos
   * @returns Resposta do servidor ou null em caso de erro
   */
  const upload = useCallback(
    async (files: File[]): Promise<AlphabotUploadResponse | null> => {
      if (files.length === 0) {
        setState((prev) => ({
          ...prev,
          status: 'error',
          error: 'Nenhum arquivo selecionado',
        }))
        return null
      }

      // Validar tipos de arquivo
      const allowedExtensions = ['.csv', '.xlsx', '.xls']
      const invalidFiles = files.filter((file) => {
        const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))
        return !allowedExtensions.includes(ext)
      })

      if (invalidFiles.length > 0) {
        setState((prev) => ({
          ...prev,
          status: 'error',
          error: `Arquivos inválidos: ${invalidFiles.map((f) => f.name).join(', ')}. Apenas CSV e XLSX são permitidos.`,
        }))
        return null
      }

      // Iniciar upload
      setState({
        status: 'uploading',
        progress: { loaded: 0, total: 0, percentage: 0 },
      })

      try {
        const response = await uploadAlphabotFiles(files, (progress) => {
          setState((prev) => ({
            ...prev,
            progress,
          }))
        })

        setState({
          status: 'success',
          progress: { loaded: 0, total: 0, percentage: 100 },
          response,
        })

        return response
      } catch (error) {
        const errorMsg =
          error instanceof Error ? error.message : 'Erro desconhecido ao fazer upload'

        setState({
          status: 'error',
          progress: { loaded: 0, total: 0, percentage: 0 },
          error: errorMsg,
        })

        return null
      }
    },
    []
  )

  return {
    ...state,
    upload,
    reset,
    isUploading: state.status === 'uploading',
    isSuccess: state.status === 'success',
    isError: state.status === 'error',
    isIdle: state.status === 'idle',
  }
}
