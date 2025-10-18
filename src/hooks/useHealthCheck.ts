/**
 * useHealthCheck Hook
 * Hook para verificar o status do backend
 */

import { useState, useEffect, useCallback } from 'react'
import { checkHealth } from '../services/api'

interface UseHealthCheckOptions {
  interval?: number // Intervalo em ms para verificar (0 = desabilitado)
  onStatusChange?: (isHealthy: boolean) => void
}

export function useHealthCheck(options: UseHealthCheckOptions = {}) {
  const { interval = 30000, onStatusChange } = options // Default: 30 segundos
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null)
  const [isChecking, setIsChecking] = useState(false)
  const [lastCheck, setLastCheck] = useState<Date | null>(null)

  /**
   * Executa uma verificação de saúde
   */
  const check = useCallback(async () => {
    setIsChecking(true)

    try {
      await checkHealth()
      setIsHealthy(true)
      setLastCheck(new Date())

      if (onStatusChange && isHealthy === false) {
        onStatusChange(true)
      }
    } catch {
      setIsHealthy(false)
      setLastCheck(new Date())

      if (onStatusChange && isHealthy === true) {
        onStatusChange(false)
      }
    } finally {
      setIsChecking(false)
    }
  }, [isHealthy, onStatusChange])

  // Verificação automática
  useEffect(() => {
    if (interval <= 0) return

    // Verificar imediatamente
    check()

    // Configurar intervalo
    const intervalId = setInterval(check, interval)

    return () => clearInterval(intervalId)
  }, [interval, check])

  return {
    isHealthy,
    isChecking,
    lastCheck,
    check,
  }
}
