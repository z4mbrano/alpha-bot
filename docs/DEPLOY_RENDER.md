# Guia de Deploy no Render.com 

Este guia detalha como fazer o deploy do AlphaBot no Render.com com PostgreSQL gratuito.

## 🚀 Configuração no Render

### 1. Criar Conta no Render
- Acesse [render.com](https://render.com)
- Conecte sua conta GitHub
- Autorize acesso ao repositório `alpha-bot`

### 2. Criar Banco PostgreSQL (Gratuito)

1. No Dashboard do Render, clique **"New +"**
2. Selecione **"PostgreSQL"**
3. Configure:
   - **Name**: `alpha-bot-postgres`
   - **Database Name**: `alphabot`
   - **User**: `alphabot_user`
   - **Region**: Oregon (US West)
   - **Plan**: **Free**
4. Clique **"Create Database"**
5. **Aguarde 2-3 minutos** para provisionar
6. **COPIE a DATABASE_URL** que aparecerá no painel

### 3. Criar Web Service

1. No Dashboard, clique **"New +"**
2. Selecione **"Web Service"**
3. Conecte repositório:
   - **Repository**: `alpha-bot`
   - **Branch**: `main`
4. Configure:
   - **Name**: `alpha-bot-backend`
   - **Language**: **Docker**
   - **Region**: Oregon (US West)
   - **Plan**: **Free**
   - **Dockerfile Path**: `./Dockerfile`

### 4. Configurar Environment Variables

No painel do Web Service, vá para **Environment** e adicione:

```
DATABASE_URL=postgresql://alphabot_user:[PASSWORD]@[HOST]/alphabot
RENDER=true
FLASK_ENV=production
PYTHONPATH=/app
PORT=10000

# APIs do Google (copie do .env local)
ALPHABOT_API_KEY=sua_chave_google_ai
DRIVEBOT_API_KEY=sua_chave_google_ai  
GOOGLE_SERVICE_ACCOUNT_INFO=seu_json_credentials_completo
```

**⚠️ IMPORTANTE:** 
- Substitua `[PASSWORD]` e `[HOST]` pelos valores reais da DATABASE_URL copiada
- Cole o JSON completo das credenciais Google em `GOOGLE_SERVICE_ACCOUNT_INFO`

### 5. Deploy Automático

1. Clique **"Create Web Service"**
2. Render irá:
   - Clonar o repositório
   - Executar `docker build`
   - Instalar dependências
   - Inicializar PostgreSQL automaticamente
3. **Aguarde 5-10 minutos** para primeiro deploy

## 🔗 Configurar Frontend (Vercel)

Após backend no ar, configure o frontend:

### 1. Atualizar URL da API

No arquivo `src/services/api.ts`:

```typescript
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://sua-app.onrender.com/api'
  : 'http://localhost:5000/api'
```

### 2. Deploy no Vercel

```bash
npm run build
vercel --prod
```

## ✅ Verificar Deploy

### 1. Testar Health Check

Acesse: `https://sua-app.onrender.com/api/health`

Resposta esperada:
```json
{
  "status": "ok",
  "service": "Alpha Insights Chat Backend",
  "database": "healthy",
  "environment": {
    "render": true,
    "postgres": true
  }
}
```

### 2. Testar Funcionalidades

1. **Cadastro de usuário**: `POST /api/auth/register`
2. **Login**: `POST /api/auth/login`
3. **AlphaBot**: Upload de planilha
4. **DriveBot**: Conectar pasta Google Drive

## 🔄 Migração de Dados (Opcional)

Se você tem dados no SQLite local, pode migrá-los:

### 1. Local para Render

```bash
# No terminal local, configure DATABASE_URL do Render:
$env:DATABASE_URL="postgresql://alphabot_user:[PASSWORD]@[HOST]/alphabot"

# Execute migração:
cd backend
python migrate_to_postgresql.py
```

### 2. Verificar Migração

```bash
python migrate_to_postgresql.py --test
```

## 📊 Monitoramento

### Logs em Tempo Real
- No painel Render → Web Service → **Logs**
- Filtre por `ERROR` ou `WARNING` se houver problemas

### Métricas de Uso
- Dashboard Render mostra:
  - CPU/Memory usage
  - Request count
  - Response times
  - Uptime

## 🛠️ Troubleshooting

### Problema: Build falha

**Solução**:
1. Verifique se `Dockerfile` existe na raiz
2. Confirme que `backend/requirements.txt` tem `psycopg2-binary`
3. Veja logs de build no painel

### Problema: Database connection failed

**Solução**:
1. Verifique se PostgreSQL foi criado na mesma região
2. Confirme `DATABASE_URL` está correta
3. Teste conexão: `https://sua-app.onrender.com/api/health`

### Problema: Import errors

**Solução**:
1. Confirme `PYTHONPATH=/app` nas env vars
2. Verifique estrutura de pastas no repositório
3. Restart web service se necessário

## 🎯 URLs Finais

Após deploy bem-sucedido:

- **Backend API**: `https://alpha-bot-backend-[ID].onrender.com`
- **Frontend**: `https://alpha-bot-frontend.vercel.app` 
- **Health Check**: `https://alpha-bot-backend-[ID].onrender.com/api/health`

## 💡 Otimizações Futuras

### Plano Paid ($7/mês)
- **Zero downtime** (não hiberna)
- **SSH access** para debug
- **Persistent disks** (para uploads)
- **Custom domains**

### Escalar Aplicação
- Redis para cache (sessions)
- CDN para assets estáticos
- Load balancer para múltiplas instâncias

---

## 🚀 Deploy Rápido (Resumo)

```bash
# 1. Push código para GitHub
git add .
git commit -m "Preparar deploy Render"
git push origin main

# 2. Render Dashboard
# - New PostgreSQL → Copiar DATABASE_URL
# - New Web Service → Docker → Definir env vars

# 3. Aguardar deploy (5-10 min)

# 4. Testar API
curl https://sua-app.onrender.com/api/health
```

**🎉 Pronto! AlphaBot hospedado no Render com PostgreSQL gratuito!**