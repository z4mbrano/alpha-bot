/**
 * TypeScript Types and Interfaces
 * Definições de tipos para a aplicação Alpha Bot
 */

// Bot Types
export type BotId = 'alphabot' | 'drivebot'

// Message Types
export interface Message {
  id: string
  author: 'bot' | 'user'
  botId?: BotId
  text: string
  time: number
  isTyping?: boolean
  suggestions?: string[]  // 🚀 SPRINT 2: Sugestões de perguntas
}

// API Response Types

// AlphaBot Responses
export interface AlphabotUploadResponse {
  session_id: string
  files_count: number
  total_rows: number
  memory_mb: number
  columns: string[]
  message: string
}

export interface AlphabotChatResponse {
  answer: string
  session_id: string
  suggestions?: string[]  // 🚀 SPRINT 2: Sugestões de perguntas follow-up
}

export interface AlphabotSessionInfo {
  session_id: string
  files_count: number
  total_rows: number
  memory_mb: number
  columns: string[]
  created_at: number
}

// DriveBot Responses
export interface DrivebotChatResponse {
  response: string
  conversation_id: string
}

export interface DrivebotConversationInfo {
  conversation_id: string
  history_length: number
  has_drive_data: boolean
  folder_id?: string
}

// Health Check
export interface HealthResponse {
  status: 'ok'
}

// Error Response
export interface ErrorResponse {
  error: string
  conversation_id?: string
  session_id?: string
}

// API Request Types

export interface AlphabotChatRequest {
  session_id: string
  message: string
}

export interface DrivebotChatRequest {
  message: string
  conversation_id?: string
}

// File Upload Types
export interface FileUploadProgress {
  loaded: number
  total: number
  percentage: number
}

export type FileUploadStatus = 'idle' | 'uploading' | 'success' | 'error'

export interface FileUploadState {
  status: FileUploadStatus
  progress: FileUploadProgress
  error?: string
  response?: AlphabotUploadResponse
}
