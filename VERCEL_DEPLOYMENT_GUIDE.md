# 🚀 Guia de Deploy no Vercel - Alpha Bot Multi-User

## ✅ Pré-requisitos Completados

- ✅ Sistema multi-usuário com autenticação
- ✅ Gerenciamento de conversas (CRUD completo)
- ✅ Persistência de mensagens no SQLite
- ✅ Isolamento de sessões por conversa (bug corrigido)
- ✅ `vercel.json` configurado com rotas de auth e conversations
- ✅ `package.json` com script `vercel-build`

## 📋 Checklist de Deploy

### 1. Configurar Variáveis de Ambiente no Vercel

Acesse o painel do Vercel → Settings → Environment Variables e adicione:

```env
# ⚠️ OBRIGATÓRIAS
GOOGLE_API_KEY=sua_chave_gemini_aqui
FLASK_SECRET_KEY=chave_secreta_aleatoria_64_caracteres

# 📁 Google Drive (se usar DriveBot)
GOOGLE_DRIVE_CREDENTIALS={"type":"service_account","project_id":"..."}

# 🗄️ Database (Recomendado: PostgreSQL externo)
DATABASE_URL=postgresql://user:pass@host:5432/dbname
# OU para manter SQLite (não recomendado para produção):
# DATABASE_URL=sqlite:///tmp/alphabot.db
```

#### 🔐 Como Obter as Chaves:

**GOOGLE_API_KEY:**
1. Acesse [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Crie uma nova API key
3. Copie e cole no Vercel

**FLASK_SECRET_KEY:**
```python
# Execute no Python:
import secrets
print(secrets.token_hex(32))
```

**GOOGLE_DRIVE_CREDENTIALS (opcional):**
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie uma service account
3. Baixe o JSON e copie TODO o conteúdo (minificado)
4. Cole no Vercel como string única

### 2. Escolher Solução de Database

#### ❌ SQLite (NÃO recomendado)
- Vercel tem filesystem efêmero (dados perdem a cada deploy)
- Apenas para testes rápidos

#### ✅ **PostgreSQL Externo (RECOMENDADO)**

**Opção A: Supabase (GRÁTIS)**
1. Criar conta em [supabase.com](https://supabase.com)
2. Criar novo projeto
3. Copiar connection string de Settings → Database
4. Adicionar `DATABASE_URL` no Vercel

**Opção B: Railway (GRÁTIS com limites)**
1. Criar conta em [railway.app](https://railway.app)
2. Deploy PostgreSQL
3. Copiar connection string
4. Adicionar `DATABASE_URL` no Vercel

**Opção C: Vercel Postgres (PAGO após trial)**
1. No painel Vercel → Storage → Create Database
2. Escolher Postgres
3. Conectar ao projeto
4. `DATABASE_URL` é adicionada automaticamente

### 3. Atualizar Código para PostgreSQL (se escolher)

#### 📝 Modificar `backend/database.py`:

```python
import os
import sqlite3
from contextlib import contextmanager

# Detectar ambiente
DATABASE_URL = os.environ.get('DATABASE_URL', 'alphabot.db')
IS_PRODUCTION = DATABASE_URL.startswith('postgresql://')

if IS_PRODUCTION:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    @contextmanager
    def get_db_connection():
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            conn.close()
else:
    @contextmanager
    def get_db_connection():
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
```

#### 📝 Adicionar `psycopg2` em `backend/requirements.txt`:

```txt
psycopg2-binary==2.9.9
```

### 4. Deploy no Vercel

#### Via Dashboard (Recomendado para primeira vez):

1. **Conectar Repositório:**
   - Acesse [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import do GitHub: `alpha-bot`
   - Autorize o acesso ao repo

2. **Configurar Build:**
   - Framework Preset: `Vite`
   - Root Directory: `./` (padrão)
   - Build Command: `npm run vercel-build` (auto-detectado)
   - Output Directory: `dist` (auto-detectado)

3. **Adicionar Environment Variables:**
   - Cole todas as variáveis da seção 1
   - Marque para aplicar em: Production, Preview, Development

4. **Deploy:**
   - Click "Deploy"
   - Aguarde ~3-5 minutos
   - Acesse URL fornecida (ex: `alpha-bot-xxx.vercel.app`)

#### Via CLI (Para devs experientes):

```bash
# Instalar Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy (primeira vez)
vercel

# Deploy em produção
vercel --prod
```

### 5. Criar Tabelas no Database

**Se usar PostgreSQL:**

1. Acesse o database pelo dashboard (Supabase/Railway/Vercel)
2. Execute o SQL:

```sql
-- Tabela de usuários
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de conversas
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bot_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabela de mensagens
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    author VARCHAR(50) NOT NULL,
    text TEXT NOT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chart_data TEXT,
    suggestions TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Índices para performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
```

**Se usar SQLite (não recomendado):**
- As tabelas serão criadas automaticamente no primeiro acesso
- ⚠️ ATENÇÃO: Dados serão perdidos a cada novo deploy!

### 6. Testar Deploy

1. **Acesse a URL do deploy**
2. **Teste o fluxo completo:**
   - [ ] Registrar novo usuário
   - [ ] Fazer login
   - [ ] Criar conversa no AlphaBot
   - [ ] Fazer upload de arquivo CSV
   - [ ] Enviar pergunta sobre os dados
   - [ ] Criar segunda conversa com arquivo diferente
   - [ ] Alternar entre conversas
   - [ ] Verificar isolamento de dados (bug corrigido)
   - [ ] Deletar conversa
   - [ ] Fazer logout e login novamente
   - [ ] Verificar que conversas persistiram

3. **Verificar Console do Navegador:**
   - Nenhum erro 404 em `/api/*` routes
   - Nenhum erro de CORS
   - localStorage com `alpha_user` e `alpha_active_conversation`

4. **Verificar Logs no Vercel:**
   - Functions → Ver logs em tempo real
   - Verificar se há erros de database connection
   - Verificar se API Key do Gemini está funcionando

### 7. Monitoramento Pós-Deploy

#### Dashboard do Vercel:
- **Analytics**: Uso de banda, requests
- **Functions**: Duração, execuções, erros
- **Logs**: Erros em tempo real

#### Testar com Múltiplos Usuários:
1. Abrir aba anônima + aba normal
2. Registrar 2 usuários diferentes
3. Upload de arquivos diferentes em cada
4. Verificar isolamento de dados
5. Verificar que conversas não aparecem entre usuários

## 🚨 Problemas Comuns e Soluções

### ❌ "502 Bad Gateway"
**Causa:** Backend não está respondendo  
**Solução:**
1. Verificar logs no Vercel
2. Conferir se `GOOGLE_API_KEY` está configurada
3. Conferir se `requirements.txt` tem todas as dependências

### ❌ "Database connection failed"
**Causa:** `DATABASE_URL` incorreta ou database não criado  
**Solução:**
1. Testar connection string localmente
2. Verificar se tabelas foram criadas (ver seção 5)
3. Conferir firewall do database provider

### ❌ "CORS error"
**Causa:** Frontend tentando acessar API de domínio diferente  
**Solução:**
1. Verificar se `vercel.json` tem rotas corretas
2. Conferir se routes tem `/api/auth/(.*)` e `/api/conversations/(.*)`

### ❌ "Files not persisting between conversations"
**Causa:** Session isolation bug  
**Solução:** ✅ JÁ CORRIGIDO! O bug foi resolvido com session keys por conversa

### ❌ "Lost all data after deploy"
**Causa:** Usando SQLite no Vercel (filesystem efêmero)  
**Solução:** Migrar para PostgreSQL externo (ver seção 2)

## 📊 Comparação de Database Providers

| Provider | Preço | Storage | Conexões | Latência | Recomendação |
|----------|-------|---------|----------|----------|--------------|
| **Supabase** | GRÁTIS até 500MB | 500MB | 100 | ~50ms | ⭐⭐⭐⭐⭐ Melhor p/ começar |
| **Railway** | GRÁTIS $5 crédito/mês | 1GB | 20 | ~30ms | ⭐⭐⭐⭐ Ótimo |
| **Vercel Postgres** | $20/mês após trial | Ilimitado | 500 | ~10ms | ⭐⭐⭐ Pago mas rápido |
| **SQLite** | GRÁTIS | Efêmero | 1 | ~0ms | ❌ NÃO usar |

## 🎯 Recomendação Final

**Para Produção:**
1. ✅ **Database**: Supabase PostgreSQL (grátis, confiável)
2. ✅ **Deploy**: Vercel (já configurado)
3. ✅ **Monitoring**: Vercel Analytics + Logs
4. ✅ **Backup**: Supabase tem backup automático

**Tempo estimado:** 30-45 minutos para deploy completo

## 🔗 Links Úteis

- [Vercel Dashboard](https://vercel.com/dashboard)
- [Supabase Dashboard](https://app.supabase.com)
- [Google AI Studio](https://aistudio.google.com/app/apikey)
- [Documentação Vercel Python](https://vercel.com/docs/functions/runtimes/python)

## ✅ Checklist Final

- [ ] Variáveis de ambiente configuradas no Vercel
- [ ] Database provider escolhido (Supabase recomendado)
- [ ] `DATABASE_URL` adicionada ao Vercel
- [ ] Tabelas criadas no database
- [ ] `requirements.txt` atualizado com `psycopg2-binary` (se PostgreSQL)
- [ ] Deploy realizado com sucesso
- [ ] Testes com 2+ usuários simultâneos
- [ ] Session isolation funcionando corretamente
- [ ] Conversas persistindo entre reloads
- [ ] Nenhum erro nos logs do Vercel

---

**Pronto para deploy! 🚀**

Se seguir este guia, seu sistema multi-usuário estará funcionando em produção em menos de 1 hora.
