import React from 'react'
import { ThemeProvider } from './contexts/ThemeContext'
import { BotProvider } from './contexts/BotContext'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'

export default function App() {
  return (
    <ThemeProvider>
      <BotProvider>
        <div className="h-screen flex bg-[var(--bg)]">
          <Sidebar />
          <ChatArea />
        </div>
      </BotProvider>
    </ThemeProvider>
  )
}
