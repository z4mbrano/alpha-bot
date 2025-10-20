# 🔧 Fix: Conversas Misturando Entre Bots

## 🐛 Problema

**Comportamento Incorreto:**
1. Usuário cria conversa no **AlphaBot** com planilha de vendas
2. Usuário troca para **DriveBot** 
3. As mensagens do AlphaBot aparecem no DriveBot ❌
4. Ao voltar para AlphaBot, aparece conversa do DriveBot ❌

**Causa Raiz:**
O código estava carregando mensagens de **qualquer conversa ativa**, sem verificar se era do bot correto.

```typescript
// ❌ ANTES: Carregava mensagens sem verificar bot_type
const messages = await api.getConversationMessages(activeConversationId, user.id)
const convertedMessages: Message[] = messages.map(msg => ({
  botId: active, // ❌ Forçava o bot atual, ignorando o bot_type da conversa
  ...
}))
```

## ✅ Solução Implementada

### 1. **Verificar `bot_type` da conversa antes de carregar**

```typescript
// ✅ DEPOIS: Verifica se a conversa é do bot correto
const activeConv = getActiveConversation()

if (!activeConv || activeConv.bot_type !== active) {
  console.log(`🔒 Conversa é do bot "${activeConv.bot_type}", mas você está em "${active}". Limpando.`)
  setStore((s) => ({ ...s, [active]: [] })) // Limpa tela
  return
}

// Só carrega se for do bot correto
const messages = await api.getConversationMessages(activeConversationId, user.id)
const convertedMessages: Message[] = messages.map(msg => ({
  botId: activeConv.bot_type as BotId, // ✅ Usa o bot_type real da conversa
  ...
}))
```

### 2. **Melhorar função `setActive` para logging**

```typescript
const setActive = (newBotId: BotId) => {
  if (newBotId !== active) {
    console.log(`🔄 Trocando de ${active} → ${newBotId}`)
    
    // Limpar mensagens do NOVO bot antes de trocar
    setStore((s) => ({ ...s, [newBotId]: [] }))
    
    // Se houver conversa ativa mas for do bot errado, avisar
    const activeConv = getActiveConversation()
    if (activeConv && activeConv.bot_type !== newBotId) {
      console.log(`⚠️ Conversa ativa é do bot "${activeConv.bot_type}", mas você está trocando para "${newBotId}"`)
    }
  }
  setActiveBot(newBotId)
}
```

## 📋 O que foi corrigido

**Arquivo:** `src/contexts/BotContext.tsx`

**Mudanças:**
1. ✅ Adicionar verificação `if (activeConv.bot_type !== active)` antes de carregar mensagens
2. ✅ Retornar early e limpar tela se bot estiver errado
3. ✅ Usar `activeConv.bot_type` ao invés de forçar `active` nas mensagens
4. ✅ Adicionar logs detalhados para debugging
5. ✅ Melhorar `setActive` com avisos sobre incompatibilidade

## 🎯 Comportamento Esperado Após Fix

### Cenário 1: Trocar de Bot com Conversa Ativa

**Passo a passo:**
1. Usuário está no **AlphaBot** com conversa ativa
2. Usuário clica em **DriveBot** no sidebar
3. **Resultado:** Tela limpa ✅ (porque a conversa ativa é do AlphaBot, não DriveBot)

### Cenário 2: Trocar Entre Conversas

**Passo a passo:**
1. Usuário cria 2 conversas no AlphaBot
2. Alterna entre elas
3. **Resultado:** Mensagens carregam corretamente ✅

**Passo a passo:**
1. Usuário tem conversa no AlphaBot
2. Usuário tem conversa no DriveBot
3. Alterna entre AlphaBot e DriveBot
4. **Resultado:** Cada bot mostra apenas suas próprias conversas ✅

### Cenário 3: Criar Nova Conversa em Bot Diferente

**Passo a passo:**
1. Usuário está no AlphaBot com conversa ativa
2. Troca para DriveBot
3. Envia mensagem (cria nova conversa automaticamente)
4. **Resultado:** Nova conversa criada no DriveBot, sem interferência do AlphaBot ✅

## 🧪 Como Testar

### Teste 1: Isolamento Entre Bots

1. Acesse: https://alpha-bot-six.vercel.app
2. Faça login
3. Troque para **AlphaBot**
4. Crie uma conversa e envie: "Olá AlphaBot"
5. Troque para **DriveBot**
6. **Esperado:** Tela vazia ✅
7. Envie: "Olá DriveBot"
8. Volte para **AlphaBot**
9. **Esperado:** Mensagens do AlphaBot aparecem ✅

### Teste 2: Múltiplas Conversas no Mesmo Bot

1. No **AlphaBot**, crie 2 conversas diferentes
2. Envie mensagens diferentes em cada uma
3. Alterne entre as conversas no sidebar
4. **Esperado:** Cada conversa mostra suas próprias mensagens ✅

### Teste 3: Logs do Console

Abra DevTools (F12) → Console e veja os logs:

```
✅ Esperado ao trocar de bot:
🔄 Trocando de alphabot → drivebot
⚠️ Conversa ativa é do bot "alphabot", mas você está trocando para "drivebot". Limpando tela.

✅ Esperado ao carregar conversa correta:
✅ 5 mensagens carregadas da conversa abc123 (alphabot)

❌ Esperado ao tentar carregar conversa errada:
🔒 Conversa é do bot "drivebot", mas você está em "alphabot". Limpando.
```

## 📊 Diferenças Técnicas

| Aspecto | Antes ❌ | Depois ✅ |
|---------|---------|-----------|
| Verificação de bot | Nenhuma | Verifica `bot_type` da conversa |
| Carregamento de mensagens | Carrega qualquer conversa | Só carrega se `bot_type === active` |
| `botId` nas mensagens | Forçava `active` | Usa `activeConv.bot_type` |
| Comportamento ao trocar bot | Mantinha mensagens | Limpa se conversa for de outro bot |
| Logs | Básicos | Detalhados com emojis |

## 🚀 Deploy

**Commit:** `d6252c6` - "fix: verificar bot_type da conversa antes de carregar mensagens"

**Status:** 
- ✅ Push para GitHub concluído
- ⏳ Vercel detectando mudanças (~30 segundos)
- ⏳ Build e deploy (~2 minutos)
- ⏳ CDN propagation (~1 minuto)

**Total:** ~3-4 minutos até estar live

## 🎯 Checklist de Validação

Após o deploy completar:

- [ ] Limpar cache do navegador (`Ctrl + Shift + Delete`)
- [ ] Ou abrir janela anônima
- [ ] Fazer login
- [ ] Criar conversa no AlphaBot
- [ ] Trocar para DriveBot → Tela deve estar vazia ✅
- [ ] Criar conversa no DriveBot
- [ ] Trocar para AlphaBot → Tela deve estar vazia ✅
- [ ] Alternar entre conversas do mesmo bot → Mensagens corretas aparecem ✅
- [ ] Verificar logs no Console (F12) → Logs detalhados aparecem ✅

---

**Última atualização:** Commit `d6252c6`  
**Status:** ⏳ Deploy do Vercel em andamento  
**ETA:** ~3 minutos
