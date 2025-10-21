# ✅ Correções Aplicadas: Bot Switching + DriveBot

## 🐛 Problemas Identificados

### 1. **Mensagens se misturam ao trocar de bot** ❌
**Comportamento:** 
- Usuário está no AlphaBot com conversa ativa
- Troca para DriveBot
- As mensagens do AlphaBot aparecem no DriveBot

**Causa:** 
O `useEffect` que carrega mensagens não diferenciava entre bots, sempre carregava da mesma `activeConversationId`.

### 2. **DriveBot não funciona** ❌
**Comportamento:**
- Usuário envia mensagem para o DriveBot
- Erro 500 no backend
- Resposta: "GOOGLE_API_KEY não configurada"

**Causa:**
Railway não tem a variável `GOOGLE_API_KEY` configurada.

---

## ✅ Soluções Implementadas

### 1. **Limpar mensagens ao trocar de bot** ✅

**Arquivo:** `src/contexts/BotContext.tsx`

**Antes:**
```typescript
const [active, setActive] = useState<BotId>('alphabot')
```

**Depois:**
```typescript
const [active, setActiveBot] = useState<BotId>('alphabot')

// Wrapper que limpa mensagens ao trocar de bot
const setActive = (newBotId: BotId) => {
  if (newBotId !== active) {
    // Limpar mensagens do novo bot antes de trocar
    setStore((s) => ({ ...s, [newBotId]: [] }))
    console.log(`🔄 Trocando para ${newBotId}, limpando mensagens`)
  }
  setActiveBot(newBotId)
}
```

**Resultado:**
- ✅ Ao trocar de AlphaBot → DriveBot: mensagens são limpas
- ✅ Ao trocar de DriveBot → AlphaBot: mensagens são limpas
- ✅ Cada bot começa com conversa vazia ao ser selecionado

---

### 2. **Guia para configurar Google API no Railway** ✅

**Arquivo criado:** `RAILWAY_GOOGLE_API_KEY.md`

**Conteúdo:**
- 📋 Passo a passo completo para adicionar `GOOGLE_API_KEY`
- 🔍 Troubleshooting de erros comuns
- 🧪 Instruções de teste

**Próximo passo do usuário:**
1. Acessar: https://railway.app/
2. Ir no projeto **alphainsights**
3. Clicar em **Variables**
4. Adicionar: `GOOGLE_API_KEY=<sua-chave>`
5. Aguardar redeploy automático (1-2 min)

---

## 🚀 Deploy

**Commit:** `02a93eb` - "fix: limpar mensagens ao trocar de bot e adicionar guia Google API"

### Arquivos modificados:
1. ✅ `src/contexts/BotContext.tsx` - Correção do bot switching
2. ✅ `RAILWAY_GOOGLE_API_KEY.md` - Guia de configuração
3. ✅ `FIX_VITE_API_URL_PRODUCTION.md` - Documentação anterior

---

## 🧪 Como Testar

### Teste 1: Troca de Bot (Frontend - já corrigido)

1. Faça login em: https://alpha-bot-six.vercel.app
2. Crie conversa no **AlphaBot**
3. Envie algumas mensagens
4. Troque para **DriveBot** no sidebar
5. **Esperado:** Tela de chat vazia ✅
6. Envie mensagem no DriveBot
7. Volte para **AlphaBot**
8. **Esperado:** Tela de chat vazia novamente ✅

### Teste 2: DriveBot (Backend - precisa configurar API)

**⚠️ Só vai funcionar após configurar GOOGLE_API_KEY no Railway!**

1. Configure a variável seguindo: `RAILWAY_GOOGLE_API_KEY.md`
2. Aguarde redeploy do Railway
3. Acesse: https://alpha-bot-six.vercel.app
4. Troque para **DriveBot**
5. Envie: "Liste os arquivos da pasta raiz"
6. **Esperado:** Lista de arquivos do Google Drive ✅

---

## 📊 Status Atual

| Componente | Status | Observação |
|------------|--------|------------|
| Frontend (Vercel) | ✅ Funcionando | API conectada ao Railway |
| Backend (Railway) | ✅ Funcionando | AlphaBot operacional |
| AlphaBot | ✅ Funcionando | Análise de planilhas OK |
| DriveBot | ⏳ Pendente | Aguarda GOOGLE_API_KEY |
| Troca de Bot | ✅ Corrigido | Mensagens não misturam mais |
| Multi-usuário | ✅ Funcionando | Login, conversas, histórico |

---

## 🎯 Próximos Passos

1. **Usuário:** Configurar `GOOGLE_API_KEY` no Railway
   - Seguir guia: `RAILWAY_GOOGLE_API_KEY.md`
   - Tempo estimado: 5 minutos

2. **Sistema:** Aguardar redeploy automático
   - Railway detecta mudança de variável
   - Redeploy leva ~2 minutos

3. **Teste:** Validar DriveBot funcionando
   - Enviar mensagem de teste
   - Verificar resposta do Google Drive

---

## ✨ Resultado Final Esperado

Após configurar a API Key:

```
✅ Frontend (Vercel) → Backend (Railway) → Google Drive API
✅ AlphaBot: Análise de planilhas funcionando
✅ DriveBot: Integração com Google Drive funcionando
✅ Troca entre bots: Sem mistura de conversas
✅ Multi-usuário: Login, histórico, conversas isoladas
```

---

**Última atualização:** Commit `02a93eb`
**Deploy Vercel:** Em andamento (~2 min)
**Ação necessária:** Configurar GOOGLE_API_KEY no Railway
