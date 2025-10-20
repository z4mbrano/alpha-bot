# 🔄 Atualizar Frontend (Vercel) para usar Railway

## 🎯 O que fazer:

O frontend (Vercel) precisa saber onde está o backend (Railway).

---

## 📝 Passo a Passo

### Opção 1: Variável de Ambiente no Vercel (RECOMENDADO)

1. **Acesse:** https://vercel.com/dashboard
2. **Seu projeto:** `alpha-bot`
3. **Settings** → **Environment Variables**
4. **Adicionar nova variável:**
   ```
   Nome: VITE_API_URL
   Valor: https://alphainsights.up.railway.app
   ```
5. **Aplicar em:** Production, Preview, Development
6. **Redeploy:** Deployments → Latest → ⋯ → Redeploy

---

### Opção 2: Commit do `.env.production` (JÁ CRIADO)

Já criei o arquivo `.env.production` na raiz do projeto.

**Fazer commit:**
```bash
git add .env.production
git commit -m "feat: conectar frontend (Vercel) com backend (Railway)"
git push origin main
```

Vercel vai detectar o push e fazer redeploy automático!

---

## 🧪 Testar Após Atualização

1. **Acesse:** https://alpha-bot-six.vercel.app
2. **Tente fazer login/registro**
3. **Deve funcionar!** ✅

---

## 📊 Fluxo Completo

```
Usuário acessa
    ↓
https://alpha-bot-six.vercel.app
    ↓
Frontend carrega
    ↓
Usuário clica em "Login"
    ↓
Frontend faz request para:
https://alphainsights.up.railway.app/api/auth/login
    ↓
Railway processa
    ↓
Retorna resposta
    ↓
Frontend exibe resultado
```

---

## ✅ Checklist

- [x] Arquivo `.env.production` criado
- [ ] Fazer commit e push
- [ ] Aguardar redeploy do Vercel (2-3 min)
- [ ] Testar login no site
- [ ] Compartilhar link: `https://alpha-bot-six.vercel.app`

---

## 🎯 Link para Compartilhar

**URL do seu site:**
```
https://alpha-bot-six.vercel.app
```

**NÃO compartilhe:**
```
https://alphainsights.up.railway.app ❌
```

O Railway é apenas o backend (API interna)!

---

## 🚀 Próximos Passos

1. **Fazer commit:**
   ```bash
   git add .env.production
   git commit -m "feat: conectar com Railway backend"
   git push origin main
   ```

2. **Aguardar Vercel redeploy** (automático)

3. **Testar:** https://alpha-bot-six.vercel.app

4. **Compartilhar** com amigos! 🎉

---

**Status:** ✅ Pronto para commit e deploy final!
