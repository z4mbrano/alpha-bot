# 🚂 Deploy no Railway - Guia Completo

## Por que Railway ao invés do Vercel?

### ✅ Vantagens do Railway:
- **SQLite Persistente**: Volume dedicado, dados não são perdidos
- **Sem Cold Starts**: Aplicação sempre ativa
- **Sem Timeout de 10s**: Perfeito para processamento de IA
- **$5 Grátis/Mês**: Suficiente para testes e pequeno uso
- **Deploy Automático**: Conecta ao GitHub
- **Logs em Tempo Real**: Debug mais fácil
- **PostgreSQL Grátis**: Se quiser migrar depois

### ❌ Limitações do Vercel (que Railway resolve):
- Filesystem efêmero (dados perdidos)
- Timeout de 10 segundos (ruim para IA)
- Cold starts frequentes
- Não otimizado para aplicações stateful

---

## 🎯 Passo a Passo - Deploy em 10 Minutos

### 1️⃣ Criar Conta no Railway

1. Acesse: https://railway.app
2. Click em **"Start a New Project"**
3. Login com GitHub (recomendado)

---

### 2️⃣ Conectar Repositório

1. Na dashboard do Railway:
   - Click em **"New Project"**
   - Selecione **"Deploy from GitHub repo"**
   - Autorize o Railway a acessar seus repositórios
   - Selecione: **`z4mbrano/alpha-bot`**

2. Railway vai detectar automaticamente:
   - ✅ Python project
   - ✅ requirements.txt
   - ✅ Procfile

---

### 3️⃣ Criar Volume para Database (IMPORTANTE!)

O SQLite precisa de um volume persistente para não perder dados:

1. No projeto Railway, click no serviço **"alpha-bot"**
2. Vá em **"Data"** → **"+ Volume"**
3. Configure:
   - **Mount Path**: `/data`
   - **Size**: `1 GB` (suficiente para começar)
4. Click em **"Add Volume"**

**Por que é importante:**
- ✅ Dados persistem entre deploys
- ✅ Database não é recriado a cada restart
- ✅ Backup automático do Railway

---

### 4️⃣ Configurar Variáveis de Ambiente

1. No serviço, vá em **"Variables"**
2. Click em **"+ New Variable"**
3. Adicione as seguintes variáveis:

```env
# ⚠️ OBRIGATÓRIAS

# API Key do Google Gemini
GOOGLE_API_KEY=sua_chave_aqui

# Chave secreta do Flask (para sessions)
FLASK_SECRET_KEY=sua_chave_secreta_64_caracteres

# Path do volume (Railway injeta automaticamente, mas confirme)
RAILWAY_VOLUME_MOUNT_PATH=/data

# 📁 OPCIONAL - Google Drive (apenas se usar DriveBot)
GOOGLE_SERVICE_ACCOUNT_INFO={"type":"service_account","project_id":"..."}
```

#### Como obter as chaves:

**GOOGLE_API_KEY:**
1. Acesse: https://aistudio.google.com/app/apikey
2. Click em "Create API Key"
3. Copie a chave

**FLASK_SECRET_KEY:**
Execute no terminal:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### 5️⃣ Deploy!

1. Railway faz deploy automático após configurar
2. Aguarde ~2-3 minutos
3. Quando concluir, você verá:
   - ✅ **"Deploy Success"**
   - 🔗 URL pública (ex: `alpha-bot-production.up.railway.app`)

---

### 6️⃣ Configurar Domínio Público

1. No serviço, vá em **"Settings"**
2. Seção **"Networking"**
3. Click em **"Generate Domain"**
4. Railway vai gerar: `https://alpha-bot-production.up.railway.app`

**Opção: Domínio Customizado**
- Click em **"Custom Domain"**
- Adicione seu domínio (ex: `alphabot.seusite.com`)
- Configure DNS conforme instruções

---

### 7️⃣ Atualizar Frontend (IMPORTANTE!)

O frontend precisa apontar para a nova URL do Railway:

1. **Localmente** (desenvolvimento):
   - Mantenha: `http://localhost:5000`

2. **Produção** (Vercel):
   - Atualizar variável de ambiente no Vercel:
   ```env
   VITE_API_URL=https://alpha-bot-production.up.railway.app
   ```

**Ou** criar arquivo `.env.production`:
```env
VITE_API_URL=https://seu-dominio.up.railway.app
```

---

### 8️⃣ Testar o Deploy

#### Via Browser:
```
https://seu-dominio.up.railway.app/api/health
```

**Resposta esperada:**
```json
{"status": "ok", "service": "Alpha Insights Chat Backend"}
```

#### Via Terminal:
```bash
# Health check
curl https://seu-dominio.up.railway.app/api/health

# Registrar usuário
curl -X POST https://seu-dominio.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"teste","password":"senha123"}'

# Login
curl -X POST https://seu-dominio.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"teste","password":"senha123"}'
```

---

## 📊 Monitoramento e Logs

### Ver Logs em Tempo Real:

1. No Railway, vá no serviço **"alpha-bot"**
2. Click em **"Deployments"**
3. Selecione o deploy ativo
4. Veja logs em tempo real!

**Comandos úteis nos logs:**
- `🚂 Railway: Usando database em /data/alphabot.db` - Database configurado
- `✅ Database inicializado com sucesso` - Tabelas criadas
- `🚂 Iniciando em modo produção na porta 8080` - App rodando

### Métricas:

1. Dashboard do Railway mostra:
   - 📊 CPU Usage
   - 💾 Memory Usage
   - 🌐 Request Count
   - ⏱️ Response Time

---

## 🔄 Deploy Automático (CI/CD)

**Railway atualiza automaticamente quando você faz push!**

```bash
# Fazer alterações no código
git add .
git commit -m "feat: nova funcionalidade"
git push origin main

# Railway detecta o push e faz redeploy automático!
# Tempo: ~2-3 minutos
```

---

## 💰 Custos e Limites

### Tier Gratuito:
- ✅ **$5 de crédito/mês** (renovável)
- ✅ **500 horas de execução/mês**
- ✅ **100 GB de bandwidth**
- ✅ **1 GB de volume grátis**

### Quanto consome o Alpha Bot:
- ~$1-2/mês com uso moderado
- Volume de 1GB é suficiente para milhares de conversas
- Bandwidth: ~10-20 GB/mês (uso normal)

**Resumo:** Tier gratuito é suficiente para testes e uso pessoal! 🎉

---

## 🛠️ Troubleshooting

### ❌ "Application failed to respond"
**Causa:** App não está escutando na porta correta

**Solução:** Verificar que `app.py` usa `PORT` do ambiente:
```python
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
```

### ❌ "Database locked"
**Causa:** Volume não foi criado ou está cheio

**Solução:**
1. Verificar que volume está montado em `/data`
2. Aumentar tamanho do volume se necessário

### ❌ "Module not found"
**Causa:** Dependência faltando em `requirements.txt`

**Solução:**
1. Adicionar dependência em `backend/requirements.txt`
2. Fazer commit e push
3. Railway fará redeploy

### ❌ "CORS error"
**Causa:** Frontend não está na whitelist

**Solução:** Atualizar CORS em `app.py`:
```python
CORS(app, origins=[
    "http://localhost:5173",
    "https://seu-dominio.vercel.app",
    "https://seu-dominio.up.railway.app"
])
```

---

## 🎯 Checklist Final

Antes de considerar completo, verifique:

- [ ] Volume de 1GB criado e montado em `/data`
- [ ] `GOOGLE_API_KEY` configurada
- [ ] `FLASK_SECRET_KEY` configurada
- [ ] Deploy com sucesso (status verde)
- [ ] `/api/health` retorna 200 OK
- [ ] Registro de usuário funciona
- [ ] Login funciona
- [ ] Criar conversa funciona
- [ ] Upload de arquivo funciona
- [ ] Dados persistem após restart (testar!)
- [ ] Frontend atualizado com nova URL da API

---

## 📚 Recursos Úteis

- **Dashboard Railway:** https://railway.app/dashboard
- **Documentação:** https://docs.railway.app
- **Comunidade Discord:** https://discord.gg/railway
- **Status Page:** https://status.railway.app

---

## 🚀 Próximos Passos (Opcional)

### 1. Adicionar PostgreSQL (se crescer muito)

Railway oferece PostgreSQL grátis:
1. No projeto, click em **"+ New"**
2. Selecione **"Database" → "PostgreSQL"**
3. Railway injeta `DATABASE_URL` automaticamente
4. Modificar `database.py` para usar PostgreSQL

### 2. Configurar Domínio Customizado

1. Comprar domínio (ex: Namecheap, Google Domains)
2. No Railway: Settings → Custom Domain
3. Adicionar CNAME no seu provedor de DNS

### 3. Configurar Backups

Railway faz backup automático do volume, mas você pode:
1. Criar script de backup manual
2. Exportar database periodicamente
3. Usar Railway CLI para download

### 4. Monitoramento Avançado

Adicionar ferramentas:
- Sentry (error tracking)
- Datadog (métricas)
- Uptime Robot (monitoramento de disponibilidade)

---

## ✅ Comparação: Railway vs Vercel

| Recurso | Railway | Vercel |
|---------|---------|--------|
| SQLite Persistente | ✅ Sim | ❌ Efêmero |
| Cold Starts | ✅ Não | ⚠️ Sim |
| Timeout | ✅ Sem limite | ❌ 10s |
| Custo Inicial | ✅ $5 grátis/mês | ✅ Grátis |
| Deploy GitHub | ✅ Sim | ✅ Sim |
| Logs Real-time | ✅ Sim | ✅ Sim |
| Melhor Para | Stateful apps | Serverless/JAMstack |

**Conclusão:** Railway é melhor para o Alpha Bot! 🎯

---

## 🎉 Pronto!

Seguindo este guia, seu Alpha Bot estará rodando no Railway com:
- ✅ SQLite persistente (dados seguros)
- ✅ Deploy automático (push to deploy)
- ✅ Monitoramento em tempo real
- ✅ Custo zero ou muito baixo
- ✅ Performance excelente

**Tempo total:** 10-15 minutos

**URL final:** `https://alpha-bot-production.up.railway.app`

Agora é só usar! 🚀
