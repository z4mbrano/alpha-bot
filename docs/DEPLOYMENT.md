# Deployment Guide

Guia completo para fazer deploy do Alpha Bot em produção.

## Índice

- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Deploy do Backend](#deploy-do-backend)
  - [Heroku](#heroku)
  - [Railway](#railway)
  - [Render](#render)
  - [Docker](#docker)
  - [VPS (Ubuntu)](#vps-ubuntu)
- [Deploy do Frontend](#deploy-do-frontend)
  - [Vercel](#vercel)
  - [Netlify](#netlify)
- [Configurações Pós-Deploy](#configurações-pós-deploy)
- [Monitoramento](#monitoramento)
- [Troubleshooting](#troubleshooting)

---

## Visão Geral

O Alpha Bot é composto por duas partes:
1. **Backend** (Flask + Python) - API REST
2. **Frontend** (React + TypeScript + Vite) - Interface do usuário

Cada parte pode ser deployada independentemente em diferentes plataformas.

---

## Pré-requisitos

### Backend
- Python 3.10 ou superior
- Conta no Google Cloud (para Service Account do Drive)
- API Keys do Google Gemini (DriveBot e AlphaBot)

### Frontend
- Node.js 18+ e npm
- URL do backend deployado

### Google Cloud Setup

1. Criar projeto no [Google Cloud Console](https://console.cloud.google.com)
2. Ativar APIs:
   - Google Drive API
   - Google Sheets API
3. Criar Service Account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Gerar chave JSON
   - Compartilhar pastas do Drive com o email da Service Account

---

## Variáveis de Ambiente

### Backend (.env)

```env
# Google AI (Gemini)
DRIVEBOT_API_KEY=your_gemini_api_key_for_drivebot
ALPHABOT_API_KEY=your_gemini_api_key_for_alphabot

# Google Drive Service Account (escolha uma opção)
# Opção 1: Caminho para arquivo JSON
GOOGLE_SERVICE_ACCOUNT_FILE=./service-account.json

# Opção 2: JSON como string (recomendado para Heroku/Railway)
GOOGLE_SERVICE_ACCOUNT_INFO='{"type":"service_account","project_id":"..."}'

# Flask
FLASK_ENV=production
PORT=5000
```

### Frontend (.env)

```env
VITE_API_URL=https://your-backend-url.com
```

---

## Deploy do Backend

### Heroku

#### 1. Instalar Heroku CLI
```bash
# Windows (Chocolatey)
choco install heroku-cli

# Mac
brew tap heroku/brew && brew install heroku

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

#### 2. Login e Criar App
```bash
heroku login
cd backend
heroku create alpha-bot-backend
```

#### 3. Configurar Variáveis de Ambiente
```bash
heroku config:set DRIVEBOT_API_KEY="your_key"
heroku config:set ALPHABOT_API_KEY="your_key"
heroku config:set GOOGLE_SERVICE_ACCOUNT_INFO='{"type":"service_account",...}'
heroku config:set FLASK_ENV=production
```

#### 4. Criar Procfile
```
web: gunicorn app:app
```

#### 5. Atualizar requirements.txt
```txt
gunicorn==21.2.0
```

#### 6. Deploy
```bash
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main
```

#### 7. Verificar
```bash
heroku logs --tail
heroku open
```

---

### Railway

#### 1. Criar Conta
- Acesse [railway.app](https://railway.app)
- Login com GitHub

#### 2. Deploy via GitHub
- New Project → Deploy from GitHub repo
- Selecionar repositório `alpha-bot`
- Railway detectará automaticamente Python

#### 3. Configurar Variáveis de Ambiente
- Settings → Variables
- Adicionar todas as variáveis do `.env`

#### 4. Configurar Start Command
- Settings → Deploy
- Start Command: `gunicorn app:app`

#### 5. Configurar Root Directory
- Settings → Deploy
- Root Directory: `/backend`

#### 6. Deploy
- Railway fará deploy automaticamente
- Obter URL em Settings → Domains

---

### Render

#### 1. Criar Conta
- Acesse [render.com](https://render.com)
- Login com GitHub

#### 2. New Web Service
- Dashboard → New → Web Service
- Conectar repositório GitHub

#### 3. Configurar Serviço
```yaml
Name: alpha-bot-backend
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Root Directory: backend
```

#### 4. Configurar Variáveis de Ambiente
- Environment → Environment Variables
- Adicionar todas as variáveis

#### 5. Deploy
- Render fará deploy automaticamente
- URL disponível após conclusão

---

### Docker

#### 1. Criar Dockerfile (backend/)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 5000

# Comando de inicialização
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

#### 2. Criar .dockerignore (backend/)
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.git/
.vscode/
```

#### 3. Build e Run
```bash
cd backend

# Build
docker build -t alpha-bot-backend .

# Run com variáveis de ambiente
docker run -d \
  -p 5000:5000 \
  -e DRIVEBOT_API_KEY="your_key" \
  -e ALPHABOT_API_KEY="your_key" \
  -e GOOGLE_SERVICE_ACCOUNT_INFO='{"type":"service_account",...}' \
  -e FLASK_ENV=production \
  --name alpha-bot \
  alpha-bot-backend
```

#### 4. Docker Compose (opcional)
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - DRIVEBOT_API_KEY=${DRIVEBOT_API_KEY}
      - ALPHABOT_API_KEY=${ALPHABOT_API_KEY}
      - GOOGLE_SERVICE_ACCOUNT_INFO=${GOOGLE_SERVICE_ACCOUNT_INFO}
      - FLASK_ENV=production
    restart: unless-stopped
```

---

### VPS (Ubuntu)

#### 1. Configurar Servidor
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e pip
sudo apt install python3.11 python3.11-venv python3-pip -y

# Instalar Nginx
sudo apt install nginx -y

# Instalar Supervisor (gerenciador de processos)
sudo apt install supervisor -y
```

#### 2. Clonar Repositório
```bash
cd /opt
sudo git clone https://github.com/z4mbrano/alpha-bot.git
cd alpha-bot/backend
```

#### 3. Criar Virtual Environment
```bash
sudo python3.11 -m venv venv
sudo venv/bin/pip install -r requirements.txt
sudo venv/bin/pip install gunicorn
```

#### 4. Criar Arquivo .env
```bash
sudo nano /opt/alpha-bot/backend/.env
# Adicionar variáveis de ambiente
```

#### 5. Configurar Supervisor
```bash
sudo nano /etc/supervisor/conf.d/alpha-bot.conf
```

```ini
[program:alpha-bot]
directory=/opt/alpha-bot/backend
command=/opt/alpha-bot/backend/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 app:app
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/alpha-bot/error.log
stdout_logfile=/var/log/alpha-bot/access.log
environment=PATH="/opt/alpha-bot/backend/venv/bin"
```

```bash
# Criar diretório de logs
sudo mkdir -p /var/log/alpha-bot
sudo chown www-data:www-data /var/log/alpha-bot

# Reiniciar Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start alpha-bot
```

#### 6. Configurar Nginx
```bash
sudo nano /etc/nginx/sites-available/alpha-bot
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/alpha-bot/backend/static;
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/alpha-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 7. Configurar HTTPS com Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

---

## Deploy do Frontend

### Vercel

#### 1. Instalar Vercel CLI
```bash
npm install -g vercel
```

#### 2. Login e Deploy
```bash
cd alpha-bot
vercel login
vercel
```

#### 3. Configurar Variáveis de Ambiente
- Dashboard Vercel → Settings → Environment Variables
- Adicionar `VITE_API_URL=https://your-backend-url.com`

#### 4. Redeploy
```bash
vercel --prod
```

---

### Netlify

#### 1. Build do Projeto
```bash
npm run build
```

#### 2. Deploy via Netlify CLI
```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod --dir=dist
```

#### 3. Configurar Variáveis de Ambiente
- Dashboard Netlify → Site settings → Environment variables
- Adicionar `VITE_API_URL`

#### 4. Criar netlify.toml
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

## Configurações Pós-Deploy

### 1. Atualizar CORS no Backend
```python
# backend/app.py
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://your-frontend-url.vercel.app",
            "https://your-frontend-url.netlify.app"
        ],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
```

### 2. Testar Health Check
```bash
curl https://your-backend-url.com/api/health
```

### 3. Testar Upload (AlphaBot)
```bash
curl -X POST https://your-backend-url.com/api/alphabot/upload \
  -F "files=@test.csv"
```

### 4. Testar Chat (DriveBot)
```bash
curl -X POST https://your-backend-url.com/api/drivebot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "your_drive_folder_id"}'
```

---

## Monitoramento

### Logs

#### Heroku
```bash
heroku logs --tail
```

#### Railway
- Dashboard → Deployments → Logs

#### Render
- Dashboard → Logs

#### VPS
```bash
sudo tail -f /var/log/alpha-bot/error.log
sudo tail -f /var/log/alpha-bot/access.log
```

### Uptime Monitoring

Considere usar:
- [UptimeRobot](https://uptimerobot.com) (gratuito)
- [Pingdom](https://pingdom.com)
- [Better Uptime](https://betteruptime.com)

---

## Troubleshooting

### Erro: "Module not found"
```bash
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

### Erro: "Port already in use"
```bash
# Matar processo na porta 5000
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux
sudo lsof -i :5000
sudo kill -9 <PID>
```

### Erro: "Google Drive API not enabled"
- Google Cloud Console → APIs & Services → Library
- Buscar "Google Drive API" e ativar
- Buscar "Google Sheets API" e ativar

### Erro: "Service Account not found"
- Verificar se `GOOGLE_SERVICE_ACCOUNT_INFO` está configurado
- Validar JSON:
```bash
python -c "import json; print(json.loads('''$GOOGLE_SERVICE_ACCOUNT_INFO'''))"
```

### Erro: CORS
- Verificar se frontend URL está em `CORS(app, resources=...)`
- Testar com Postman/cURL primeiro (ignora CORS)

---

## Segurança

### Recomendações para Produção

1. **Rate Limiting**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

2. **API Key Authentication**
```python
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY'):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/alphabot/upload', methods=['POST'])
@require_api_key
def upload():
    ...
```

3. **HTTPS Only**
```python
from flask_talisman import Talisman

Talisman(app, force_https=True)
```

4. **Secrets Management**
- Usar AWS Secrets Manager
- Usar Azure Key Vault
- Usar Google Secret Manager

---

## Custos Estimados

### Opção 1: Heroku + Vercel
- **Backend (Heroku Eco):** $5/mês
- **Frontend (Vercel Pro):** Gratuito (hobby) ou $20/mês (pro)
- **Total:** $5-25/mês

### Opção 2: Railway
- **Backend + Frontend:** $5-10/mês (pay-as-you-go)
- Inclui 500 horas gratuitas/mês

### Opção 3: VPS (Digital Ocean/Linode)
- **Droplet básico:** $5-12/mês
- Controle total, requer manutenção

### Opção 4: Google Cloud Run
- **Backend (Cloud Run):** Pay-per-request (~$0-20/mês)
- **Frontend (Firebase Hosting):** Gratuito
- **Total:** $0-20/mês

---

## Checklist de Deploy

- [ ] Variáveis de ambiente configuradas
- [ ] Service Account do Google Drive funcionando
- [ ] API Keys do Gemini válidas
- [ ] CORS configurado corretamente
- [ ] Frontend aponta para backend correto
- [ ] Health check respondendo
- [ ] Upload de arquivos funcionando
- [ ] Chat AlphaBot funcionando
- [ ] Chat DriveBot funcionando
- [ ] HTTPS configurado (SSL)
- [ ] Logs configurados
- [ ] Monitoring ativo
- [ ] Backup de dados (se houver persistência)

---

**Última atualização:** Outubro 2025
