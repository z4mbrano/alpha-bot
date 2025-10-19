# 🔧 Correção: Acesso à API de Outros Dispositivos

## ❌ Problema

Ao testar o AlphaBot em outros dispositivos (celular, outro computador) na **mesma rede Wi-Fi**, apareciam erros:

```
Failed to load resource: net::ERR_CONNECTION_REFUSED
❌ Erro ao enviar arquivos: TypeError: Failed to fetch
```

**Na sua máquina funcionava perfeitamente.**

---

## 🔍 Causa Raiz

### Problema 1: Backend escutando apenas em `localhost`

**Código original:**
```python
# backend/app.py
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
```

**Problema:**
- `host='localhost'` faz o Flask aceitar conexões **APENAS da própria máquina**
- Outros dispositivos na rede tentam se conectar → **RECUSADO**

### Problema 2: Frontend usando `localhost` fixo

**Código original:**
```typescript
// src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'
```

**Problema:**
- `localhost` no celular/outro computador → aponta para **eles mesmos**, não para seu servidor
- Eles tentam se conectar ao próprio dispositivo (onde não há servidor) → **FALHA**

---

## ✅ Soluções Aplicadas

### Solução 1: Backend aceita conexões externas

**Mudança em `backend/app.py`:**
```python
if __name__ == '__main__':
    # host='0.0.0.0' permite conexões de QUALQUER IP na rede
    app.run(debug=True, host='0.0.0.0', port=5000)
```

**O que faz:**
- `0.0.0.0` = "escute em todas as interfaces de rede"
- Agora aceita conexões de:
  - ✅ Sua própria máquina (`localhost`, `127.0.0.1`)
  - ✅ Outros dispositivos na mesma rede Wi-Fi (`192.168.x.x`)

---

### Solução 2: Frontend usa IP da rede local

**Arquivo criado: `.env.local`**
```bash
# API URL para desenvolvimento na rede local
VITE_API_URL=http://192.168.3.117:5000
```

**O que faz:**
- Frontend agora aponta para o **IP da sua máquina na rede local**
- Todos os dispositivos na mesma Wi-Fi podem acessar esse IP

---

## 🧪 Como Testar

### 1. Reinicie o Backend

```powershell
# Parar o servidor atual (Ctrl+C no terminal)

# Iniciar novamente com a nova configuração
cd backend
python app.py
```

**Saída esperada:**
```
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:5000
* Running on http://192.168.3.117:5000  ← IP DA REDE LOCAL
```

### 2. Reinicie o Frontend

```powershell
# Em outro terminal
npm run dev
```

**Saída esperada:**
```
VITE v5.1.7  ready in 450 ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.3.117:5173/  ← COMPARTILHÁVEL
```

### 3. Teste na Sua Máquina

1. Abra: `http://localhost:5173`
2. Envie a planilha `Planilha Teste.csv`
3. ✅ Deve funcionar normalmente

### 4. Teste no Celular (mesma Wi-Fi)

1. **Conecte o celular na mesma rede Wi-Fi**
2. Abra o navegador do celular
3. Digite: `http://192.168.3.117:5173`
4. Envie uma planilha
5. ✅ **Deve funcionar!**

### 5. Teste em Outro Computador (mesma Wi-Fi)

1. Conecte na mesma rede Wi-Fi
2. Abra: `http://192.168.3.117:5173`
3. Envie uma planilha
4. ✅ **Deve funcionar!**

---

## 🔒 Segurança e Firewall

### Windows Firewall (Pode bloquear)

Se ainda não funcionar, o **Windows Firewall** pode estar bloqueando conexões externas.

**Solução Rápida (Desenvolvimento):**

```powershell
# Adicionar regra para permitir Python (Flask) na rede
New-NetFirewallRule -DisplayName "Python Flask Dev Server" `
  -Direction Inbound `
  -Program "C:\Path\To\Python\python.exe" `
  -Action Allow `
  -Profile Private
```

**Ou manualmente:**
1. Painel de Controle → Windows Defender Firewall
2. Configurações Avançadas
3. Regras de Entrada → Nova Regra
4. Tipo: Programa
5. Caminho: `python.exe` (onde está instalado)
6. Ação: Permitir conexão
7. Perfil: **Privado** (rede doméstica)

---

## 📱 URLs de Acesso

### Na Sua Máquina:
- ✅ `http://localhost:5173` (frontend)
- ✅ `http://localhost:5000` (backend)

### Em Outros Dispositivos (mesma Wi-Fi):
- ✅ `http://192.168.3.117:5173` (frontend)
- ✅ `http://192.168.3.117:5000` (backend - não precisa acessar diretamente)

---

## ⚠️ Observações Importantes

### 1. IP Pode Mudar

O IP `192.168.3.117` é **dinâmico** e pode mudar quando você:
- Reiniciar o roteador
- Reconectar ao Wi-Fi
- Reiniciar o computador

**Como descobrir o novo IP:**
```powershell
ipconfig | Select-String -Pattern "IPv4"
```

Procure pelo IP que começa com `192.168.x.x`

**Atualizar `.env.local`:**
```bash
VITE_API_URL=http://192.168.3.XXX:5000  # Novo IP
```

Reinicie o frontend (`npm run dev`) após mudar.

### 2. IP Fixo (Opcional)

Para evitar mudanças, você pode **configurar IP estático** no roteador:
1. Acesse o painel do roteador (`192.168.1.1` ou `192.168.0.1`)
2. Encontre "Reserva de IP" ou "DHCP Reservation"
3. Associe o MAC Address do seu PC ao IP `192.168.3.117`

### 3. Não Use em Produção

**ATENÇÃO:** `host='0.0.0.0'` é **SOMENTE para desenvolvimento local**.

**Para produção (Vercel):**
- Backend: Deploy serverless (sem `app.run()`)
- Frontend: Usa variável de ambiente `VITE_API_URL` configurada na Vercel Dashboard

---

## 🌐 Configuração para Produção (Vercel)

No deploy da Vercel, configure a variável de ambiente:

**Frontend (Vercel Dashboard):**
```
VITE_API_URL = https://alpha-1we53ew14-z4mbranos-projects.vercel.app
```

Assim o frontend em produção aponta para o backend em produção.

---

## 📝 Arquivos Modificados

1. **`backend/app.py`:**
   - Mudado `host='localhost'` → `host='0.0.0.0'`

2. **`.env.local`** (criado):
   - Configuração local com IP da rede

3. **`.gitignore`** (criado):
   - Ignora `.env.local` (não deve ser commitado)

---

## 🎯 Checklist

- [x] ✅ Backend configurado com `host='0.0.0.0'`
- [x] ✅ `.env.local` criado com IP local
- [x] ✅ `.gitignore` configurado
- [ ] ⏳ Backend reiniciado
- [ ] ⏳ Frontend reiniciado
- [ ] ⏳ Teste no celular
- [ ] ⏳ Teste em outro computador

---

## 🚀 Resumo

### Era:
```
Celular → http://localhost:5000 ❌ (aponta para o próprio celular)
```

### Agora é:
```
Celular → http://192.168.3.117:5000 ✅ (aponta para seu PC)
         ↓
    Backend (seu PC) aceita conexão ✅
         ↓
    Retorna resposta ✅
```

---

**Data da Correção:** 18 de outubro de 2025  
**Status:** ✅ Pronto para testar em outros dispositivos
