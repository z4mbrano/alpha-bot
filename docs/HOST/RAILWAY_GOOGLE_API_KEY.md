# 🔑 Adicionar Google API Key no Railway (DriveBot)

## ❌ Problema

O **DriveBot** não funciona porque o backend Railway não tem acesso à API do Google Drive.

Erro esperado nos logs:
```
Error: GOOGLE_API_KEY não configurada
```

## ✅ Solução

Adicionar a variável de ambiente `GOOGLE_API_KEY` no Railway.

---

## 📋 Passo a Passo

### 1. **Obter a Google API Key**

Você já deve ter essa chave configurada localmente em `backend/.env` ou `backend/service-account.json`.

**Opção A: Se usar API Key simples**
- Abra `backend/.env`
- Copie o valor de `GOOGLE_API_KEY`

**Opção B: Se usar Service Account (mais comum)**
- O DriveBot pode usar Service Account JSON
- Veja o arquivo `backend/service-account.json`

### 2. **Acessar Railway Dashboard**

1. Entre em: https://railway.app/
2. Clique no projeto: **alphainsights**
3. Clique no serviço: **alpha-bot** (o mesmo onde está rodando o backend)

### 3. **Adicionar Variável de Ambiente**

1. Na aba do serviço, clique em **"Variables"** no menu lateral
2. Clique em **"+ New Variable"**
3. Adicione:

#### Se usar API Key simples:
```
Variable: GOOGLE_API_KEY
Value: <sua-chave-aqui>
```

#### Se usar Service Account:
Você tem 2 opções:

**Opção 1: Base64 (Recomendado)**
```bash
# No seu terminal local:
cat backend/service-account.json | base64
```

Depois no Railway:
```
Variable: GOOGLE_SERVICE_ACCOUNT_BASE64
Value: <resultado-do-base64>
```

E modifique o código para decodificar:
```python
import base64
import json

service_account_b64 = os.getenv('GOOGLE_SERVICE_ACCOUNT_BASE64')
if service_account_b64:
    service_account_json = base64.b64decode(service_account_b64).decode('utf-8')
    credentials = json.loads(service_account_json)
```

**Opção 2: JSON completo (mais simples mas menos seguro)**
```
Variable: GOOGLE_SERVICE_ACCOUNT_JSON
Value: {"type":"service_account","project_id":"...","private_key_id":"..."}
```

### 4. **Salvar e Redeploy**

1. Clique em **"Add"** ou **"Save"**
2. O Railway vai automaticamente fazer **redeploy** do serviço
3. Aguarde 1-2 minutos

### 5. **Verificar Logs**

1. Clique na aba **"Deployments"**
2. Clique no deployment mais recente
3. Veja os logs em tempo real
4. Procure por: `✅ Google API configurada com sucesso`

---

## 🧪 Testar DriveBot

Após adicionar a variável:

1. Acesse: https://alpha-bot-six.vercel.app
2. Faça login
3. Troque para o bot **DriveBot** (ícone do Google Drive)
4. Envie uma mensagem de teste:
   ```
   Liste os arquivos da pasta raiz
   ```

Se funcionar, você verá uma resposta com a lista de arquivos do Drive! 🎉

---

## 🔍 Troubleshooting

### Erro: "GOOGLE_API_KEY não configurada"
- Verifique se adicionou a variável corretamente
- Certifique-se que o nome está **exatamente** como esperado pelo código
- Faça redeploy manualmente se necessário

### Erro: "Invalid credentials"
- Verifique se a chave não tem espaços extras
- Certifique-se que é a chave correta (teste localmente primeiro)
- Se usar Service Account, verifique o JSON completo

### DriveBot não responde
- Verifique logs do Railway: https://railway.app/project/<seu-projeto>/service/<seu-servico>/deployments
- Procure por erros relacionados ao Google API
- Teste o endpoint direto: `curl https://alphainsights.up.railway.app/api/health`

---

## 📝 Variáveis Atuais no Railway

Após adicionar, você deve ter no mínimo estas variáveis:

```env
GOOGLE_API_KEY=<sua-chave>              # ✅ NOVA - Necessária para DriveBot
FLASK_SECRET_KEY=<gerado-aleatório>     # ✅ Já existe
RAILWAY_VOLUME_MOUNT_PATH=/data         # ✅ Já existe (automático)
PORT=8080                                # ✅ Já existe (automático)
```

---

## ✨ Resultado Final

Após configurar:
- ✅ **AlphaBot**: Funciona (análise de planilhas)
- ✅ **DriveBot**: Funciona (Google Drive API)
- ✅ Backend Railway totalmente operacional
- ✅ Frontend Vercel conectado corretamente

---

**Status:** ⏳ Aguardando configuração da GOOGLE_API_KEY
