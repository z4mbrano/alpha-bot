# ALPHA INSIGHTS — Chat UI

Uma aplicação web moderna de chat com múltiplos bots alimentados por IA, desenvolvida para a Alpha Insights, empresa de varejo de tecnologia.

## 🚀 Features
- **DriveBot**: Especialista em análise de dados de vendas com IA avançada
- **AlphaBot**: Assistente geral para insights de negócios  
- **Tema Dark/Light**: Alternância suave com persistência local
- **Interface Responsiva**: Funciona perfeitamente em desktop, tablet e mobile
- **Indicadores de Digitação**: Feedback visual em tempo real
- **API Integration**: Backend Flask seguro com Google AI

## ⚡ Quick Start

### Frontend (React + Vite)
```powershell
# Na raiz do projeto
npm install
npm run dev
```
Acesse: http://localhost:5173/

### Backend (Flask + Google AI)
```powershell
# Em outro terminal
cd backend
pip install -r requirements.txt
python app.py
```
Backend: http://localhost:5000

## 🏗️ Arquitetura

### Frontend
- **React 18** + TypeScript + Vite
- **Tailwind CSS** para estilização
- **Zustand/Context** para gerenciamento de estado
- **Lucide React** para ícones

### Backend
- **Flask** como API proxy
- **Google AI (Gemini)** para respostas inteligentes
- **CORS** habilitado para comunicação frontend-backend
- **Prompts customizados** por bot

## 🤖 Os Bots

### DriveBot - Análise de Dados no Google Drive
**Fluxo de trabalho:**
1. Solicita ID da pasta do Google Drive
2. Instrui sobre compartilhamento com service account
3. Simula varredura e análise dos arquivos
4. Fornece relatório detalhado de status
5. Responde perguntas sobre os dados analisados

**Especialidades:**
- Análise de múltiplas planilhas simultaneamente
- Consolidação de dados de vendas
- Relatórios de performance empresarial
- Análise temporal e regional

### Analista de Planilhas - Análise Interativa de Arquivos
**Fluxo de trabalho:**
1. Convida o usuário a anexar planilhas
2. Processa automaticamente os arquivos enviados
3. Fornece feedback detalhado da análise
4. Responde perguntas específicas sobre os dados

**Especialidades:**
- Análise estatística de dados
- Rankings e comparações
- Identificação de tendências
- Métricas personalizadas

## 🔧 Configuração

As chaves de API já estão configuradas no arquivo `backend/.env`:
- **DriveBot**: `AIzaSyAm0ZCjVXqPN7IxVOxGUErfvTL-etqWAEg`
- **AlphaBot**: `AIzaSyANUpC4RMFB2O4mwQ4Wvf41a-LZHxvXitM`

## 📱 Responsividade
- **Desktop**: Layout completo com sidebar fixa
- **Tablet**: Sidebar recolhível para mais espaço
- **Mobile**: Menu hambúrguer com sidebar overlay

## 🎨 Design System
Cores otimizadas para tema escuro (padrão) e claro, inspiradas no Google Gemini com identidade visual da Alpha Insights.

## 🔄 Próximos Passos
1. **Persistência de Histórico**: Salvar conversas localmente
2. **Upload de Arquivos**: Funcionalidade do ícone de anexo
3. **Analytics**: Métricas de uso dos bots
4. **Deploy**: Configuração para produção

---
**Alpha Insights** - Tornando a análise de dados mais ágil e intuitiva.
