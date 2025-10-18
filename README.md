# 🤖 Alpha Insights — Plataforma de Análise Inteligente de Dados

[![Status](https://img.shields.io/badge/status-production-success)]()
[![Frontend](https://img.shields.io/badge/frontend-React%2018-blue)]()
[![Backend](https://img.shields.io/badge/backend-Flask%203.0-green)]()
[![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)]()

> Plataforma moderna de análise de dados com múltiplos bots especializados alimentados por IA, desenvolvida para a **Alpha Insights**, empresa de varejo de tecnologia.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#️-arquitetura)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#️-configuração)
- [Execução](#-execução)
- [Bots Disponíveis](#-bots-disponíveis)
- [API Endpoints](#-api-endpoints)
- [Testes](#-testes)
- [Deploy](#-deploy)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

---

## 🎯 Visão Geral

### O que é o Alpha Insights?

Alpha Insights é uma solução completa de análise de dados que combina:

✨ **Interface moderna e responsiva** construída com React + TypeScript  
🤖 **Múltiplos bots especializados** com IA (Google Gemini)  
📊 **Análise automatizada de planilhas** (CSV, XLSX)  
☁️ **Integração com Google Drive** para análise de pastas  
🌓 **Tema Dark/Light** com persistência local  
📱 **100% Responsivo** (Desktop, Tablet, Mobile)

### Features Principais

- **ALPHABOT**: Especialista em análise de planilhas anexadas
- **DRIVEBOT**: Analista autônomo para dados no Google Drive
- **Chat em tempo real** com indicadores de digitação
- **Upload múltiplo** de arquivos com validação
- **Histórico de conversas** por bot
- **API RESTful** segura e escalável

---

## 🏗️ Arquitetura

### Stack Tecnológico

#### Frontend
- **React 18** com TypeScript
- **Vite** como bundler ultrarrápido
- **Tailwind CSS** para estilização moderna
- **Lucide React** para ícones vetoriais
- **Context API** para gerenciamento de estado

#### Backend
- **Flask 3.0** como framework web
- **Google AI (Gemini)** para respostas inteligentes
- **Google Drive API** para acesso a arquivos
- **Pandas** para análise de dados
- **CORS** habilitado para comunicação segura

### Diagrama de Arquitetura

```
┌─────────────────┐
│   React App     │
│  (Port 5173)    │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐      ┌──────────────┐
│   Flask API     │◄────►│ Google AI    │
│  (Port 5000)    │      │  (Gemini)    │
└────────┬────────┘      └──────────────┘
         │
         ├──────► Google Drive API
         │
         └──────► Pandas (Análise)
```

---

## 📁 Estrutura do Projeto

```
alpha-bot/
├── src/                         # Frontend React
│   ├── components/              # Componentes React
│   │   ├── ChatArea.tsx         # Área principal de chat
│   │   ├── Sidebar.tsx          # Menu lateral
│   │   └── MessageBubble.tsx    # Bolha de mensagem
│   ├── contexts/                # Context API
│   │   ├── BotContext.tsx       # Estado dos bots
│   │   └── ThemeContext.tsx     # Tema dark/light
│   ├── App.tsx                  # Componente raiz
│   ├── main.tsx                 # Entry point
│   └── index.css                # Estilos globais + tokens
│
├── backend/                     # API Flask
│   ├── src/
│   │   ├── api/                 # Rotas/Endpoints
│   │   │   ├── alphabot.py      # Rotas do AlphaBot
│   │   │   └── drivebot.py      # Rotas do DriveBot
│   │   ├── services/            # Lógica de negócio
│   │   │   ├── ai_service.py    # Integração com Gemini
│   │   │   ├── drive_service.py # Google Drive
│   │   │   └── data_analyzer.py # Análise de dados
│   │   ├── models/              # Modelos de dados
│   │   │   ├── conversation.py
│   │   │   └── session.py
│   │   ├── utils/               # Utilitários
│   │   │   ├── file_handlers.py
│   │   │   ├── data_processors.py
│   │   │   └── validators.py
│   │   ├── prompts/             # Prompts de IA
│   │   │   ├── alphabot_prompt.py
│   │   │   └── drivebot_prompt.py
│   │   └── config/              # Configurações
│   │       └── settings.py
│   ├── tests/                   # Testes unitários
│   ├── app.py                   # Entry point
│   ├── requirements.txt
│   ├── service-account.json     # Credenciais Google (não versionado)
│   └── .env                     # Variáveis de ambiente (não versionado)
│
├── docs/                        # Documentação
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEPLOYMENT.md
│   ├── GOOGLE_DRIVE_SETUP.md
│   ├── FRAMEWORK-EXEMPLO.md
│   └── changelogs/
│       ├── DRIVEBOT_V5_CHANGELOG.md
│       ├── DRIVEBOT_V6_MEMORIA_CONVERSACIONAL.md
│       ├── DRIVEBOT_V7_MONOLOGO_ANALITICO.md
│       ├── DRIVEBOT_V10_MOTOR_AUTONOMO.md
│       └── DRIVEBOT_V11_ANALISTA_CONFIAVEL.md
│
├── scripts/                     # Scripts de automação
│   ├── test-alphabot.ps1
│   ├── test-drivebot-v3.ps1
│   ├── test-drivebot-v4.ps1
│   └── test-drivebot.ps1
│
├── assets/                      # Recursos estáticos
│   └── images/
│       ├── alpha-icon.png
│       └── preview.png
│
├── index.html                   # HTML raiz
├── package.json                 # Dependências Node
├── vite.config.ts               # Config Vite
├── tailwind.config.cjs          # Config Tailwind
├── tsconfig.json                # Config TypeScript
├── postcss.config.cjs           # Config PostCSS
├── README.md                    # Este arquivo
└── .gitignore
```

---

## 🔧 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

### Obrigatórios
- **Node.js** 18+ e **npm** 9+
- **Python** 3.10+
- **Git**

### Opcional
- **Google Cloud Account** (para DriveBot)
- **Conta Google AI Studio** (para APIs Gemini)

---

## 💿 Instalação

### 1. Clone o Repositório

```bash
git clone https://github.com/z4mbrano/alpha-bot.git
cd alpha-bot
```

### 2. Configure o Frontend

```bash
# Instalar dependências
npm install
```

### 3. Configure o Backend

```bash
# Navegar para o backend
cd backend

# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar o ambiente virtual
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Linux/Mac
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na pasta `backend/`:

```env
# API Keys do Google AI Studio
DRIVEBOT_API_KEY=sua_chave_drivebot_aqui
ALPHABOT_API_KEY=sua_chave_alphabot_aqui

# Google Service Account (para DriveBot)
GOOGLE_SERVICE_ACCOUNT_FILE=service-account.json
# OU
GOOGLE_SERVICE_ACCOUNT_INFO={"type":"service_account",...}
```

### 2. Google Service Account (DriveBot)

Para usar o DriveBot, você precisa de uma Service Account do Google Cloud:

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative as APIs: **Google Drive API** e **Google Sheets API**
4. Crie uma **Service Account**
5. Gere e baixe o arquivo JSON de credenciais
6. Salve como `backend/service-account.json`
7. **Importante**: Compartilhe suas pastas do Drive com o email da Service Account

> 📚 Veja o guia detalhado: [docs/GOOGLE_DRIVE_SETUP.md](docs/GOOGLE_DRIVE_SETUP.md)

### 3. API Keys do Gemini

1. Acesse [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Crie duas chaves separadas (uma para cada bot)
3. Adicione-as no `.env` conforme acima

---

## 🚀 Execução

### Modo Desenvolvimento

**Terminal 1 - Frontend:**
```bash
npm run dev
```
✅ Acesse: http://localhost:5173

**Terminal 2 - Backend:**
```bash
cd backend
python app.py
```
✅ API: http://localhost:5000

### Modo Produção

**Build do Frontend:**
```bash
npm run build
```

**Deploy do Backend:**
```bash
# Exemplo com Gunicorn
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🤖 Bots Disponíveis

### ALPHABOT 📊
**Especialista em Análise de Planilhas Anexadas**

- ✅ Upload de múltiplos arquivos (CSV, XLSX)
- ✅ Detecção automática de tipos de dados
- ✅ Motor de validação interna (Analista → Crítico → Júri)
- ✅ Análise contextual e insights

**Fluxo:**
1. Clique no botão de anexo 📎
2. Selecione um ou mais arquivos `.csv` ou `.xlsx`
3. Envie e aguarde o diagnóstico
4. Faça perguntas sobre os dados

### DRIVEBOT 💎
**Analista Autônomo para Google Drive**

- ✅ Acesso seguro via Service Account
- ✅ Leitura de múltiplos arquivos em pastas
- ✅ Consolidação automática de dados
- ✅ Kernel de dados persistente por conversa

**Fluxo:**
1. Cole o ID ou URL de uma pasta do Google Drive
2. Aguarde a indexação e relatório inicial
3. Explore dados com perguntas em linguagem natural

---

## 📡 API Endpoints

### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "ok",
  "service": "Alpha Insights API"
}
```

### Chat - DriveBot
```http
POST /api/chat
Content-Type: application/json

{
  "bot_id": "drivebot",
  "message": "Cole o link da pasta do Drive",
  "conversation_id": "uuid-opcional"
}
```

### Upload - AlphaBot
```http
POST /api/alphabot/upload
Content-Type: multipart/form-data

files: [file1.csv, file2.xlsx]
```

**Response:**
```json
{
  "session_id": "abc123",
  "metadata": {
    "files_success": ["vendas.csv"],
    "total_records": 1500,
    "columns": ["Produto", "Preco_Unitario", ...]
  }
}
```

### Chat - AlphaBot
```http
POST /api/alphabot/chat
Content-Type: application/json

{
  "session_id": "abc123",
  "message": "Liste os 5 produtos mais vendidos"
}
```

> 📚 Documentação completa da API: [docs/API.md](docs/API.md)

---

## 🧪 Testes

### Frontend
```bash
# (Testes a serem implementados)
npm test
```

### Backend

**Testes Automáticos:**
```bash
cd backend
python test_alphabot.py
python validate_v11.py
```

**Scripts de Teste Manuais (PowerShell):**
```powershell
# Testar AlphaBot
.\scripts\test-alphabot.ps1

# Testar DriveBot
.\scripts\test-drivebot.ps1
.\scripts\test-drivebot-v4.ps1
```

---

## 📦 Deploy

### Frontend (Vercel/Netlify)

```bash
# Build
npm run build

# Deploy
# Os arquivos estarão em dist/
```

### Backend (Heroku/Railway/Render)

**Procfile:**
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

**Runtime:**
```
python-3.11.9
```

> 📚 Guia completo: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'Adiciona nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

### Diretrizes

- Siga os padrões de código existentes
- Escreva testes para novas funcionalidades
- Atualize a documentação conforme necessário
- Mantenha commits atômicos e descritivos

---

## 📄 Licença

Este projeto é proprietário da **Alpha Insights**. Todos os direitos reservados.

---

## 👨‍💻 Autores

- **Guilherme Zambrano** - [@z4mbrano](https://github.com/z4mbrano)
- **Alpha Insights Team** - Desenvolvimento e manutenção

---

## 📞 Suporte

Para suporte ou dúvidas:
- 📧 Email: suporte@alphainsights.com
- 📝 Issues: [GitHub Issues](https://github.com/z4mbrano/alpha-bot/issues)
- 📚 Docs: [Documentação Completa](docs/)

---

## 🗺️ Roadmap

### Em Desenvolvimento
- [ ] Refatoração backend (clean architecture)
- [ ] Testes automatizados completos
- [ ] Documentação API OpenAPI/Swagger

### Planejado
- [ ] Autenticação de usuários
- [ ] Dashboard de analytics
- [ ] Export de relatórios (PDF/Excel)
- [ ] Novos bots especializados
- [ ] Mobile app (React Native)

---

## 📈 Changelog

Veja todas as mudanças em: [docs/changelogs/](docs/changelogs/)

**Últimas versões:**
- **v2.0.0** - Reestruturação completa do código
- **v1.1.0** - DriveBot v11 com motor autônomo
- **v1.0.0** - Lançamento inicial

---

<div align="center">

**Feito com ❤️ pela equipe Alpha Insights**

[⬆ Voltar ao topo](#-alpha-insights--plataforma-de-análise-inteligente-de-dados)

</div>
