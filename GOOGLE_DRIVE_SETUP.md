# DriveBot - Configuração da Integração com Google Drive

## 🔧 Configuração do Google Service Account

Para que o DriveBot possa ler arquivos do Google Drive, você precisa configurar um Service Account:

### 1. Criar Service Account no Google Cloud

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Vá em **IAM & Admin > Service Accounts**
4. Clique em **Create Service Account**
5. Preencha os dados:
   - Nome: `drivebot-service`
   - Descrição: `Service account para DriveBot ler dados do Drive`
6. Clique em **Create and Continue**
7. Pule as permissões (não precisa de roles) e clique em **Done**

### 2. Criar chave JSON

1. Na lista de Service Accounts, clique no account que você criou
2. Vá na aba **Keys**
3. Clique em **Add Key > Create new key**
4. Selecione **JSON** e clique em **Create**
5. O arquivo JSON será baixado automaticamente
6. Salve este arquivo em local seguro (ex: `backend/service-account.json`)
7. **IMPORTANTE**: Adicione este arquivo no `.gitignore` para não commitá-lo

### 3. Habilitar APIs

1. No Cloud Console, vá em **APIs & Services > Library**
2. Procure e habilite:
   - **Google Drive API**
   - **Google Sheets API**

### 4. Compartilhar pasta do Drive

1. Abra a pasta do Google Drive que contém suas planilhas
2. Clique em **Compartilhar**
3. Cole o email do Service Account (está no arquivo JSON, campo `client_email`)
   - Exemplo: `drivebot-service@seu-projeto.iam.gserviceaccount.com`
4. Dê permissão de **Viewer** (leitura)
5. Copie o ID da pasta da URL:
   - URL: `https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j`
   - ID: `1a2b3c4d5e6f7g8h9i0j`

### 5. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure:

```env
# API Keys do Google AI (Gemini)
DRIVEBOT_API_KEY=AIza...
ALPHABOT_API_KEY=AIza...

# Caminho para o arquivo JSON do Service Account
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
```

## 📊 Formatos de arquivo suportados

O DriveBot pode ler os seguintes formatos:

- **CSV** (.csv) - Delimitado por vírgula ou ponto-e-vírgula
- **Excel** (.xlsx, .xls) - Todas as abas
- **Google Sheets** - Planilhas nativas do Google Drive

## 🎯 Como usar

1. Inicie o backend:
   ```bash
   cd backend
   python app.py
   ```

2. Inicie o frontend:
   ```bash
   npm run dev
   ```

3. No chat do DriveBot, forneça o ID da pasta:
   ```
   Usuário: Analise a pasta 1a2b3c4d5e6f7g8h9i0j
   ```

4. O DriveBot irá:
   - Ler todos os arquivos da pasta
   - Detectar colunas numéricas, de data e texto
   - Gerar um relatório de descoberta
   - Responder perguntas sobre os dados REAIS

## 🔍 Detecção de dados

O DriveBot detecta automaticamente:

- **Colunas numéricas**: valores monetários (R$), porcentagens (%), números
- **Colunas de data**: datas em português (janeiro, fev, mar, etc.)
- **Colunas de texto**: dimensões categóricas (região, produto, cliente, etc.)
- **Formato brasileiro**: vírgula como decimal (1.234,56)

## ⚠️ Importante

- ❌ **NÃO commite** o arquivo `service-account.json` no Git
- ✅ Sempre adicione credenciais no `.gitignore`
- ✅ Use variáveis de ambiente para configuração
- ✅ Compartilhe apenas as pastas necessárias com o Service Account
- ✅ Dê apenas permissão de **Viewer** (leitura)

## 🐛 Troubleshooting

### Erro: "Failed to load credentials"

- Verifique se o arquivo `service-account.json` existe
- Verifique se o caminho está correto no `.env`
- Verifique se o JSON é válido

### Erro: "Access denied" ou "404 Not Found"

- Verifique se a pasta foi compartilhada com o email do Service Account
- Verifique se o ID da pasta está correto
- Verifique se as APIs do Drive e Sheets estão habilitadas

### DriveBot retorna dados simulados

- Verifique se você forneceu o ID da pasta
- Verifique os logs do backend para erros
- Teste a conexão com: `python -c "from app import get_google_credentials; print(get_google_credentials())"`
