# 🏛️ Arquitetura do Alpha Insights

Este documento descreve a arquitetura completa do sistema Alpha Insights, incluindo decisões de design, fluxo de dados, padrões utilizados e estrutura modular.

---

## 📑 Índice

- [Visão Geral](#visão-geral)
- [Princípios Arquiteturais](#princípios-arquiteturais)
- [Arquitetura Frontend](#arquitetura-frontend)
- [Arquitetura Backend](#arquitetura-backend)
- [Fluxo de Dados](#fluxo-de-dados)
- [Padrões de Design](#padrões-de-design)
- [Segurança](#segurança)
- [Escalabilidade](#escalabilidade)

---

## Visão Geral

### Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────┐
│                 CAMADA DE APRESENTAÇÃO              │
│      React 18 + TypeScript + Tailwind CSS           │
│                 (Port 5173)                         │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/REST
                       │ JSON
┌──────────────────────▼──────────────────────────────┐
│              CAMADA DE API GATEWAY                  │
│                 Flask 3.0 + CORS                    │
│                 (Port 5000)                         │
└──────┬────────────────────────────────────┬─────────┘
       │                                    │
┌──────▼───────────┐              ┌────────▼─────────┐
│  CAMADA DE       │              │  CAMADA DE       │
│   SERVIÇOS       │              │   INTEGRAÇÃO     │
│                  │              │                  │
│ • AI Service     │              │ • Google AI      │
│ • Drive Service  │              │ • Drive API      │
│ • Data Analyzer  │              │ • Pandas         │
└──────────────────┘              └──────────────────┘
```

### Stack Tecnológico Completo

| Camada | Tecnologia | Versão | Propósito |
|--------|-----------|--------|-----------|
| **Frontend** | React | 18.2.0 | UI Library |
| | TypeScript | 5.2.2 | Type Safety |
| | Vite | 5.1.7 | Build Tool |
| | Tailwind CSS | 3.4.7 | Styling |
| | Lucide React | 0.258.0 | Icons |
| **Backend** | Flask | 3.0.0 | Web Framework |
| | Python | 3.10+ | Language |
| | Google AI SDK | latest | Gemini API |
| | Pandas | 2.0.0+ | Data Analysis |
| | google-api-python-client | latest | Drive API |
| **Infraestrutura** | Vite Dev Server | - | Development |
| | Flask Dev Server | - | Development |
| | Gunicorn | - | Production |

---

## Princípios Arquiteturais

### 1. Separation of Concerns (SoC)
Cada módulo tem uma responsabilidade única e bem definida:
- **Frontend**: Apresentação e interação com usuário
- **Backend API**: Roteamento e validação
- **Services**: Lógica de negócio
- **Utils**: Funções auxiliares reutilizáveis

### 2. Clean Architecture
Estrutura em camadas com dependências unidirecionais:
```
Presentation → API → Services → Models → Utils
```

### 3. DRY (Don't Repeat Yourself)
Código reutilizável em:
- Componentes React compartilhados
- Hooks customizados
- Funções utilitárias
- Prompts centralizados

### 4. SOLID Principles
- **S**: Single Responsibility (cada classe/módulo uma responsabilidade)
- **O**: Open/Closed (aberto para extensão, fechado para modificação)
- **L**: Liskov Substitution (componentes substituíveis)
- **I**: Interface Segregation (interfaces específicas)
- **D**: Dependency Inversion (dependa de abstrações)

---

## Arquitetura Frontend

### Estrutura de Componentes

```
src/
├── App.tsx                    # Raiz da aplicação
├── main.tsx                   # Entry point
├── index.css                  # Design system tokens
│
├── components/                # Componentes de UI
│   ├── ChatArea.tsx           # Container principal do chat
│   ├── Sidebar.tsx            # Menu lateral
│   └── MessageBubble.tsx      # Componente de mensagem
│
└── contexts/                  # Estado global
    ├── BotContext.tsx         # Gerenciamento de bots
    └── ThemeContext.tsx       # Tema dark/light
```

### Fluxo de Estado (Context API)

```
┌─────────────────┐
│  BotContext     │
│                 │
│  State:         │
│  • currentBot   │
│  • messages     │
│  • isTyping     │
│  • sessionIds   │
│                 │
│  Actions:       │
│  • switchBot    │
│  • sendMessage  │
│  • clearChat    │
└────────┬────────┘
         │
         ├──► ChatArea (consume)
         ├──► Sidebar (consume)
         └──► MessageBubble (consume)
```

### Design System (CSS Custom Properties)

```css
/* Tema escuro (padrão) */
:root {
  --bg: #0e0f12;           /* Fundo principal */
  --sidebar: #121418;       /* Fundo sidebar */
  --surface: #1a1d22;       /* Cards e elementos */
  --hover: #22252b;         /* Estado hover */
  --border: #2c2f36;        /* Bordas */
  --text: #f5f5f5;          /* Texto principal */
  --muted: #a0a0a0;         /* Texto secundário */
  --accent: #4f8cff;        /* Cor de destaque */
}

/* Tema claro */
.light {
  --bg: #ffffff;
  --sidebar: #f8f9fa;
  --surface: #ffffff;
  --hover: #f1f3f5;
  --border: #dee2e6;
  --text: #212529;
  --muted: #6c757d;
  --accent: #2f6bff;
}
```

### Componentes-Chave

#### ChatArea.tsx
```typescript
// Responsabilidades:
// 1. Renderizar lista de mensagens
// 2. Gerenciar upload de arquivos (AlphaBot)
// 3. Exibir welcome state
// 4. Mostrar indicador de digitação
// 5. Input de mensagem com submissão

// Hooks usados:
// - useBot() para acesso ao estado global
// - useState() para controle local (input, files)
// - useRef() para scroll automático
```

#### Sidebar.tsx
```typescript
// Responsabilidades:
// 1. Listagem de bots disponíveis
// 2. Troca de bot ativo
// 3. Menu hambúrguer (collapse)
// 4. Toggle dark/light theme
// 5. Estado de collapse responsivo

// Estados:
// - Desktop: Collapsed (ícones) / Expanded (texto)
// - Mobile: Hidden / Visible (overlay)
```

#### BotContext.tsx
```typescript
// Responsabilidades:
// 1. Manter estado global dos bots
// 2. Gerenciar mensagens por bot
// 3. Comunicação com API backend
// 4. Persistência de session_ids
// 5. Controle de estado de loading/typing

// Funções principais:
// - send(message): Enviar mensagem
// - switchBot(id): Trocar bot ativo
// - clearChat(): Limpar histórico
```

---

## Arquitetura Backend

### Estrutura Modular (Clean Architecture)

```
backend/
├── app.py                     # Entry point (Flask app)
│
├── src/
│   ├── api/                   # Camada de Apresentação
│   │   ├── alphabot.py        # Rotas AlphaBot
│   │   └── drivebot.py        # Rotas DriveBot
│   │
│   ├── services/              # Camada de Negócio
│   │   ├── ai_service.py      # Integração Gemini
│   │   ├── drive_service.py   # Integração Google Drive
│   │   └── data_analyzer.py   # Análise de dados
│   │
│   ├── models/                # Camada de Domínio
│   │   ├── conversation.py    # Modelo de conversação
│   │   └── session.py         # Modelo de sessão
│   │
│   ├── utils/                 # Utilitários
│   │   ├── file_handlers.py   # Processamento de arquivos
│   │   ├── data_processors.py # Transformação de dados
│   │   └── validators.py      # Validações
│   │
│   ├── prompts/               # Prompts de IA
│   │   ├── alphabot_prompt.py # Prompt AlphaBot
│   │   └── drivebot_prompt.py # Prompt DriveBot
│   │
│   └── config/                # Configurações
│       └── settings.py        # Constantes e env vars
│
├── tests/                     # Testes unitários
├── requirements.txt           # Dependências Python
└── service-account.json       # Credenciais Google
```

### Camadas e Responsabilidades

#### 1. API Layer (`src/api/`)
**Responsabilidade**: Receber requisições HTTP, validar entrada, retornar respostas

```python
# Exemplo: api/alphabot.py
@alphabot_bp.route('/upload', methods=['POST'])
def upload_files():
    # 1. Validar request
    # 2. Chamar service layer
    # 3. Retornar response JSON
    pass
```

#### 2. Service Layer (`src/services/`)
**Responsabilidade**: Implementar lógica de negócio, orquestrar operações

```python
# Exemplo: services/ai_service.py
class AIService:
    def generate_response(self, prompt, history):
        # 1. Configurar modelo
        # 2. Enviar prompt
        # 3. Processar resposta
        pass
```

#### 3. Model Layer (`src/models/`)
**Responsabilidade**: Definir estruturas de dados e entidades

```python
# Exemplo: models/session.py
@dataclass
class Session:
    id: str
    bot_id: str
    data: dict
    created_at: datetime
```

#### 4. Utils Layer (`src/utils/`)
**Responsabilidade**: Funções auxiliares reutilizáveis

```python
# Exemplo: utils/validators.py
def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

### Serviços Principais

#### AIService
```python
# Gerencia comunicação com Google Gemini
class AIService:
    - configure_model()
    - send_prompt()
    - format_history()
    - handle_streaming()
```

#### DriveService
```python
# Gerencia acesso ao Google Drive
class DriveService:
    - authenticate()
    - list_folder_files()
    - download_file()
    - get_file_metadata()
```

#### DataAnalyzer
```python
# Gerencia análise de dados Pandas
class DataAnalyzer:
    - load_dataframe()
    - detect_types()
    - generate_summary()
    - execute_query()
```

---

## Fluxo de Dados

### 1. AlphaBot - Upload e Análise

```
┌──────────┐     (1) Upload Files     ┌──────────┐
│  React   │────────────────────────►│  Flask   │
│ Frontend │                          │  /upload │
└──────────┘                          └─────┬────┘
                                            │
                                            │ (2) Validar arquivos
                                            │
                                      ┌─────▼──────┐
                                      │ File       │
                                      │ Handlers   │
                                      └─────┬──────┘
                                            │
                                            │ (3) Processar CSV/XLSX
                                            │
                                      ┌─────▼──────┐
                                      │ Data       │
                                      │ Processors │
                                      └─────┬──────┘
                                            │
                                            │ (4) Criar sessão
                                            │
┌──────────┐     (5) Session ID       ┌─────▼──────┐
│  React   │◄────────────────────────│  Session   │
│ Frontend │                          │  Manager   │
└──────────┘                          └────────────┘
```

### 2. AlphaBot - Chat Interativo

```
┌──────────┐  (1) POST /chat         ┌──────────┐
│  React   │────────────────────────►│  Flask   │
│ Frontend │  {session_id, message}  │  /chat   │
└──────────┘                          └─────┬────┘
                                            │
                                            │ (2) Recuperar sessão
                                            │
                                      ┌─────▼──────┐
                                      │ Session    │
                                      │ Manager    │
                                      └─────┬──────┘
                                            │
                                            │ (3) Montar prompt
                                            │
                                      ┌─────▼──────┐
                                      │ AlphaBot   │
                                      │ Prompt     │
                                      └─────┬──────┘
                                            │
                                            │ (4) Enviar para IA
                                            │
                                      ┌─────▼──────┐
                                      │ AI Service │
                                      │ (Gemini)   │
                                      └─────┬──────┘
                                            │
                                            │ (5) Processar resposta
                                            │
┌──────────┐  (6) Response JSON       ┌─────▼──────┐
│  React   │◄────────────────────────│  Flask     │
│ Frontend │  {response, metadata}    │            │
└──────────┘                          └────────────┘
```

### 3. DriveBot - Análise de Pasta

```
┌──────────┐  (1) POST /chat         ┌──────────┐
│  React   │────────────────────────►│  Flask   │
│ Frontend │  {message: folder_url}  │  /chat   │
└──────────┘                          └─────┬────┘
                                            │
                                            │ (2) Extrair folder_id
                                            │
                                      ┌─────▼──────┐
                                      │ URL Parser │
                                      └─────┬──────┘
                                            │
                                            │ (3) Autenticar
                                            │
                                      ┌─────▼──────┐
                                      │ Drive      │
                                      │ Service    │
                                      └─────┬──────┘
                                            │
                                            │ (4) Listar arquivos
                                            │
                                      ┌─────▼──────┐
                                      │ Drive API  │
                                      └─────┬──────┘
                                            │
                                            │ (5) Download & parse
                                            │
                                      ┌─────▼──────┐
                                      │ File       │
                                      │ Handlers   │
                                      └─────┬──────┘
                                            │
                                            │ (6) Consolidar dados
                                            │
                                      ┌─────▼──────┐
                                      │ Data       │
                                      │ Analyzer   │
                                      └─────┬──────┘
                                            │
                                            │ (7) Gerar relatório
                                            │
                                      ┌─────▼──────┐
                                      │ AI Service │
                                      │ (Gemini)   │
                                      └─────┬──────┘
                                            │
┌──────────┐  (8) Response JSON       ┌─────▼──────┐
│  React   │◄────────────────────────│  Flask     │
│ Frontend │  {report, files_count}   │            │
└──────────┘                          └────────────┘
```

---

## Padrões de Design

### 1. Repository Pattern
**Onde**: Session management, Data storage  
**Por quê**: Abstrair acesso a dados

```python
class SessionRepository:
    def save(self, session: Session):
        # Salvar em memória/banco
        pass
    
    def find_by_id(self, session_id: str) -> Session:
        # Buscar sessão
        pass
```

### 2. Factory Pattern
**Onde**: Criação de modelos AI, inicialização de serviços  
**Por quê**: Centralizar criação de objetos complexos

```python
class AIModelFactory:
    @staticmethod
    def create_model(bot_type: str):
        if bot_type == "alphabot":
            return genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=ALPHABOT_PROMPT
            )
```

### 3. Strategy Pattern
**Onde**: Análise de dados, processamento de arquivos  
**Por quê**: Trocar algoritmos dinamicamente

```python
class FileProcessor:
    def process(self, file, strategy):
        if strategy == "csv":
            return CSVProcessor().process(file)
        elif strategy == "excel":
            return ExcelProcessor().process(file)
```

### 4. Observer Pattern
**Onde**: Indicadores de digitação, updates de estado  
**Por quê**: Notificar componentes de mudanças

```typescript
// Frontend: Context API implementa Observer
const { isTyping } = useBot(); // Componente "observa" estado
```

### 5. Singleton Pattern
**Onde**: Configurações, API clients  
**Por quê**: Garantir instância única

```python
class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

---

## Segurança

### 1. API Keys
- **Armazenamento**: Variáveis de ambiente (`.env`)
- **Não versionadas**: `.gitignore` bloqueia `.env` e `service-account.json`
- **Rotação**: Keys separadas para cada bot

### 2. CORS
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173"],  # Dev
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

### 3. Validação de Input
```python
# Validar tipos de arquivo
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

# Validar tamanho
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Sanitizar input do usuário
def sanitize_input(text: str) -> str:
    return text.strip()[:1000]  # Limitar tamanho
```

### 4. Service Account (Google)
- **Permissões mínimas**: Somente leitura no Drive
- **Compartilhamento explícito**: Pastas devem ser compartilhadas
- **Token de acesso**: Renovação automática

---

## Escalabilidade

### Estratégias de Crescimento

#### 1. Cache Layer
```python
# Redis para sessões e resultados frequentes
from redis import Redis

cache = Redis(host='localhost', port=6379)

def get_or_compute(key, compute_fn):
    cached = cache.get(key)
    if cached:
        return json.loads(cached)
    
    result = compute_fn()
    cache.setex(key, 3600, json.dumps(result))
    return result
```

#### 2. Background Jobs
```python
# Celery para processamento assíncrono
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def process_large_file(file_path):
    # Processar arquivo grande em background
    pass
```

#### 3. Database Migration
```python
# SQLite → PostgreSQL para produção
# Manter interface repository consistente

class PostgresSessionRepository(SessionRepository):
    def save(self, session: Session):
        # Implementação PostgreSQL
        pass
```

#### 4. Load Balancing
```
┌─────────┐
│ Nginx   │
│ (LB)    │
└────┬────┘
     │
     ├───► Flask Instance 1 (Port 5001)
     ├───► Flask Instance 2 (Port 5002)
     └───► Flask Instance 3 (Port 5003)
```

#### 5. API Rate Limiting
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)

@app.route("/api/chat")
@limiter.limit("10 per minute")
def chat():
    pass
```

---

## Decisões Arquiteturais (ADRs)

### ADR-001: Escolha do React sobre Vue/Angular
**Contexto**: Necessidade de framework frontend moderno  
**Decisão**: Usar React 18  
**Razões**:
- Ecossistema maduro
- TypeScript de primeira classe
- Performance (Virtual DOM)
- Ampla comunidade

### ADR-002: Flask sobre FastAPI
**Contexto**: Framework backend Python  
**Decisão**: Usar Flask 3.0  
**Razões**:
- Simplicidade para MVP
- Maturidade e estabilidade
- Fácil integração com Pandas
- WSGI padrão (Gunicorn)

### ADR-003: Context API sobre Redux
**Contexto**: Gerenciamento de estado frontend  
**Decisão**: Usar Context API  
**Razões**:
- Aplicação de tamanho médio
- Menos boilerplate
- Nativo do React
- Suficiente para necessidades atuais

### ADR-004: Tailwind CSS sobre CSS-in-JS
**Contexto**: Solução de estilização  
**Decisão**: Usar Tailwind CSS + CSS Variables  
**Razões**:
- Desenvolvimento rápido
- Design system consistente
- Temas fáceis com CSS vars
- Build-time optimizations

### ADR-005: Gemini sobre GPT/Claude
**Contexto**: Escolha de modelo de IA  
**Decisão**: Usar Google Gemini  
**Razões**:
- Integração nativa com Google Drive
- API gratuita generosa
- Performance satisfatória
- Multimodal capabilities

---

## Monitoramento e Observabilidade

### Logs
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("Request received", extra={"user_id": user_id})
```

### Métricas
```python
# Prometheus + Grafana (futuro)
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)

@app.route("/api/chat")
@metrics.counter('chat_requests_total', 'Total chat requests')
def chat():
    pass
```

### Health Checks
```python
@app.route("/health")
def health():
    return {
        "status": "ok",
        "checks": {
            "gemini_api": check_gemini_connection(),
            "drive_api": check_drive_connection(),
        }
    }
```

---

## Próximos Passos

1. **Implementar testes automatizados** (Jest, Pytest)
2. **Adicionar autenticação de usuários** (JWT)
3. **Migrar para banco de dados** (PostgreSQL)
4. **Implementar cache** (Redis)
5. **Configurar CI/CD** (GitHub Actions)
6. **Adicionar monitoramento** (Sentry, Datadog)
7. **Documentar API** (OpenAPI/Swagger)
8. **Containerizar** (Docker, Docker Compose)

---

<div align="center">

**[⬅ Voltar ao README](../README.md)**

</div>
