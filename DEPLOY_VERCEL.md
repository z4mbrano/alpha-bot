# 🚀 Guia de Deploy na Vercel - Alpha Bot

## 📋 Visão Geral

Este guia explica como fazer deploy do **Alpha Bot** (projeto híbrido Python + React) na Vercel.

---

## ✅ Arquivos de Configuração Criados

### 1. `vercel.json`
Configura o build e roteamento do projeto híbrido:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "backend/app.py",
      "use": "@vercel/python"
    },
    {
      "src": "package.json",
      "use": "@vercel/static-build"
    }
  ],
  "routes": [
    { "src": "/api/(.*)", "dest": "/backend/app.py" },
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

### 2. `.vercelignore`
Otimiza o deploy ignorando arquivos desnecessários:
- `__pycache__/` e `*.pyc`
- `node_modules/`
- Documentação e testes
- Backups

### 3. `package.json` (atualizado)
Adicionado script `vercel-build` que corrige permissões:

```json
{
  "scripts": {
    "vercel-build": "chmod +x ./node_modules/.bin/vite && vite build"
  }
}
```

### 4. URLs Dinâmicas
Frontend agora usa `import.meta.env.VITE_API_URL`:
- **Desenvolvimento:** `http://localhost:5000`
- **Produção:** URL relativa automaticamente

---

## 🔧 Configurar Variáveis de Ambiente na Vercel

### Via Dashboard

1. Acesse seu projeto na Vercel
2. Vá em **Settings → Environment Variables**
3. Adicione as seguintes variáveis:

| Nome | Valor | Tipo |
|------|-------|------|
| `DRIVEBOT_API_KEY` | Sua chave do Gemini para DriveBot | Secret |
| `ALPHABOT_API_KEY` | Sua chave do Gemini para AlphaBot | Secret |
| `GOOGLE_SERVICE_ACCOUNT_INFO` | JSON da Service Account (completo) | Secret |
| `FLASK_ENV` | `production` | Plain Text |

### Via CLI (Alternativa)

```bash
# Instalar Vercel CLI
npm i -g vercel

# Login
vercel login

# Adicionar secrets
vercel secrets add drivebot-api-key "sua_chave_aqui"
vercel secrets add alphabot-api-key "sua_chave_aqui"
vercel secrets add google-service-account-info '{"type":"service_account",...}'
```

---

## 📦 Deploy

### Método 1: Deploy via GitHub (Recomendado)

1. **Commit e Push:**
   ```bash
   git add .
   git commit -m "Configurar para deploy na Vercel"
   git push origin main
   ```

2. **Conectar GitHub na Vercel:**
   - Acesse [vercel.com](https://vercel.com)
   - **New Project → Import Git Repository**
   - Selecione o repositório `alpha-bot`
   - A Vercel detectará automaticamente o `vercel.json`

3. **Deploy Automático:**
   - Vercel fará o build automaticamente
   - Cada push para `main` dispara novo deploy

### Método 2: Deploy via CLI

```bash
# Na raiz do projeto
vercel

# Para produção
vercel --prod
```

---

## 🧪 Testar o Deploy

### 1. Health Check
```bash
curl https://your-app.vercel.app/api/health
```

Resposta esperada:
```json
{"status": "ok"}
```

### 2. AlphaBot Upload
```bash
curl -X POST https://your-app.vercel.app/api/alphabot/upload \
  -F "files=@test.csv"
```

### 3. DriveBot Chat
```bash
curl -X POST https://your-app.vercel.app/api/drivebot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "your_drive_folder_id"}'
```

---

## ⚠️ Problemas Comuns e Soluções

### 1. Erro: `Permission denied`

**Causa:** Permissões de execução não configuradas no Linux (Vercel).

**Solução:** ✅ **JÁ RESOLVIDO** com o script `vercel-build` no `package.json`:
```json
"vercel-build": "chmod +x ./node_modules/.bin/vite && vite build"
```

---

### 2. Erro: `Module not found: google.generativeai`

**Causa:** Dependências Python não instaladas.

**Solução:** Verificar `backend/requirements.txt`:
```txt
Flask==3.0.0
Flask-CORS==4.0.0
google-generativeai==0.3.0
google-api-python-client==2.100.0
google-auth==2.23.0
pandas==2.0.0
python-dotenv==1.0.0
openpyxl==3.1.2
```

---

### 3. Erro: `429 API Quota Exceeded`

**Causa:** Limite de 50 requests/dia do Gemini Free Tier.

**Soluções:**
- **Temporária:** Aguardar reset (24h)
- **Permanente:** Fazer upgrade para plano pago
- **Alternativa:** Usar API keys diferentes para DriveBot e AlphaBot

---

### 4. Erro: `Google Drive API not enabled`

**Causa:** APIs não ativadas no Google Cloud.

**Solução:**
1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. **APIs & Services → Library**
3. Ativar:
   - Google Drive API
   - Google Sheets API

---

### 5. Erro: `CORS blocked`

**Causa:** Backend não permite requisições do domínio da Vercel.

**Solução:** Atualizar CORS no `backend/app.py`:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://your-app.vercel.app",
            "http://localhost:5173"
        ]
    }
})
```

---

## 📊 Estrutura de Deployment

```
Vercel Deploy
├── Frontend (Static Build)
│   ├── Build: npm run vercel-build
│   ├── Output: dist/
│   └── Serve: / (todas as rotas exceto /api/*)
│
└── Backend (Serverless Functions)
    ├── Runtime: Python 3.9
    ├── Entry: backend/app.py
    └── Routes: /api/*
```

---

## 🎯 Checklist de Deploy

- [x] `vercel.json` criado
- [x] `.vercelignore` criado
- [x] `package.json` atualizado com `vercel-build`
- [x] URLs hardcoded substituídas por `import.meta.env.VITE_API_URL`
- [ ] Variáveis de ambiente configuradas na Vercel
- [ ] Repositório conectado ao GitHub
- [ ] Deploy realizado
- [ ] Health check testado
- [ ] Upload de arquivos testado
- [ ] Chat testado

---

## 🚀 Comandos Úteis

```bash
# Testar build localmente
npm run build

# Testar backend localmente
cd backend && python app.py

# Ver logs do deploy na Vercel
vercel logs

# Listar deploys
vercel ls

# Rollback para deploy anterior
vercel rollback
```

---

## 📈 Melhorias Futuras

### 1. Adicionar Cache
```json
// vercel.json
{
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

### 2. Adicionar Rate Limiting
```python
# backend/app.py
from flask_limiter import Limiter

limiter = Limiter(
    app=app,
    key_func=lambda: request.headers.get('X-Forwarded-For', request.remote_addr),
    default_limits=["100 per hour"]
)
```

### 3. Monitoramento
- Usar **Vercel Analytics** (gratuito)
- Adicionar **Sentry** para error tracking
- Configurar **Logtail** para logs centralizados

---

## ✅ Resultado Esperado

Após seguir este guia, você terá:

✅ Frontend React servido estaticamente  
✅ Backend Flask como Serverless Functions  
✅ Roteamento automático entre `/api/*` e frontend  
✅ Variáveis de ambiente seguras  
✅ Deploy contínuo via GitHub  
✅ URLs otimizadas para produção  

---

**Última atualização:** 18 de outubro de 2025  
**Status:** ✅ Pronto para Deploy
