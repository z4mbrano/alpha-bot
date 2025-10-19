import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { BarChart2, Gem, Loader2, User, Lock, LogIn, UserPlus } from 'lucide-react'

export default function AuthScreen() {
  const { login, register } = useAuth()
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({})

  const validateForm = (): boolean => {
    const newErrors: { username?: string; password?: string } = {}

    if (!username.trim()) {
      newErrors.username = 'Username é obrigatório'
    } else if (username.length < 3) {
      newErrors.username = 'Username deve ter pelo menos 3 caracteres'
    }

    if (!password) {
      newErrors.password = 'Senha é obrigatória'
    } else if (password.length < 6) {
      newErrors.password = 'Senha deve ter pelo menos 6 caracteres'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    setLoading(true)

    try {
      const success = isLogin 
        ? await login(username, password)
        : await register(username, password)

      if (!success) {
        // Erro já mostrado via toast
      }
    } finally {
      setLoading(false)
    }
  }

  const toggleMode = () => {
    setIsLogin(!isLogin)
    setErrors({})
    setUsername('')
    setPassword('')
  }

  return (
    <div className="h-screen flex items-center justify-center bg-gradient-to-br from-[var(--bg)] via-[var(--bg-2)] to-[var(--bg)]">
      <div className="w-full max-w-md mx-4">
        {/* Header com logos */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="p-3 rounded-xl bg-[var(--accent)]/10 border border-[var(--accent)]/20">
              <BarChart2 size={32} className="text-[var(--accent)]" />
            </div>
            <div className="text-3xl font-bold text-[var(--text)]">×</div>
            <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20">
              <Gem size={32} className="text-purple-500" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-[var(--text)] mb-2">
            Alpha Insights Chat
          </h1>
          <p className="text-[var(--muted)]">
            {isLogin ? 'Entre para continuar' : 'Crie sua conta gratuitamente'}
          </p>
        </div>

        {/* Card de login/registro */}
        <div className="bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Campo Username */}
            <div>
              <label className="block text-sm font-medium text-[var(--text)] mb-2">
                Username
              </label>
              <div className="relative">
                <User size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value)
                    setErrors({ ...errors, username: undefined })
                  }}
                  disabled={loading}
                  className={`w-full pl-10 pr-4 py-3 bg-[var(--bg)] border rounded-lg text-[var(--text)] placeholder:text-[var(--muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-fast ${
                    errors.username ? 'border-red-500' : 'border-[var(--border)]'
                  }`}
                  placeholder="seunome"
                  autoComplete="username"
                />
              </div>
              {errors.username && (
                <p className="mt-1 text-sm text-red-500">{errors.username}</p>
              )}
            </div>

            {/* Campo Senha */}
            <div>
              <label className="block text-sm font-medium text-[var(--text)] mb-2">
                Senha
              </label>
              <div className="relative">
                <Lock size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    setErrors({ ...errors, password: undefined })
                  }}
                  disabled={loading}
                  className={`w-full pl-10 pr-4 py-3 bg-[var(--bg)] border rounded-lg text-[var(--text)] placeholder:text-[var(--muted)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] transition-fast ${
                    errors.password ? 'border-red-500' : 'border-[var(--border)]'
                  }`}
                  placeholder="••••••••"
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                />
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-500">{errors.password}</p>
              )}
            </div>

            {/* Botão Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white font-medium rounded-lg transition-fast disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2 focus:ring-offset-[var(--surface)]"
            >
              {loading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  <span>{isLogin ? 'Entrando...' : 'Criando conta...'}</span>
                </>
              ) : (
                <>
                  {isLogin ? <LogIn size={18} /> : <UserPlus size={18} />}
                  <span>{isLogin ? 'Entrar' : 'Criar Conta'}</span>
                </>
              )}
            </button>
          </form>

          {/* Toggle entre Login/Registro */}
          <div className="mt-6 text-center">
            <p className="text-sm text-[var(--muted)]">
              {isLogin ? 'Não tem uma conta?' : 'Já tem uma conta?'}
              {' '}
              <button
                onClick={toggleMode}
                disabled={loading}
                className="text-[var(--accent)] hover:underline font-medium disabled:opacity-50"
              >
                {isLogin ? 'Criar conta' : 'Fazer login'}
              </button>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-xs text-[var(--muted)]">
            Ao continuar, você concorda com nossos Termos de Uso
          </p>
        </div>
      </div>
    </div>
  )
}
