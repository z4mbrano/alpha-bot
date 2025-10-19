import React from 'react'
import { createRoot } from 'react-dom/client'
import { Analytics } from '@vercel/analytics/react'
import { Toaster } from 'sonner'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
    <Analytics />
    <Toaster position="top-right" richColors closeButton />
  </React.StrictMode>
)
