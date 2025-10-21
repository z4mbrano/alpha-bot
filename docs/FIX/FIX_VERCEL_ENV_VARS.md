# 🔧 Correção: Erro de Environment Variables na Vercel

## ❌ Problema

```
Environment Variable "DRIVEBOT_API_KEY" references Secret "drivebot-api-key", 
which does not exist.
```

### Causa

O arquivo `vercel.json` estava tentando referenciar **Vercel Secrets** que não existem:

```json
// ❌ ERRADO - vercel.json (antes)
{
  "env": {
    "DRIVEBOT_API_KEY": "@drivebot-api-key",  // ❌ Tentando usar secret
    "ALPHABOT_API_KEY": "@alphabot-api-key",   // ❌ Tentando usar secret
    "GOOGLE_SERVICE_ACCOUNT_INFO": "@google-service-account-info" // ❌ Tentando usar secret
  }
}
```

**Secrets (`@secret-name`)** são para valores compartilhados entre múltiplos projetos. Para um único projeto, devemos usar **Environment Variables** configuradas no Dashboard.

---

## ✅ Solução Aplicada

### 1. Remover Seção `env` do vercel.json

```json
// ✅ CORRETO - vercel.json (depois)
{
  "version": 2,
  "builds": [...],
  "routes": [...]
  // ✅ Sem seção "env"
}
```

### 2. Configurar Variables no Dashboard da Vercel

As variáveis de ambiente devem ser configuradas **manualmente no Dashboard**:

1. Acesse: **Projeto → Settings → Environment Variables**
2. Adicione cada variável:
   - `DRIVEBOT_API_KEY`
   - `ALPHABOT_API_KEY`
   - `GOOGLE_SERVICE_ACCOUNT_INFO`
   - `FLASK_ENV=production`

---

## 📋 Passo a Passo para Configurar

### 1. Commit e Push das Correções

```bash
git add vercel.json DEPLOY_VERCEL.md
git commit -m "Fix: Remover referências a secrets do vercel.json"
git push origin main
```

### 2. Acessar Dashboard da Vercel

- Vá em: https://vercel.com/dashboard
- Selecione seu projeto `alpha-bot`

### 3. Adicionar Environment Variables

**Settings → Environment Variables → Add New**

#### Adicionar: DRIVEBOT_API_KEY
```
Name: DRIVEBOT_API_KEY
Value: [Cole sua chave do Gemini]
Environments: ✓ Production ✓ Preview ✓ Development
```

#### Adicionar: ALPHABOT_API_KEY
```
Name: ALPHABOT_API_KEY
Value: [Cole sua chave do Gemini]
Environments: ✓ Production ✓ Preview ✓ Development
```

#### Adicionar: GOOGLE_SERVICE_ACCOUNT_INFO
```
Name: GOOGLE_SERVICE_ACCOUNT_INFO
Value: [Cole o JSON completo do service-account.json]
Environments: ✓ Production ✓ Preview ✓ Development
```

**Exemplo do valor:**
```json
{"type":"service_account","project_id":"seu-projeto","private_key_id":"abc123...","private_key":"-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n","client_email":"[email protected]","client_id":"123456789","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/..."}
```

#### Adicionar: FLASK_ENV
```
Name: FLASK_ENV
Value: production
Environments: ✓ Production
```

### 4. Redeploy

Após adicionar as variáveis:
- **Deployments → ⋯ (menu) → Redeploy**
- Ou faça um novo commit qualquer para disparar novo deploy

---

## 🎯 Diferença: Secrets vs Environment Variables

### Vercel Secrets (`@secret-name`)
- ✅ Para valores **compartilhados entre múltiplos projetos**
- ✅ Criados via CLI: `vercel secrets add my-secret "value"`
- ✅ Referenciados no `vercel.json` com `@` prefix
- ❌ **Não funcionam** para projetos individuais sem criar o secret primeiro

### Environment Variables
- ✅ Para valores **específicos de um projeto**
- ✅ Configurados no Dashboard: **Settings → Environment Variables**
- ✅ Não precisam de `@` prefix
- ✅ **Recomendado para a maioria dos casos**

---

## ✅ Resultado Esperado

Após seguir os passos acima:

```
✅ vercel.json sem seção "env"
✅ Variáveis configuradas no Dashboard
✅ Deploy bem-sucedido
✅ Backend pode acessar as variáveis via os.getenv()
```

### Validar no Backend

O Python acessa as variáveis normalmente:

```python
# backend/app.py
import os
from dotenv import load_dotenv

load_dotenv()

DRIVEBOT_API_KEY = os.getenv('DRIVEBOT_API_KEY')
ALPHABOT_API_KEY = os.getenv('ALPHABOT_API_KEY')
# ✅ Funciona perfeitamente!
```

---

## 🧪 Testar após Deploy

```bash
# 1. Health check
curl https://your-app.vercel.app/api/health

# 2. Verificar se as variáveis estão carregando
# (o backend deve responder sem erros de "API key not found")
```

---

## ✅ Status

- [x] ✅ `vercel.json` corrigido (seção `env` removida)
- [x] ✅ `DEPLOY_VERCEL.md` atualizado com instruções claras
- [ ] ⏳ Fazer commit e push
- [ ] ⏳ Configurar Environment Variables no Dashboard
- [ ] ⏳ Redeploy na Vercel
- [ ] ⏳ Testar em produção

---

**Resultado:** O erro "Secret does not exist" foi resolvido! Agora basta configurar as variáveis no Dashboard da Vercel. 🎉
