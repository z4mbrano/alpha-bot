# API Documentation

Documentação completa dos endpoints do Alpha Bot Backend.

## Base URL

```
http://localhost:5000
```

Para produção, ajuste a URL conforme necessário (ex: `https://api.alphabot.com`).

---

## Índice

- [Health Check](#health-check)
- [AlphaBot API](#alphabot-api)
  - [Upload de Arquivos](#upload-de-arquivos)
  - [Chat](#alphabot-chat)
  - [Gerenciar Sessão](#gerenciar-sessão)
- [DriveBot API](#drivebot-api)
  - [Chat](#drivebot-chat)
  - [Gerenciar Conversação](#gerenciar-conversação)

---

## Health Check

Verifica se o servidor está respondendo.

### `GET /api/health`

**Resposta de Sucesso (200 OK):**
```json
{
  "status": "ok"
}
```

**Exemplo cURL:**
```bash
curl http://localhost:5000/api/health
```

---

## AlphaBot API

O AlphaBot é especializado em análise de planilhas (CSV, XLSX) com validação por múltiplas personas.

### Upload de Arquivos

Faz upload de arquivos e cria uma sessão de análise.

#### `POST /api/alphabot/upload`

**Content-Type:** `multipart/form-data`

**Parâmetros:**
- `files` (FormData, obrigatório): Um ou mais arquivos CSV/XLSX

**Resposta de Sucesso (200 OK):**
```json
{
  "session_id": "abc123def456",
  "files_count": 2,
  "total_rows": 1523,
  "memory_mb": 2.45,
  "columns": [
    "data",
    "produto",
    "quantidade",
    "valor",
    "mês",
    "ano",
    "dia_da_semana"
  ],
  "message": "2 arquivo(s) processado(s) com sucesso. Total: 1523 linhas."
}
```

**Resposta de Erro (400 Bad Request):**
```json
{
  "error": "Nenhum arquivo enviado"
}
```

**Exemplo cURL:**
```bash
curl -X POST http://localhost:5000/api/alphabot/upload \
  -F "files=@vendas_janeiro.csv" \
  -F "files=@vendas_fevereiro.xlsx"
```

**Exemplo JavaScript:**
```javascript
const formData = new FormData()
formData.append('files', file1)
formData.append('files', file2)

const response = await fetch('http://localhost:5000/api/alphabot/upload', {
  method: 'POST',
  body: formData
})

const data = await response.json()
console.log('Session ID:', data.session_id)
```

---

### AlphaBot Chat

Envia uma pergunta sobre os dados carregados.

#### `POST /api/alphabot/chat`

**Content-Type:** `application/json`

**Body:**
```json
{
  "session_id": "abc123def456",
  "message": "Qual foi o total de vendas em janeiro?"
}
```

**Resposta de Sucesso (200 OK):**
```json
{
  "answer": "## Resposta validada\n\nO total de vendas em janeiro foi de R$ 45.230,00...",
  "session_id": "abc123def456"
}
```

**Resposta de Erro (400 Bad Request):**
```json
{
  "error": "session_id é obrigatório"
}
```

**Resposta de Erro (404 Not Found):**
```json
{
  "error": "Sessão não encontrada",
  "session_id": "abc123def456"
}
```

**Exemplo cURL:**
```bash
curl -X POST http://localhost:5000/api/alphabot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc123def456",
    "message": "Qual foi o produto mais vendido?"
  }'
```

**Exemplo JavaScript:**
```javascript
const response = await fetch('http://localhost:5000/api/alphabot/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    session_id: 'abc123def456',
    message: 'Qual foi o produto mais vendido?'
  })
})

const data = await response.json()
console.log('Resposta:', data.answer)
```

---

### Gerenciar Sessão

#### Obter Informações da Sessão

##### `GET /api/alphabot/session/<session_id>`

**Resposta de Sucesso (200 OK):**
```json
{
  "session_id": "abc123def456",
  "files_count": 2,
  "total_rows": 1523,
  "memory_mb": 2.45,
  "columns": ["data", "produto", "quantidade", "valor"],
  "created_at": 1729209600
}
```

**Resposta de Erro (404 Not Found):**
```json
{
  "error": "Sessão não encontrada",
  "session_id": "abc123def456"
}
```

**Exemplo cURL:**
```bash
curl http://localhost:5000/api/alphabot/session/abc123def456
```

---

#### Deletar Sessão

##### `DELETE /api/alphabot/session/<session_id>`

**Resposta de Sucesso (200 OK):**
```json
{
  "message": "Sessão removida com sucesso",
  "session_id": "abc123def456"
}
```

**Resposta de Erro (404 Not Found):**
```json
{
  "error": "Sessão não encontrada",
  "session_id": "abc123def456"
}
```

**Exemplo cURL:**
```bash
curl -X DELETE http://localhost:5000/api/alphabot/session/abc123def456
```

---

## DriveBot API

O DriveBot é especializado em análise de dados do Google Drive com motor de descoberta autônomo.

### DriveBot Chat

Envia uma mensagem para o DriveBot (pode ser ID de pasta do Drive ou pergunta sobre dados).

#### `POST /api/drivebot/chat`

**Content-Type:** `application/json`

**Body:**
```json
{
  "message": "1a2b3c4d5e6f7g8h9i0j",
  "conversation_id": "conv-uuid-123" // opcional
}
```

**Resposta de Sucesso (200 OK):**
```json
{
  "response": "## Preparando o ambiente de análise\n\nRecebi o ID: 1a2b3c4d5e6f7g8h9i0j...",
  "conversation_id": "conv-uuid-123"
}
```

**Resposta de Erro (500 Internal Server Error):**
```json
{
  "error": "Erro ao processar pergunta: Pasta não encontrada",
  "conversation_id": "conv-uuid-123"
}
```

**Exemplo cURL (Primeira mensagem - ID da pasta):**
```bash
curl -X POST http://localhost:5000/api/drivebot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "1a2b3c4d5e6f7g8h9i0j"
  }'
```

**Exemplo cURL (Mensagem subsequente):**
```bash
curl -X POST http://localhost:5000/api/drivebot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Qual foi o total de vendas?",
    "conversation_id": "conv-uuid-123"
  }'
```

**Exemplo JavaScript:**
```javascript
// Primeira mensagem - enviar ID da pasta
const response1 = await fetch('http://localhost:5000/api/drivebot/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: '1a2b3c4d5e6f7g8h9i0j' // ID da pasta do Google Drive
  })
})

const data1 = await response1.json()
console.log('Conversation ID:', data1.conversation_id)
console.log('Resposta:', data1.response)

// Mensagens subsequentes - usar conversation_id
const response2 = await fetch('http://localhost:5000/api/drivebot/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: 'Qual foi o total de vendas?',
    conversation_id: data1.conversation_id
  })
})

const data2 = await response2.json()
console.log('Resposta:', data2.response)
```

---

### Gerenciar Conversação

#### Obter Informações da Conversação

##### `GET /api/drivebot/conversation/<conversation_id>`

**Resposta de Sucesso (200 OK):**
```json
{
  "conversation_id": "conv-uuid-123",
  "history_length": 8,
  "has_drive_data": true,
  "folder_id": "1a2b3c4d5e6f7g8h9i0j"
}
```

**Resposta de Erro (404 Not Found):**
```json
{
  "error": "Conversação não encontrada",
  "conversation_id": "conv-uuid-123"
}
```

**Exemplo cURL:**
```bash
curl http://localhost:5000/api/drivebot/conversation/conv-uuid-123
```

---

#### Deletar Conversação

##### `DELETE /api/drivebot/conversation/<conversation_id>`

**Resposta de Sucesso (200 OK):**
```json
{
  "message": "Conversação removida com sucesso",
  "conversation_id": "conv-uuid-123"
}
```

**Resposta de Erro (404 Not Found):**
```json
{
  "error": "Conversação não encontrada",
  "conversation_id": "conv-uuid-123"
}
```

**Exemplo cURL:**
```bash
curl -X DELETE http://localhost:5000/api/drivebot/conversation/conv-uuid-123
```

---

## Códigos de Status HTTP

| Código | Significado |
|--------|-------------|
| 200 | Sucesso |
| 400 | Bad Request - Parâmetros inválidos |
| 404 | Not Found - Recurso não encontrado |
| 500 | Internal Server Error - Erro do servidor |

---

## Limites e Restrições

- **Tamanho máximo de upload:** 50 MB por requisição
- **Tipos de arquivo aceitos (AlphaBot):** `.csv`, `.xlsx`, `.xls`
- **Tipos de arquivo aceitos (DriveBot):** CSV e Excel no Google Drive
- **Rate limiting:** Não implementado (considere adicionar em produção)

---

## Tratamento de Erros

Todas as respostas de erro seguem o formato:

```json
{
  "error": "Mensagem de erro descritiva"
}
```

Campos adicionais podem ser incluídos dependendo do contexto (como `session_id` ou `conversation_id`).

---

## Notas de Implementação

### CORS

O servidor está configurado para aceitar requisições de:
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:5173`

Para produção, ajuste as origens permitidas em `backend/app.py`.

### Autenticação

Atualmente, a API não requer autenticação. Para produção, considere implementar:
- API Keys
- JWT Tokens
- OAuth 2.0

### Google Drive Service Account

O DriveBot requer uma Service Account do Google Cloud com acesso às pastas do Drive. Configure a variável de ambiente `GOOGLE_SERVICE_ACCOUNT_FILE` ou `GOOGLE_SERVICE_ACCOUNT_INFO`.

---

## Changelog

### v2.0.0 (Clean Architecture)
- Refatoração completa seguindo Clean Architecture
- Blueprints modulares para AlphaBot e DriveBot
- Separação clara de responsabilidades (API → Services → Utils)
- Documentação completa da API

### v1.0.0 (Monolith)
- Implementação inicial com endpoint `/api/chat` único
- Roteamento interno por `bot_id`

---

## Suporte

Para problemas ou dúvidas:
1. Verifique se o backend está rodando: `GET /api/health`
2. Consulte os logs do servidor
3. Revise esta documentação
4. Consulte `docs/ARCHITECTURE.md` para entender a estrutura interna

---

**Última atualização:** Outubro 2025
