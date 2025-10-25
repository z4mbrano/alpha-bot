# 🤖 Alpha Insights — Plataforma de Análise Inteligente de Dados

[![Status](https://img.shields.io/badge/status-production-success)]()
[![Frontend](https://img.shields.io/badge/frontend-React%2018-61dafb?logo=react)]()
[![Backend](https://img.shields.io/badge/backend-Flask%203.0-000000?logo=flask)]()
[![AI](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6?logo=typescript)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

> Plataforma moderna de análise de dados com múltiplos bots especializados alimentados por IA, desenvolvida para transformar dados empresariais em insights acionáveis através de conversação natural.

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Features](#-features)
- [Arquitetura](#️-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#️-configuração)
- [Execução](#-execução)
- [Bots Disponíveis](#-bots-disponíveis)
- [API Reference](#-api-reference)
- [Deploy](#-deploy)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Contribuição](#-contribuição)
- [Licença](#-licença)

---

## 🎯 Visão Geral

**Alpha Insights** é uma solução completa de análise de dados empresariais que combina interface intuitiva com inteligência artificial avançada. A plataforma permite que usuários não-técnicos extraiam insights complexos de planilhas e dados no Google Drive através de conversação natural.

### Por que Alpha Insights?

- ⚡ **Análise instantânea** de milhares de registros
- 🧠 **IA Multimodal** com Google Gemini 2.5 Flash
- 📊 **Visualizações automáticas** de dados
- 🔐 **Multi-tenant** com isolamento por usuário
- 🌍 **Deploy em produção** (Vercel + Railway)

---

## ✨ Features

### 🤖 Bots Especializados

#### **ALPHABOT** - Analista de Planilhas
- 📎 Upload de múltiplos arquivos (CSV, XLSX)
- 🔍 Detecção automática de colunas (numéricas, categóricas, temporais)
- 📈 Cálculos determinísticos (faturamento, totais, médias)
- 📊 Respostas estruturadas com tabelas Markdown
- 💾 Histórico de conversas persistente

#### **DRIVEBOT** - Analista Autônomo Google Drive
- ☁️ Integração nativa com Google Drive API
- 📁 Análise de pastas completas
- 🔄 Sincronização automática de dados
- 🎯 Motor de validação com 3 personas (Analista → Crítico → Júri)
- 📉 Gráficos interativos automáticos

### 🎨 Interface & UX

- 🌓 **Dark/Light Mode** com persistência
- 📱 **Totalmente Responsivo** (mobile-first)
- ⚡ **Indicadores em tempo real** (typing, loading)
- 💬 **Chat fluido** com scroll automático
- 🎯 **Navegação intuitiva** entre bots

### 🔒 Segurança & Performance

- 🔐 Autenticação JWT
- 🏢 Isolamento multi-tenant
- 📦 Cache inteligente de dados
- ⚙️ Rate limiting
- 🛡️ Validação de entrada robusta

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   AlphaBot   │  │   DriveBot   │  │     Auth     │     │
│  │   Upload     │  │   Drive API  │  │    Login     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Flask)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Blueprints: /alphabot, /drivebot, /auth        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ AI Service   │  │ Data Process │  │   Database   │     │
│  │ (Gemini 2.5) │  │   (Pandas)   │  │   (SQLite)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
                  Google Cloud APIs
              (Gemini AI + Drive API)
```

### Stack Tecnológico

**Frontend:**
- ⚛️ React 18 + TypeScript
- 🎨 Tailwind CSS 3.4
- ⚡ Vite 5
- 📊 Recharts (gráficos)
- 🎭 Zustand (state)
- 📝 React Markdown

**Backend:**
- 🐍 Python 3.11
- 🌶️ Flask 3.0
- 🤖 Google Generative AI SDK
- 🗄️ SQLite
- 🐼 Pandas (processamento de dados)

**DevOps:**
- 🚀 Vercel (frontend)
- 🚂 Railway (backend)
- 🐳 Docker
- 🔄 GitHub Actions (CI/CD)

---

## 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Node.js** 18+ ([Download](https://nodejs.org/))
- **Python** 3.11+ ([Download](https://www.python.org/))
- **Git** ([Download](https://git-scm.com/))
- **Conta Google Cloud** (para Gemini API)
- **Conta Google** (para Drive API - opcional)

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/z4mbrano/alpha-bot.git
cd alpha-bot
```

### 2. Configurar Frontend

```bash
# Instalar dependências
npm install

# ou com yarn
yarn install
```

### 3. Configurar Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

---

## ⚙️ Configuração

### Frontend (.env)

Crie um arquivo `.env` na raiz do projeto:

```env
# API Backend URL
VITE_API_URL=http://localhost:5000

# Analytics (opcional)
VITE_VERCEL_ANALYTICS_ID=seu_analytics_id
```

### Backend (.env)

Crie um arquivo `.env` em `backend/`:

```env
# Google Gemini API
GOOGLE_API_KEY=sua_chave_api_gemini

# Google Drive API (opcional - só para DriveBot)
GOOGLE_DRIVE_CREDENTIALS_PATH=./service-account.json

# Flask Config
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=sua_chave_secreta_aqui

# Database
DATABASE_PATH=./alphabot.db

# CORS (permitir frontend local)
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Obter Google Gemini API Key

1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Clique em "Create API Key"
3. Copie a chave e cole em `GOOGLE_API_KEY`

### Configurar Google Drive (Opcional)

Para usar o DriveBot:

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto
3. Ative a Google Drive API
4. Crie credenciais de Service Account
5. Baixe o JSON e salve como `backend/service-account.json`

---

## ▶️ Execução

### Desenvolvimento Local

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
# Servidor rodando em http://localhost:5000
```

**Terminal 2 - Frontend:**
```bash
npm run dev
# Aplicação em http://localhost:5173
```

### Acessar Aplicação

Abra [http://localhost:5173](http://localhost:5173) no navegador.

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin123`

---

## 🤖 Bots Disponíveis

### ALPHABOT - Analista de Planilhas

**Capacidades:**
- ✅ Upload de até 10 arquivos simultâneos
- ✅ Suporta CSV, XLSX, XLS, ODS, TSV
- ✅ Detecção inteligente de tipos de dados
- ✅ Cálculos financeiros precisos (R$ formatado)
- ✅ Análises temporais (mensal, trimestral, anual)
- ✅ Comparações por categoria/região

**Exemplo de uso:**
```
Usuário: "Qual foi a fatura total de 2024?"

AlphaBot:
## 🎯 OBJETIVO
Informar a fatura total do ano de 2024 e comparar a fatura total dos 12 meses.

## 📊 EXECUÇÃO E RESULTADO
A fatura total para o ano de 2024 foi calculada como R$ 11.384.047,18.

| Mês       | Fatura Mensal (R$) |
|-----------|-------------------:|
| Janeiro   |      1.084.997,91 |
| Fevereiro |        990.121,09 |
| ...       |               ... |
| **TOTAL** | **11.384.047,18** |

## 💡 INSIGHT
Novembro apresentou a maior fatura (R$ 1.363.655,41) enquanto 
Setembro registrou a menor (R$ 712.578,67).
```

**Perguntas que o AlphaBot responde:**
- "Compare as vendas por região"
- "Mostre a evolução das vendas ao longo do tempo"
- "Qual produto teve maior faturamento?"
- "Qual foi a média de vendas por mês?"

### DRIVEBOT - Analista Google Drive

**Capacidades:**
- ✅ Análise de pastas completas no Drive
- ✅ Consolidação automática de múltiplos arquivos
- ✅ Motor de validação em 3 etapas
- ✅ Geração automática de gráficos
- ✅ Insights contextualizados

**Exemplo de uso:**
```
Usuário: "Analise as vendas por região na pasta 'Dados 2024'"

DriveBot: [Acessa Drive → Consolida dados → Gera análise]
```

---

## 📡 API Reference

### Autenticação

#### POST `/api/login`
Login de usuário.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "message": "Login bem-sucedido",
  "user": {
    "id": 1,
    "username": "admin"
  }
}
```

### AlphaBot

#### POST `/api/alphabot/upload`
Upload de arquivos para análise.

**Request (FormData):**
- `files`: File[] (múltiplos arquivos)
- `user_id`: number
- `conversation_id`: string (opcional)

**Response:**
```json
{
  "status": "success",
  "session_id": "abc-123",
  "conversation_id": "def-456",
  "metadata": {
    "total_records": 3029,
    "total_columns": 20,
    "columns": ["ID_Transacao", "Produto", ...],
    "date_columns": ["Data"],
    "files_success": ["DADOS_JANUARY.CSV", ...]
  }
}
```

#### POST `/api/alphabot/chat`
Enviar mensagem para análise.

**Request:**
```json
{
  "session_id": "abc-123",
  "conversation_id": "def-456",
  "user_id": 1,
  "message": "Qual foi a fatura de 2024?"
}
```

**Response:**
```json
{
  "answer": "## 🎯 OBJETIVO\n...",
  "metadata": {
    "records_analyzed": 3029,
    "computation_method": "deterministic"
  }
}
```

### DriveBot

#### POST `/api/drivebot/chat`
Análise de dados no Google Drive.

**Request:**
```json
{
  "user_id": 1,
  "conversation_id": "xyz-789",
  "message": "Analise a pasta 'Vendas 2024'"
}
```

### Conversas

#### GET `/api/conversations?user_id=1`
Listar conversas do usuário.

#### GET `/api/conversation/{id}/messages`
Obter mensagens de uma conversa.

---

## 🚀 Deploy

### Frontend (Vercel)

1. Conecte seu repositório no [Vercel](https://vercel.com)
2. Configure variáveis de ambiente:
   ```
   VITE_API_URL=https://seu-backend.railway.app
   ```
3. Deploy automático a cada push

### Backend (Railway)

1. Conecte seu repositório no [Railway](https://railway.app)
2. Configure variáveis:
   ```
   GOOGLE_API_KEY=...
   ALLOWED_ORIGINS=https://seu-frontend.vercel.app
   ```
3. Railway detecta automaticamente Flask

### Docker (Alternativo)

```bash
# Build
docker build -t alpha-insights .

# Run
docker run -p 5000:5000 -p 5173:5173 \
  -e GOOGLE_API_KEY=... \
  alpha-insights
```

---

## 📁 Estrutura do Projeto

```
alpha-bot/
├── backend/                    # Backend Flask
│   ├── src/
│   │   ├── api/               # Blueprints (alphabot, drivebot)
│   │   ├── services/          # AI service, data analyzer
│   │   ├── utils/             # Data processor, helpers
│   │   ├── models/            # Data models
│   │   └── prompts/           # AI prompts
│   ├── database.py            # SQLite operations
│   ├── app.py                 # Flask app entry
│   └── requirements.txt       # Python deps
│
├── src/                       # Frontend React
│   ├── components/            # UI components
│   │   ├── ChatArea.tsx
│   │   ├── MessageBubble.tsx
│   │   └── Sidebar.tsx
│   ├── contexts/              # React contexts
│   │   ├── AuthContext.tsx
│   │   ├── BotContext.tsx
│   │   └── ConversationContext.tsx
│   ├── services/              # API client
│   └── types/                 # TypeScript types
│
├── docs/                      # Documentação técnica
├── scripts/                   # Scripts de teste
├── package.json               # Frontend deps
├── vite.config.ts             # Vite config
├── tailwind.config.cjs        # Tailwind config
└── README.md                  # Este arquivo
```

---

## 🧪 Testes

### Backend

```bash
cd backend

# Testar upload e chat do AlphaBot
python test_alphabot.py

# Testar DriveBot
python test_drivebot.py
```

### Frontend

```bash
# Build de produção
npm run build

# Preview da build
npm run preview
```

---

## 🤝 Contribuição

Contribuições são bem-vindas! Siga estes passos:

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/nova-feature`)
3. **Commit** suas mudanças (`git commit -m 'Add: nova feature incrível'`)
4. **Push** para a branch (`git push origin feature/nova-feature`)
5. Abra um **Pull Request**

### Convenções de Commit

```
feat: Nova funcionalidade
fix: Correção de bug
docs: Documentação
style: Formatação
refactor: Refatoração
test: Testes
chore: Manutenção
```

---

## 📝 Roadmap

- [ ] Autenticação OAuth2
- [ ] Export de relatórios (PDF/Excel)
- [ ] Gráficos interativos avançados
- [ ] Notificações em tempo real
- [ ] API pública documentada (Swagger)
- [ ] Suporte a PostgreSQL
- [ ] Deploy Kubernetes
- [ ] App Mobile (React Native)

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👥 Autores

- **Alpha Insights Team** - [GitHub](https://github.com/z4mbrano)

---

## 📞 Suporte

Caso tenha dúvidas ou problemas:

1. Abra uma [Issue](https://github.com/z4mbrano/alpha-bot/issues)
2. Consulte a [Documentação](./docs/)
3. Entre em contato via Pull Request

---

## 🙏 Agradecimentos

- Google Gemini AI pela API poderosa
- Comunidade React pela biblioteca incrível
- Todos os contribuidores do projeto

---

<div align="center">

**[⬆ Voltar ao topo](#-alpha-insights--plataforma-de-análise-inteligente-de-dados)**

Feito com ❤️ por Alpha Insights Team

</div>
