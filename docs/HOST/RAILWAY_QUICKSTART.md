# 🚀 Deploy Rápido no Railway

## ⚡ 5 Passos - 10 Minutos

### 1. Criar Conta
👉 https://railway.app → Login com GitHub

### 2. Novo Projeto
- **New Project** → **Deploy from GitHub repo**
- Selecione: `z4mbrano/alpha-bot`

### 3. Criar Volume (IMPORTANTE!)
- Click no serviço → **Data** → **+ Volume**
- Mount Path: `/data`
- Size: `1 GB`

### 4. Variáveis de Ambiente
```env
GOOGLE_API_KEY=sua_chave_gemini
FLASK_SECRET_KEY=sua_chave_secreta_64_chars
```

### 5. Deploy Automático!
Railway faz deploy e gera URL: `https://alpha-bot-production.up.railway.app`

---

## ✅ Por que Railway?

- ✅ **SQLite Persistente** (dados não são perdidos!)
- ✅ **Sem Cold Starts** (sempre ativo)
- ✅ **$5 Grátis/Mês** (suficiente para uso pessoal)
- ✅ **Deploy Automático** (push to deploy)
- ✅ **Sem Timeout** (perfeito para IA)

---

## 📝 Arquivos Já Preparados

- ✅ `Procfile` - Comando de start
- ✅ `railway.json` - Configuração
- ✅ `nixpacks.toml` - Build config
- ✅ `app.py` - Detecta Railway e usa porta correta
- ✅ `database.py` - Usa volume persistente `/data`

---

## 🎯 Testar

```bash
# Health check
curl https://seu-dominio.up.railway.app/api/health

# Registrar
curl -X POST https://seu-dominio.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"teste","password":"senha123"}'
```

---

## 📚 Guia Completo

Ver: `DEPLOY_RAILWAY.md` (documentação detalhada)

---

**Pronto para deploy!** 🚂
