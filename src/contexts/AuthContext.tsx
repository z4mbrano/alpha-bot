import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { toast } from 'sonner'

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? 'https://alpha-bot-oglo.onrender.com' : 'http://localhost:5000')

interface User {
  id: number
  username: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<boolean>
  register: (username: string, password: string) => Promise<boolean>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Carregar usuário do localStorage na inicialização
  useEffect(() => {
    // Debug: exibir URL base atual para facilitar diagnóstico
    try {
      console.log('[AuthContext] API_BASE_URL em uso:', API_BASE_URL)
      if (API_BASE_URL.includes('railway')) {
        console.warn('[AuthContext] ⚠️ URL aponta para Railway. Atualize VITE_API_URL para Render em Vercel.')
      }
    } catch {}

    const storedUser = localStorage.getItem('alpha_user')
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser)
        setUser(userData)
      } catch (error) {
        console.error('Erro ao carregar usuário:', error)
        localStorage.removeItem('alpha_user')
      }
    }
    setLoading(false)
  }, [])

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      const data = await response.json()

      if (response.ok && data.success) {
        const userData = data.user
        setUser(userData)
        localStorage.setItem('alpha_user', JSON.stringify(userData))
        toast.success(`Bem-vindo, ${userData.username}! 👋`)
        return true
      } else {
        toast.error(data.error || 'Credenciais inválidas')
        return false
      }
    } catch (error) {
      console.error('Erro no login:', error)
      toast.error('Erro ao conectar com o servidor')
      return false
    }
  }

  const register = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      const data = await response.json()

      if (response.ok && data.success) {
        // Não realizar login automático após registro para evitar fluxo incorreto
        toast.success('Conta criada com sucesso! Faça login para continuar. ✅')
        return true
      } else {
        toast.error(data.error || 'Erro ao criar conta')
        return false
      }
    } catch (error) {
      console.error('Erro no registro:', error)
      toast.error('Erro ao conectar com o servidor')
      return false
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('alpha_user')
    // Limpar conversas em memória também
    localStorage.removeItem('alpha_active_conversation')
    toast.success('Logout realizado com sucesso! 👋')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider')
  }
  return context
}
