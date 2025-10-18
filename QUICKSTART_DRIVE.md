# 🚀 GUIA RÁPIDO: Configurar Google Drive

## ⚠️ PROBLEMA ATUAL
```
Erro: Credenciais não configuradas
```

## ✅ SOLUÇÃO RÁPIDA

### Passo 1: Localize o Arquivo JSON
Você já tem o Service Account com email:
```
id-spreadsheet-reader-robot@data-analytics-gc-475218.iam.gserviceaccount.com
```

Você deve ter baixado um arquivo JSON quando criou este Service Account.
O arquivo tem um nome parecido com:
```
data-analytics-gc-475218-a1b2c3d4e5f6.json
```

### Passo 2: Copie o Arquivo para a Pasta Backend
```powershell
# No PowerShell, vá para a pasta do projeto
cd C:\Users\vrd\Documents\GitHub\alpha-bot\backend

# Cole o arquivo JSON aqui e renomeie para service-account.json
# (ou mantenha o nome original e ajuste o .env)
```

### Passo 3: Verifique o .env
O arquivo `backend/.env` já está configurado com:
```env
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
```

Se você usar outro nome para o arquivo, ajuste esta linha.

### Passo 4: Reinicie o Backend
```powershell
# Pare o servidor (CTRL+C no terminal onde está rodando)
# Inicie novamente:
python app.py
```

---

## 🔍 ONDE ENCONTRAR O ARQUIVO JSON?

### Se você ainda não tem o arquivo:

1. Acesse: https://console.cloud.google.com/
2. Selecione o projeto: `data-analytics-gc-475218`
3. Vá em: **IAM & Admin > Service Accounts**
4. Encontre: `id-spreadsheet-reader-robot`
5. Clique nos **3 pontinhos** → **Manage Keys**
6. Clique em **Add Key > Create new key**
7. Escolha **JSON** e clique em **Create**
8. O arquivo será baixado automaticamente

---

## ✅ CHECKLIST COMPLETO

- [ ] Arquivo JSON baixado do Google Cloud
- [ ] Arquivo copiado para `C:\Users\vrd\Documents\GitHub\alpha-bot\backend\`
- [ ] Arquivo renomeado para `service-account.json` (ou ajustado no .env)
- [ ] `.env` configurado com `GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json`
- [ ] Pasta do Drive compartilhada com `id-spreadsheet-reader-robot@...` como Viewer
- [ ] Backend reiniciado

---

## 🧪 TESTE RÁPIDO

Depois de configurar, teste no PowerShell:

```powershell
cd C:\Users\vrd\Documents\GitHub\alpha-bot\backend

# Teste 1: Verificar se o arquivo existe
Test-Path service-account.json

# Teste 2: Verificar se consegue carregar as credenciais
python -c "from app import get_google_credentials; print(get_google_credentials())"
```

Se tudo estiver correto, você verá:
```
<google.oauth2.service_account.Credentials object at 0x...>
```

---

## ❌ SE NÃO FUNCIONAR

Execute este comando para ver o erro completo:
```powershell
python -c "from app import get_google_credentials; get_google_credentials()"
```

E me envie a mensagem de erro.
