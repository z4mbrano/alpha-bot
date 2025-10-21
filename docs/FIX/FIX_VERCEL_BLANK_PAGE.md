# 🔧 Correção: Site Branco na Vercel

## ❌ Problema

Site aparece completamente branco ao acessar: https://alpha-1we53ew14-z4mbranos-projects.vercel.app

### Causa Raiz

O `vercel.json` estava redirecionando **TODOS os requests** (incluindo assets CSS/JS) para `/index.html`, impedindo o carregamento dos arquivos estáticos.

---

## ✅ Correções Aplicadas

### 1. Atualizado `vite.config.ts`

Adicionadas configurações explícitas de build:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
  },
})
```

**O que isso faz:**
- `base: '/'` - Define a base URL (root)
- `outDir: 'dist'` - Output vai para pasta `dist`
- `assetsDir: 'assets'` - Assets vão para `dist/assets/`
- `sourcemap: false` - Desativa sourcemaps (reduz tamanho)

---

### 2. Corrigido `vercel.json`

**ANTES (❌ Errado):**
```json
{
  "routes": [
    {"src": "/api/health", "dest": "/backend/app.py"},
    {"src": "/api/alphabot/(.*)", "dest": "/backend/app.py"},
    {"src": "/api/chat", "dest": "/backend/app.py"},
    {"src": "/(.*)", "dest": "/index.html"}  // ❌ Pega tudo, inclusive assets!
  ]
}
```

**DEPOIS (✅ Correto):**
```json
{
  "routes": [
    {"src": "/api/health", "dest": "/backend/app.py"},
    {"src": "/api/alphabot/(.*)", "dest": "/backend/app.py"},
    {"src": "/api/chat", "dest": "/backend/app.py"},
    {"src": "/assets/(.*)", "dest": "/assets/$1"},  // ✅ Assets primeiro
    {"src": "/(.*\\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot))", "dest": "/$1"},  // ✅ Arquivos estáticos
    {"src": "/(.*)", "dest": "/index.html"}  // ✅ Só pega rotas HTML
  ]
}
```

**Ordem das Rotas (IMPORTANTE):**
1. Rotas da API (`/api/*`) - Primeiro
2. Assets (`/assets/*`) - Segundo
3. Arquivos estáticos (`.js`, `.css`, etc.) - Terceiro
4. Fallback para SPA (`/index.html`) - Por último

---

## 🔍 Como Diagnosticar Site Branco

### 1. Abrir DevTools do Navegador

**Chrome/Edge:** `F12` ou `Ctrl+Shift+I`

### 2. Verificar Console (Erros JS)

Procure por:
```
❌ Failed to load module script: Expected a JavaScript module script but the server responded with a MIME type of "text/html"
❌ Uncaught SyntaxError: Unexpected token '<'
```

**Causa:** Assets estão retornando HTML em vez de JS/CSS (problema de roteamento)

### 3. Verificar Network (Assets)

- Vá na aba **Network**
- Filtre por **JS** e **CSS**
- Clique em `/assets/index-xxxxx.js`
- **Preview:** Deve mostrar código JavaScript
  - ❌ Se mostrar HTML → Problema de roteamento
  - ✅ Se mostrar JS → Assets carregando corretamente

### 4. Verificar Status Codes

- **200 OK** → Arquivo carregado
- **404 Not Found** → Arquivo não existe (build incorreto)
- **301/302 Redirect** → Redirecionamento incorreto

---

## 📋 Checklist Pós-Correção

- [x] ✅ `vite.config.ts` atualizado
- [x] ✅ `vercel.json` com rotas na ordem correta
- [x] ✅ Build local bem-sucedido
- [ ] ⏳ Commit e push
- [ ] ⏳ Redeploy na Vercel
- [ ] ⏳ Verificar site funcionando

---

## 🚀 Próximos Passos

### 1. Commit e Push

```bash
git add vite.config.ts vercel.json
git commit -m "Fix: Corrigir roteamento de assets na Vercel"
git push origin main
```

### 2. Aguardar Deploy Automático

- Vercel detectará o push e fará novo deploy
- Aguarde 1-2 minutos

### 3. Testar o Site

```bash
# Abrir no navegador
https://alpha-1we53ew14-z4mbranos-projects.vercel.app

# Verificar DevTools:
# 1. Console → Sem erros
# 2. Network → Assets carregando (Status 200)
# 3. Página renderizando corretamente
```

---

## 🧪 Testes de Validação

### Teste 1: Health Check (Backend)
```bash
curl https://alpha-1we53ew14-z4mbranos-projects.vercel.app/api/health
# Esperado: {"status":"ok"}
```

### Teste 2: Assets CSS
```bash
curl -I https://alpha-1we53ew14-z4mbranos-projects.vercel.app/assets/index-CIHdcvFb.css
# Esperado: HTTP/1.1 200 OK
# Content-Type: text/css
```

### Teste 3: Assets JS
```bash
curl -I https://alpha-1we53ew14-z4mbranos-projects.vercel.app/assets/index-BVZFYimh.js
# Esperado: HTTP/1.1 200 OK
# Content-Type: application/javascript
```

### Teste 4: Página Principal
```bash
curl -I https://alpha-1we53ew14-z4mbranos-projects.vercel.app/
# Esperado: HTTP/1.1 200 OK
# Content-Type: text/html
```

---

## 🔄 Se Ainda Estiver Branco

### Opção 1: Limpar Cache da Vercel

1. Acesse: **Project → Settings → General**
2. Role até **Build & Development Settings**
3. Clique em **Clear Build Cache**
4. Faça um novo deploy

### Opção 2: Forçar Redeploy

1. Acesse: **Deployments**
2. Clique nos **⋯** do último deploy
3. Selecione **Redeploy**
4. Marque **Use existing Build Cache** = OFF

### Opção 3: Build Localmente e Deploy Manual

```bash
# Build local
npm run build

# Deploy via CLI
npx vercel --prod
```

---

## 📊 Estrutura de Build Correta

```
dist/
├── index.html          (Entry point)
└── assets/
    ├── index-CIHdcvFb.css   (Styles)
    └── index-BVZFYimh.js    (App bundle)
```

### Validar Build Local

```bash
# 1. Build
npm run build

# 2. Verificar estrutura
ls dist/
ls dist/assets/

# 3. Servir localmente
npx vite preview
# Abrir: http://localhost:4173
```

---

## ✅ Resultado Esperado

Após o deploy:

```
✅ Página carrega sem tela branca
✅ Console sem erros
✅ Assets CSS/JS carregando (Status 200)
✅ React app renderizando
✅ Sidebar e chat funcionando
✅ Backend respondendo em /api/*
```

---

## 🎯 Resumo da Correção

| Problema | Causa | Solução |
|----------|-------|---------|
| Site branco | Assets redirecionando para `/index.html` | Adicionado rotas específicas para assets no `vercel.json` |
| JS não carrega | Rota `/(.*)` pegando tudo | Movido fallback para última posição nas rotas |
| Build inconsistente | Falta de config explícita | Adicionado `base` e `build` no `vite.config.ts` |

---

**Data da Correção:** 18 de outubro de 2025  
**Status:** ✅ Correções aplicadas, aguardando redeploy
