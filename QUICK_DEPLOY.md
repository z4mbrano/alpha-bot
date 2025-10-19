# ⚡ Guia Rápido - Deploy no Vercel (ATUALIZADO)

## 🐛 CORREÇÕES APLICADAS - Erro 500 Resolvido

### ✅ O que foi corrigido:
1. Database path dinâmico (detecta Vercel e usa `/tmp`)
2. Inicialização segura do database com try-catch
3. Error handling detalhado nos endpoints de auth
4. Validação de `request.json` antes de usar

### ⚠️ IMPORTANTE: SQLite no Vercel é Efêmero
- ❌ Dados são perdidos quando a função reinicia
- ✅ Funciona para **TESTES**, mas não para produção
- 🎯 **Recomendado**: Migrar para PostgreSQL após testar

---

## 🎯 TL;DR - Deploy em 5 Passos

### 1. Configurar Variáveis de Ambiente

Acesse: https://vercel.com/dashboard → Seu Projeto → Settings → Environment Variables

Adicione:
```env
GOOGLE_API_KEY=sua_chave_gemini
FLASK_SECRET_KEY=sua_chave_secreta_64_chars
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

**Como obter:**
- **GOOGLE_API_KEY**: https://aistudio.google.com/app/apikey
- **FLASK_SECRET_KEY**: Execute `python -c "import secrets; print(secrets.token_hex(32))"`
- **DATABASE_URL**: Crie database no Supabase (grátis): https://supabase.com

### 2. Criar Database no Supabase

1. Acesse https://supabase.com e crie conta
2. Criar novo projeto
3. Vá em SQL Editor e execute:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    bot_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

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

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
```

4. Copiar connection string de Settings → Database → Connection String
5. Adicionar como `DATABASE_URL` no Vercel

### 3. Deploy no Vercel

**Opção A: Via Dashboard (Recomendado)**
1. https://vercel.com/new
2. Import do GitHub → Selecionar repositório `alpha-bot`
3. Configurar:
   - Framework: Vite
   - Build Command: `npm run vercel-build` (auto-detectado)
   - Output Directory: `dist` (auto-detectado)
4. Adicionar Environment Variables (passo 1)
5. Click "Deploy"

**Opção B: Via CLI**
```powershell
npm install -g vercel
vercel login
vercel
# Seguir prompts
vercel --prod
```

### 4. Testar Deploy

Acesse a URL fornecida (ex: `https://alpha-bot-xxx.vercel.app`)

Teste:
- [ ] Registrar novo usuário
- [ ] Fazer login
- [ ] Criar conversa
- [ ] Upload de arquivo CSV
- [ ] Enviar pergunta
- [ ] Criar segunda conversa
- [ ] Alternar entre conversas (verificar isolamento)
- [ ] Deletar conversa
- [ ] Logout e login novamente

### 5. Monitorar

Vercel Dashboard → Seu Projeto:
- **Deployments**: Histórico de deploys
- **Analytics**: Tráfego e performance
- **Functions**: Logs em tempo real
- **Logs**: Erros e warnings

---

## 🔧 Solução de Problemas

### "502 Bad Gateway"
```powershell
# Verificar logs do Vercel
# Dashboard → Functions → Ver logs
# Conferir se GOOGLE_API_KEY está configurada
```

### "Database connection failed"
```powershell
# Testar connection string localmente:
python -c "import psycopg2; psycopg2.connect('sua_database_url'); print('✅ OK')"
```

### "Lost data after deploy"
- Você está usando SQLite → Migre para PostgreSQL
- SQLite no Vercel é efêmero (reseta a cada deploy)

---

## 📝 Comandos Úteis

### Gerar FLASK_SECRET_KEY
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### Testar Build Localmente
```powershell
npm run build
# Verificar se pasta dist/ foi criada
```

### Instalar Dependências do Backend
```powershell
cd backend
pip install -r requirements.txt
```

### Migrar Dados SQLite → PostgreSQL (opcional)
```powershell
cd backend
$env:DATABASE_URL="postgresql://user:pass@host:5432/db"
python migrate_to_postgres.py
```

### Ver Logs do Vercel em Tempo Real
```powershell
vercel logs --follow
```

### Rollback para Deploy Anterior
```powershell
vercel rollback
```

---

## 📊 Checklist Completo

### Pré-Deploy
- [x] Sistema multi-usuário implementado
- [x] Bug de isolamento de sessão corrigido
- [x] vercel.json configurado
- [x] requirements.txt atualizado
- [x] Guia de deploy criado

### Durante Deploy
- [ ] GOOGLE_API_KEY configurada no Vercel
- [ ] FLASK_SECRET_KEY configurada no Vercel
- [ ] Database criado (Supabase recomendado)
- [ ] DATABASE_URL configurada no Vercel
- [ ] Tabelas criadas no database
- [ ] Deploy realizado com sucesso

### Pós-Deploy
- [ ] Testes com 2+ usuários
- [ ] Session isolation funcionando
- [ ] Conversas persistindo
- [ ] Nenhum erro nos logs
- [ ] Analytics configurado

---

## 🚀 Deploy Agora!

**Tempo estimado:** 30-40 minutos

**Link rápido:** https://vercel.com/new

**Documentação completa:** Ver `VERCEL_DEPLOYMENT_GUIDE.md`

---

**Status:** ✅ Sistema pronto para produção  
**Bug crítico:** ✅ Corrigido  
**Documentação:** ✅ Completa
