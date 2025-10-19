import React from 'react'
import { ThemeProvider } from './contexts/ThemeContext'
import { BotProvider } from './contexts/BotContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ConversationProvider } from './contexts/ConversationContext'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import AuthScreen from './components/AuthScreen'

function AppContent() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[var(--bg)]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[var(--accent)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-[var(--muted)]">Carregando...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return <AuthScreen />
  }

  return (
    <div className="h-screen flex bg-[var(--bg)]">
      <Sidebar />
      <ChatArea />
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ConversationProvider>
          <BotProvider>
            <AppContent />
          </BotProvider>
        </ConversationProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}
