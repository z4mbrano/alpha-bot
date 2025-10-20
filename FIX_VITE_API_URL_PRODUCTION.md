# Fix: VITE_API_URL em Produção

## 🐛 Problema Encontrado

O frontend estava fazendo requisições para o **próprio domínio do Vercel** ao invés do backend Railway:

```
❌ https://alpha-bot-six.vercel.app/api/auth/login (500 Error)
✅ https://alphainsights.up.railway.app/api/auth/login (correto)
```

## 🔍 Causa Raiz

Todos os arquivos estavam usando esta lógica incorreta:

```typescript
const API_BASE_URL = import.meta.env.PROD 
  ? '' // ❌ String vazia em produção = requisições relativas
  : (import.meta.env.VITE_API_URL || 'http://localhost:5000')
```

Isso fazia com que:
- ✅ **Dev**: Usava `VITE_API_URL` ou `localhost:5000`
- ❌ **Prod**: Usava string vazia `''` → requisições relativas ao Vercel

## ✅ Solução Aplicada

Mudamos para sempre usar `VITE_API_URL` (tanto em dev quanto em prod):

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
```

### Arquivos Corrigidos (4):

1. ✅ `src/contexts/AuthContext.tsx`
2. ✅ `src/services/api.ts`
3. ✅ `src/contexts/BotContext.tsx`
4. ✅ `src/components/ChatArea.tsx`

## 🚀 Deploy

**Commit:** `5fa9d51` - "fix: usar VITE_API_URL em produção para Railway"

O Vercel vai detectar o push automaticamente e fazer novo deploy em ~2 minutos.

## 🧪 Testando

Após o deploy completar:

1. Abra nova janela anônima ou limpe cache (`Ctrl + Shift + Delete`)
2. Acesse: https://alpha-bot-six.vercel.app
3. Abra DevTools (F12) → Network
4. Tente fazer login
5. Verifique que requisições vão para: `alphainsights.up.railway.app` ✅

## 📝 Variáveis de Ambiente

**No Vercel:**
```
VITE_API_URL=https://alphainsights.up.railway.app
```

Esta variável já está configurada no dashboard do Vercel desde o deploy anterior.

## ✨ Resultado Esperado

Agora todas as requisições vão corretamente para o Railway:
- ✅ `POST /api/auth/login` → Railway
- ✅ `POST /api/auth/register` → Railway
- ✅ `POST /api/alphabot/chat` → Railway
- ✅ `POST /api/drivebot/chat` → Railway
- ✅ Todas as outras APIs → Railway

---

**Status:** ✅ Fix aplicado - Aguardando deploy do Vercel
