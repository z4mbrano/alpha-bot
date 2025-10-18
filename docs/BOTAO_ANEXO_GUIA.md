# 📎 Guia: Botão de Anexo do AlphaBot

## **Problema Resolvido** ✅

O botão de anexo (📎) não tinha funcionalidade. Agora está totalmente implementado!

---

## **O Que Foi Implementado**

### **1. Botão de Anexo Funcional** (`ChatArea.tsx`)
- ✅ `<input type="file">` oculto com aceite apenas `.csv` e `.xlsx`
- ✅ Botão Paperclip que abre o seletor de arquivos
- ✅ Visível apenas quando `active === 'alphabot'`
- ✅ Suporte para múltiplos arquivos

### **2. Preview de Arquivos Selecionados**
- ✅ Lista de arquivos com nome e botão de remoção (X)
- ✅ Contador de arquivos selecionados
- ✅ Botão "Enviar Arquivos" para upload

### **3. Upload para Backend**
- ✅ POST para `/api/alphabot/upload`
- ✅ FormData com múltiplos arquivos
- ✅ Armazena `session_id` no localStorage
- ✅ Feedback visual de sucesso/erro

### **4. Integração com Chat** (`BotContext.tsx`)
- ✅ AlphaBot usa endpoint `/api/alphabot/chat`
- ✅ Envia `session_id` + `message`
- ✅ DriveBot continua usando endpoint original

---

## **Como Testar**

### **Passo 1: Iniciar Backend**
```powershell
cd c:\Users\vrd\Documents\GitHub\alpha-bot\backend
python app.py
```

### **Passo 2: Iniciar Frontend**
```powershell
cd c:\Users\vrd\Documents\GitHub\alpha-bot
npm run dev
```

### **Passo 3: Testar Botão de Anexo**

1. **Abrir AlphaBot:**
   - Clicar no bot "Analista de Planilhas" na sidebar

2. **Anexar Arquivos:**
   - Clicar no botão 📎 (Paperclip) no canto inferior esquerdo
   - Selecionar um ou mais arquivos `.csv` ou `.xlsx`
   - Ver preview dos arquivos selecionados

3. **Enviar Arquivos:**
   - Clicar em "Enviar Arquivos"
   - Aguardar resposta de sucesso

4. **Fazer Perguntas:**
   - Após upload, digitar perguntas como:
     - "Qual foi o produto mais vendido?"
     - "Qual foi o faturamento total?"
     - "Mostre os dados de janeiro"

---

## **Estrutura Visual**

### **Antes do Upload:**
```
┌────────────────────────────────────────────────────┐
│  [📎]  [Digite sua mensagem...]         [Enviar]  │
└────────────────────────────────────────────────────┘
```

### **Após Selecionar Arquivos:**
```
┌────────────────────────────────────────────────────┐
│  2 arquivo(s) selecionado(s)    [Enviar Arquivos] │
│  ┌──────────────────┐  ┌──────────────────┐      │
│  │ vendas.csv   [X] │  │ produtos.xlsx [X]│      │
│  └──────────────────┘  └──────────────────┘      │
├────────────────────────────────────────────────────┤
│  [📎]  [Digite sua mensagem...]         [Enviar]  │
└────────────────────────────────────────────────────┘
```

### **Durante Upload:**
```
📎 Enviando 2 arquivo(s): vendas.csv, produtos.xlsx

AlphaBot está digitando...
```

### **Após Upload Bem-Sucedido:**
```
✅ Upload concluído! 2 arquivo(s) processado(s) com sucesso.

📊 100 registros consolidados em 8 colunas.

Agora você pode fazer perguntas sobre os dados!
```

---

## **Fluxo Completo**

```
┌─────────────────────────────────────────────────────┐
│  USUÁRIO: Clica no botão 📎                        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  FRONTEND: Abre file picker                         │
│  - Filtra apenas .csv e .xlsx                      │
│  - Adiciona à lista selectedFiles                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  USUÁRIO: Clica em "Enviar Arquivos"              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  FRONTEND: POST /api/alphabot/upload               │
│  - FormData com múltiplos arquivos                 │
│  - Adiciona mensagem "📎 Enviando..."              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  BACKEND: Processa arquivos                         │
│  - Valida extensões                                │
│  - Lê com pandas                                   │
│  - Consolida em DataFrame único                    │
│  - Cria colunas auxiliares temporais               │
│  - Retorna session_id                              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  FRONTEND: Armazena session_id                      │
│  - localStorage.setItem('alphabot_session_id', id) │
│  - Adiciona mensagem "✅ Upload concluído!"        │
│  - Limpa selectedFiles                             │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  USUÁRIO: Faz perguntas                            │
│  "Qual foi o produto mais vendido?"                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  FRONTEND: POST /api/alphabot/chat                  │
│  - session_id (do localStorage)                    │
│  - message (pergunta do usuário)                   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  BACKEND: Motor de Validação                        │
│  1. ANALISTA: Análise técnica                      │
│  2. CRÍTICO: Desafios                              │
│  3. JÚRI: Resposta estruturada                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  FRONTEND: Exibe resposta do AlphaBot              │
│  - Resposta Direta                                 │
│  - Análise Detalhada                               │
│  - Insights Adicionais                             │
│  - Limitações e Contexto                           │
└─────────────────────────────────────────────────────┘
```

---

## **Tratamento de Erros**

### **Erro: Nenhum session_id**
```
❌ Por favor, anexe planilhas (.csv, .xlsx) primeiro usando o botão de anexo.
```

### **Erro: Sessão não encontrada**
```
❌ Erro: Sessão não encontrada. Por favor, faça upload dos arquivos primeiro.
```

### **Erro: Arquivo inválido**
```
❌ Erro no upload: Formato de arquivo não suportado (apenas .csv e .xlsx)
```

### **Erro: Backend offline**
```
❌ Erro ao enviar arquivos: Failed to fetch
```

---

## **Diferenças entre Bots**

| Característica | AlphaBot | DriveBot |
|---------------|----------|----------|
| **Botão de Anexo** | ✅ Visível | ❌ Oculto |
| **Upload** | Direto via formulário | Não aplicável |
| **Session Management** | session_id (localStorage) | conversation_id (Context) |
| **Endpoint** | `/api/alphabot/chat` | `/api/chat` |
| **Placeholder** | "Anexe planilhas..." | "Cole ID da pasta..." |

---

## **Arquivos Modificados**

1. ✅ `src/components/ChatArea.tsx`
   - Estado `selectedFiles`
   - Ref `fileInputRef`
   - Função `handleFileSelect()`
   - Função `handleRemoveFile()`
   - Função `handleUploadFiles()`
   - UI de preview de arquivos
   - Botão de anexo condicional

2. ✅ `src/contexts/BotContext.tsx`
   - Lógica condicional em `send()`
   - Endpoint `/api/alphabot/chat` para AlphaBot
   - Usa `session_id` do localStorage
   - Retorna `data.answer` (não `data.response`)

---

## **Validações Implementadas**

### **Frontend:**
- ✅ Aceita apenas `.csv` e `.xlsx`
- ✅ Permite múltiplos arquivos
- ✅ Valida se há arquivos antes de enviar
- ✅ Desabilita botões durante upload

### **Backend:**
- ✅ Valida extensões permitidas
- ✅ Trata erros de leitura de arquivo
- ✅ Valida session_id em chat
- ✅ Retorna erros estruturados

---

## **Próximos Passos**

1. ⬜ Adicionar barra de progresso de upload
2. ⬜ Mostrar tamanho dos arquivos
3. ⬜ Limitar tamanho máximo de arquivo
4. ⬜ Adicionar botão "Limpar sessão"
5. ⬜ Persistir arquivos no backend (não apenas em memória)

---

**Status:** ✅ Totalmente implementado e pronto para teste!  
**Data:** 2025-10-18  
**Versão:** AlphaBot v1.0 + Frontend Integration
