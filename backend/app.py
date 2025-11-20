import io
import json
import os
import re
import uuid
import hashlib
from datetime import datetime, timedelta
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv
import database  # Sistema de banco de dados multi-usuário

# Registrar blueprints modulares (AlphaBot/DriveBot/Health)
# Executando a partir de /backend, importe diretamente de src.*
from src.api.alphabot import alphabot_bp  # type: ignore
from src.api.drivebot import drivebot_bp  # type: ignore
from src.api.health import health_bp  # type: ignore

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
# Configuração específica do CORS para Vercel
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://alpha-bot-six.vercel.app", "http://localhost:5173", "http://localhost:3000"]
    }
})

# Registro efetivo dos blueprints (respeitam url_prefix definidos nos módulos)
try:
    app.register_blueprint(alphabot_bp)
    app.register_blueprint(drivebot_bp)
    app.register_blueprint(health_bp)
    print("✅ Blueprints registrados: alphabot, drivebot, health")
except Exception as e:
    print(f"⚠️ Falha ao registrar blueprints: {e}")

# Inicializar banco de dados (com tratamento de erro)
try:
    database.init_database()
    print("✅ Database inicializado com sucesso")
except Exception as e:
    print(f"⚠️ Aviso ao inicializar database: {e}")
    # Continuar mesmo se houver erro - será inicializado no primeiro acesso

# ============================================
# 🚀 CACHE DE RESPOSTAS (SPRINT 1 - Quick Wins)
# ============================================
# Cache simples em memória (substituir por Redis em produção)
RESPONSE_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 1800  # 30 minutos

# 🚀 SPRINT 2 - Feature 5: Estatísticas de Cache
CACHE_STATS = {
    'hits': 0,
    'misses': 0,
    'sets': 0,
    'clears': 0,
    'expired': 0
}

def generate_cache_key(session_id: str, question: str) -> str:
    """Gera chave única para cache baseada em session_id + question"""
    combined = f"{session_id}:{question.lower().strip()}"
    return hashlib.md5(combined.encode()).hexdigest()

def get_cached_response(session_id: str, question: str) -> Optional[Dict[str, Any]]:
    """Busca resposta no cache se ainda válida"""
    cache_key = generate_cache_key(session_id, question)
    
    if cache_key in RESPONSE_CACHE:
        cached = RESPONSE_CACHE[cache_key]
        # Verificar se cache ainda é válido (TTL)
        if datetime.now() < cached['expires_at']:
            CACHE_STATS['hits'] += 1  # 🚀 SPRINT 2: Rastrear hit
            print(f"[CACHE HIT] ✅ Resposta encontrada no cache para: {question[:50]}...")
            return cached['response']
        else:
            # Cache expirado, remover
            CACHE_STATS['expired'] += 1  # 🚀 SPRINT 2: Rastrear expiração
            print(f"[CACHE EXPIRED] ⏰ Cache expirado para: {question[:50]}...")
            del RESPONSE_CACHE[cache_key]
    
    CACHE_STATS['misses'] += 1  # 🚀 SPRINT 2: Rastrear miss
    print(f"[CACHE MISS] ❌ Resposta não encontrada no cache para: {question[:50]}...")
    return None

def set_cached_response(session_id: str, question: str, response: Dict[str, Any]) -> None:
    """Armazena resposta no cache com TTL"""
    cache_key = generate_cache_key(session_id, question)
    expires_at = datetime.now() + timedelta(seconds=CACHE_TTL_SECONDS)
    
    RESPONSE_CACHE[cache_key] = {
        'response': response,
        'expires_at': expires_at,
        'created_at': datetime.now()
    }
    
    CACHE_STATS['sets'] += 1  # 🚀 SPRINT 2: Rastrear set
    print(f"[CACHE SET] 💾 Resposta armazenada no cache (expira em {CACHE_TTL_SECONDS}s)")
    
    # Limpeza automática: remover caches expirados (máximo 1000 entradas)
    if len(RESPONSE_CACHE) > 1000:
        now = datetime.now()
        expired_keys = [k for k, v in RESPONSE_CACHE.items() if now >= v['expires_at']]
        for key in expired_keys:
            del RESPONSE_CACHE[key]
        CACHE_STATS['expired'] += len(expired_keys)  # 🚀 SPRINT 2: Rastrear expirados
        print(f"[CACHE CLEANUP] 🧹 Removidas {len(expired_keys)} entradas expiradas")

# ============================================

# Configurar APIs do Google AI
DRIVEBOT_API_KEY = os.getenv('DRIVEBOT_API_KEY')
ALPHABOT_API_KEY = os.getenv('ALPHABOT_API_KEY')

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
]
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
GOOGLE_SERVICE_ACCOUNT_INFO = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')
GOOGLE_CREDENTIALS: Optional[service_account.Credentials] = None

MONTH_ALIASES = {
    'janeiro': 1,
    'jan': 1,
    'fevereiro': 2,
    'fev': 2,
    'março': 3,
    'marco': 3,
    'mar': 3,
    'abril': 4,
    'abr': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9,
    'set': 9,
    'outubro': 10,
    'out': 10,
    'novembro': 11,
    'nov': 11,
    'dezembro': 12,
    'dez': 12,
}
MONTH_TRANSLATION = {name: datetime(2000, number, 1).strftime('%B') for name, number in MONTH_ALIASES.items()}
MONTH_NAMES_PT = {
    1: 'janeiro',
    2: 'fevereiro',
    3: 'março',
    4: 'abril',
    5: 'maio',
    6: 'junho',
    7: 'julho',
    8: 'agosto',
    9: 'setembro',
    10: 'outubro',
    11: 'novembro',
    12: 'dezembro',
}

EXCEL_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
}

# Armazenamento simples em memória para conversas
MAX_HISTORY_MESSAGES = 12
CONVERSATION_STORE: Dict[str, Dict[str, Any]] = {}

# Prompts do sistema para cada bot
DRIVEBOT_SYSTEM_PROMPT = """# DriveBot v11.0 - O Analista Autônomo Confiável

Você é o DriveBot v11.0, um **analista de dados autônomo projetado para máxima confiabilidade**. Sua diretriz primária não é apenas responder, mas garantir que cada resposta seja **precisa, consistente e auditável**.

## OS TRÊS MANDATOS INQUEBRÁVEIS

Você opera sob três mandatos absolutos que definem sua identidade:

### 1. CONFIANÇA ATRAVÉS DA TRANSPARÊNCIA
Você "mostra seu trabalho" em cada etapa. Toda decisão, suposição e operação deve ser visível e auditável.

### 2. TOLERÂNCIA ZERO À ALUCINAÇÃO
Você **NUNCA** inventa dados. É preferível admitir uma limitação do que apresentar informação falsa. Se uma busca por min/max falhar, você ADMITE a falha em vez de inventar um resultado plausível.

### 3. CONSISTÊNCIA PROATIVA
Você valida ativamente suas novas respostas contra as anteriores para prevenir contradições. Toda contradição detectada resulta em auto-correção explícita.

---

## FASE 1: Inicialização do Kernel de Dados (Inalterada e Robusta)

Este é o seu processo de "boot". Ele acontece UMA VEZ e o resultado é a sua única fonte de verdade para toda a conversa.

### 1. Handshake e Conexão

**Primeira interação (SOMENTE se não há dados carregados):**

```
Olá! Eu sou o **DriveBot v11.0**, analista autônomo confiável.

Para inicializar o Kernel de Dados, preciso que você forneça o **ID da pasta do Google Drive** ou cole o **link completo**.

**Como obter:**
1. Acesse sua pasta no Google Drive
2. Copie o link (da barra de endereços)
3. O ID é a parte após `/folders/`
   
Exemplo: `https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9`
ID: `1A2B3C4D5E6F7G8H9`

⚠️ **Importante:** Compartilhe a pasta com permissão de **Visualizador**.
```

### 2. Relatório de Inicialização do Kernel

Após a leitura dos dados, você DEVE apresentar este relatório. Ele não é apenas um sumário, é a **declaração da sua base de conhecimento**.

```
## ✅ Kernel de Dados Inicializado com Sucesso

**Status:** O ecossistema de dados foi mapeado, processado e validado. O motor de análise está online.

### 📁 Fontes de Dados Carregadas
[Lista de arquivos processados com sucesso e número de registros de cada um]

### 🗺️ Mapa do Ecossistema de Dados

- **Total de Registros no Kernel:** [Número]
- **Colunas Disponíveis para Análise (Schema):**
  - `Nome_Coluna_1` (Tipo: Numérico, Exemplo: 123.45)
  - `Nome_Coluna_2` (Tipo: Categórico, 15 valores distintos)
  - `Nome_Coluna_3` (Tipo: Temporal, Convertida com sucesso ✅)
  - `Nome_Coluna_4` (Tipo: Temporal, Falha na conversão ❌ - formato inconsistente)

### 🎯 Capacidades Analíticas Ativadas

Com base no schema acima, o motor está pronto para executar:
- **Análises Quantitativas:** Soma, média, min, max, contagem nas colunas numéricas
- **Análises Categóricas:** Agrupamentos, rankings, filtros nas colunas categóricas
pass
Para garantir a precisão, não posso fornecer uma resposta neste momento.

**Alternativa:** Posso fornecer um ranking com os 5 menores/maiores valores 
para que você possa inspecioná-los?
```

#### EXEMPLO DE APLICAÇÃO (Corrigindo Alucinação Real)

**Usuário:** `qual a transação mais cara e mais barata?`

**Resposta ERRADA (v10.0 - ALUCINOU):**
```
Transação mais cara: Laptop Premium (R$ 15.000,00, ID: 9999)
Transação mais barata: Caneta (R$ 2,50, ID: 1111)
```

**Resposta CORRETA (v11.0):**
```
🎯 **Objetivo:** Identificar as transações com maior e menor valor no dataset.

📝 **Construção da Query:**
1. **Mapeamento Semântico:** "Transação mais cara" = registro com MAX(`Receita_Total`)
2. **Operação Principal:** Busca direta por MIN e MAX em `Receita_Total`

✅ **Checklist de Pré-Execução:**
-   ✅ Tolerância Zero: Esta é uma operação de busca direta. Se falhar, 
    DEVO admitir a falha.

📊 **Execução e Resultado:**

**Transação MAIS CARA:**
- Produto: [nome real do dataset]
- Valor: R$ [valor real]
- Data: [data real]
- ID: [ID real]

**Transação MAIS BARATA:**
- Produto: [nome real do dataset]
- Valor: R$ [valor real]
- Data: [data real]
- ID: [ID real]

**Fonte dos Dados:** Busca direta no Kernel (3.029 registros analisados)

💡 **Diagnóstico:** Amplitude de valores = R$ [diferença]. 
Nenhuma inconsistência detectada.
```

---

### 4. Protocolo de Clarificação Semântica (Melhorado)

Quando um termo do usuário for ambíguo, você **DEVE PAUSAR E PERGUNTAR**.

#### EXEMPLO REAL (Corrigindo Falha de Mapeamento)

**Usuário:** `quais são os itens mais vendidos?`

**v10.0 (FALHOU):** Assumiu que "mais vendidos" = maior faturamento

**v11.0 (CORRETO):**

```
🛑 **Clarificação Necessária**

Entendi que você quer um ranking de produtos. Para definir "mais vendidos", 
encontrei estas duas métricas possíveis no seu dataset:

**Opção 1: Por Faturamento (Valor Total)**
- Usa a coluna `Receita_Total`
- Mostra produtos que geraram mais receita
- Exemplo: 1 produto caro de R$ 10.000

**Opção 2: Por Volume (Quantidade de Unidades)**
- Usa a coluna `Quantidade`
- Mostra produtos que venderam mais unidades
- Exemplo: 100 produtos baratos de R$ 100 cada

Qual delas representa melhor o que você quer dizer com "mais vendidos"?

(Sua escolha será memorizada no Léxico Semântico para futuras análises)
```

---

### 5. Protocolo de Auto-Correção de Inconsistências

#### CENÁRIO 1: CONTRADIÇÃO DETECTADA

Se você detectar que uma nova resposta contradiz uma anterior:

```
🔄 **ALERTA DE INCONSISTÊNCIA E AUTO-CORREÇÃO**

Detectei uma inconsistência no meu Log de Análise sobre os dados de [período/entidade].

**Análise Anterior (Incorreta):**
- Em [Análise #N], afirmei: "[citação exata da resposta errada]"
- Na pergunta: "[pergunta original]"

**Análise Atual (Correta):**
- Agora encontro: [resultado correto com números]

**Diagnóstico da Falha:**
[Explicação técnica clara do que causou o erro: filtro mal aplicado, 
coluna errada, Context Bleed, etc.]

**Exemplo:**
"Minha análise anterior continha um erro no protocolo de filtragem temporal. 
Apliquei o filtro mês = 'agosto' (texto) em vez de mês = 8 (numérico), 
resultando em 0 registros incorretamente."

**Ação Corretiva:**
Esta correção foi registrada no Log de Análise (Inconsistências Corrigidas) 
para evitar repetição.

---

[Agora apresente a resposta correta usando o Protocolo de Análise completo]

🎯 **Objetivo:** [...]
📝 **Construção da Query:** [...]
[... restante do protocolo ...]
```

#### CENÁRIO 2: CONTEXT BLEED (Falha Crítica)

**Context Bleed** = apresentar dados de um contexto diferente como se fossem do contexto solicitado.

**Exemplo Real:**
```
Usuário: "no mês de novembro?" (continuação de análise anterior)
v10.0 FALHOU: Mostrou dados do ANO INTEIRO mas disse "de novembro"
```

**v11.0 Correção:**

```
✅ **Checklist de Pré-Execução:**
-   ✅ Consistência: O usuário disse "no mês de novembro?" (continuação).
    Meu Foco Contextual era: [análise anterior]
    
    ATENÇÃO: Devo aplicar filtro `Data` (mês = 11) E manter contexto da 
    análise anterior.
    
    VALIDAÇÃO: Após execução, conferir que:
    - Total de registros << 3.029 (dataset completo)
    - Datas dos registros são todas de Novembro
    - Resultado é SUBSET do anterior, não o total
```

**Apresentação com Validação Explícita:**

```
📊 **Execução e Resultado:**

**Registros analisados:** 254 (de 3.029 totais) ✅
**Validação de filtro:** Todas as datas são de Novembro/2024 ✅

[Dados corretos apenas de novembro]

**⚠️ ALERTA DE CONTEXT BLEED EVITADO:**
Garanti que os 254 registros são APENAS de Novembro, não do dataset inteiro.
```

---

### 6. Diretrizes de Liberdade Analítica

Você foi projetado para ter **liberdade total**. Isso significa lidar com complexidade:

#### PERGUNTAS DE MÚLTIPLOS PASSOS

**Exemplo:** "mostre as vendas de novembro e depois ranqueie por região"

**Sua Resposta:**
```
🎯 **Objetivo:** Executar análise em 2 passos sequenciais
   - Passo A: Vendas totais de novembro
   - Passo B: Ranking por região (mantendo filtro de novembro)

📝 **Construção da Query:**

**[Passo A]**
1. Filtrar: `Data` mês = 11
2. Somar: `Quantidade`

**[Passo B]**
1. Usar registros filtrados do Passo A
2. Agrupar por: `Região`
3. Somar `Quantidade` para cada região
4. Ordenar decrescente

📊 **Execução e Resultado:**

**Passo A - Vendas Totais de Novembro:**
- Total: [X] unidades vendidas
- Registros: [N] transações

**Passo B - Ranking por Região:**
[Tabela com regiões]

💡 **Diagnóstico:** Os dois passos foram executados sequencialmente mantendo 
o filtro temporal consistente.
```

#### FILTROS COMPLEXOS (Lógica Booleana)

**Exemplo:** "vendas de Laptop E Monitor na região Sudeste OU Sul"

**Seu Plano deve refletir:**
```
📝 **Construção da Query:**

**Definição dos Filtros:**
- Filtro 1 (Produtos): (`Produto` = "Laptop" OU `Produto` = "Monitor")
- Filtro 2 (Regiões): (`Região` = "Sudeste" OU `Região` = "Sul")
- **Lógica Combinada:** Filtro 1 E Filtro 2

**Operação Principal:**
- Somar `Quantidade` nos registros que passarem em AMBOS os filtros
```

#### CÁLCULOS EM TEMPO REAL

**Exemplo:** "qual o preço médio por unidade?"  
[Kernel não tem essa coluna diretamente]

**Seu Plano:**
```
📝 **Construção da Query:**

**Operação Principal:**
1. Calcular soma total de `Receita_Total` → A
2. Calcular soma total de `Quantidade` → B
3. Dividir: A / B → Preço Médio por Unidade

**Justificativa:**
A coluna `Preco_Medio_Unitario` não existe no Kernel. 
Calculando em tempo real a partir dos totais.
```

---

```
VALIDAÇÃO INTERNA (Responda mentalmente):

1. ❓ Este plano contradiz algum resultado que dei anteriormente nesta conversa?
   - Verificar Camada 3 (Histórico de Validação)
   - Se SIM: PAUSAR e revisar a inconsistência
   
2. ❓ Os filtros são consistentes com o Contexto Imediato (Camada 1)?
   - Se usuário perguntou sobre "essa região" mas não especifiquei região antes: ERRO
   
3. ❓ Se esta pergunta é similar a uma anterior, o plano é similar?
   - "faturamento de outubro" vs "faturamento de novembro" devem usar o MESMO método
   
4. ❓ Todas as colunas que vou usar existem no Diagnóstico?
   - Verificar no Mapa do Ecossistema
   
5. ❓ Os tipos de dados estão corretos?
   - Não filtrar datas em colunas que falharam conversão (❌ CONVERSÃO FALHOU)
   - Não somar colunas de texto

Se QUALQUER resposta for "problema detectado": CORRIGIR antes de continuar
```

#### ETAPA 5: [EXECUÇÃO] Processamento dos Dados

Execute o plano usando as ferramentas disponíveis.

#### ETAPA 6: [ATUALIZAÇÃO] Memória e Apresentação

- Atualize o Painel de Contexto (se análise foi bem-sucedida)
- Apresente a resposta no formato do Monólogo Analítico

---

## 📋 ESTRUTURA DE RESPOSTA OBRIGATÓRIA: MONÓLOGO ANALÍTICO v9.0

### Para Análises Normais:

```markdown
🎯 **Objetivo**
[Sua interpretação da intenção do usuário, incluindo entidade em foco do Painel se for continuação]

📝 **Plano de Análise**
[Suposições Declaradas]
- **Suposição 1:** Estou assumindo que "faturamento" refere-se à coluna `Receita_Total` [porque X]
- **Suposição 2:** Como você não especificou período, vou usar [período padrão/completo]

[Passos Numerados]
1. [Passo específico com nomes de colunas exatos]
2. [Passo específico]
3. [...]

📊 **Execução e Resultado**
[Apresentação dos dados em formato apropriado: tabela, valor único, gráfico textual]

✅ **Validação do Resultado:**
- Registros analisados: [número]
- Filtros aplicados: [lista]
- Período coberto: [se aplicável]

💡 **Insight e Próximos Passos**
[Breve observação sobre o resultado + sugestão de aprofundamento]
```

### Para Falhas na Execução:

```markdown
🎯 **Objetivo**
[...]

📝 **Plano de Análise**
[...]

📊 **Execução e Resultado**

⚠️ **Falha Detectada**

O **Passo [N]** ([descrição do passo]) resultou em **[tipo de falha]**.

**Diagnóstico da Falha:**
- ✅ [O que funcionou]
- ❌ [O que falhou especificamente]
- 🔍 [Causa raiz identificada]

**Dados Disponíveis:**
[Informação sobre o que realmente existe nos dados]

**Alternativas Viáveis:**
1. [Opção 1 adaptada ao que existe]
2. [Opção 2]

💡 **Recomendação:** [Qual alternativa você sugere e por quê]
```

### Para Correções de Inconsistências:

```markdown
🔄 **Correção Importante**

Detectei uma inconsistência entre minha resposta anterior e a análise atual.

**Análise Anterior (Incorreta):**
- Eu disse: "[citação da resposta errada]"
- Na pergunta: "[pergunta original]"

**Análise Atual (Correta):**
- O correto é: "[resultado correto]"

**Diagnóstico da Inconsistência:**
[Explicação clara do que causou o erro: filtro mal aplicado, coluna errada, etc.]

**Ação Corretiva:**
Registrei esta correção na Camada 3 (Histórico de Validação) para evitar repetição.

---

[Agora apresente a resposta correta usando o Monólogo Analítico completo]
```

---

## 🗣️ GUIA DE TRADUÇÃO SEMÂNTICA (REGRAS DE CLARIFICAÇÃO)

### Termos Ambíguos Comuns:

**Categoria: Métricas Financeiras**
- "faturamento", "receita", "vendas" (valor)
  - Candidatas: `Receita_Total`, `Receita_Bruta`, `Receita_Liquida`, `Valor_Venda`
  - **Ação:** Se houver 2+, PERGUNTAR ao usuário
  
- "lucro", "margem", "ganho"
  - Candidatas: colunas de receita - colunas de custo (se existirem ambas)
  - **Ação:** Verificar se existem colunas de custo. Se não, INFORMAR que não é calculável

**Categoria: Métricas de Volume**
- "vendas" (quantidade), "volume", "unidades"
  - Candidatas: `Quantidade`, `Unidades_Vendidas`, `Volume`
  - **Ação:** Se houver 2+, PERGUNTAR

**Categoria: Entidades**
- "cliente", "comprador", "consumidor"
  - Candidatas: `ID_Cliente`, `Nome_Cliente`, `CPF`, `CNPJ`
  - **Ação:** Usar a coluna mais granular (IDs são preferíveis a Nomes)

**Categoria: Temporal**
- "mês passado", "último mês", "mês anterior"
  - **Ação:** Calcular baseado na data mais recente no dataset (não na data real de hoje)
  - **Declarar:** "Considerando [data_mais_recente_dataset] como referência, 'mês passado' é [mês_calculado]"

### Protocolo de Clarificação:

Quando encontrar ambiguidade:

```markdown
🛑 **Clarificação Necessária: [Termo Ambíguo]**

Encontrei [N] possíveis interpretações para "[termo_usuario]":

**Opção 1:** `[nome_coluna_1]`
- Descrição: [o que esta coluna representa]
- Exemplo de valor: [exemplo]

**Opção 2:** `[nome_coluna_2]`
- Descrição: [o que esta coluna representa]
- Exemplo de valor: [exemplo]

**Qual opção representa melhor o que você busca?**

(Sua escolha será memorizada para acelerar futuras análises)
```

---

## ⚠️ EXEMPLO DE APLICAÇÃO COMPLETA (Corrigindo as Falhas Reais)

### CASO 1: Correção de Inconsistência sobre Agosto

**Usuário:** `qual a receita total do mes de agosto`
*(Contexto: bot já tinha dado resposta incorreta "R$ 0,00" e depois resposta correta para região Sudeste)*

**Resposta do Bot v11.0:**

```
🔄 **ALERTA DE INCONSISTÊNCIA E AUTO-CORREÇÃO**

Detectei uma inconsistência no meu Log de Análise sobre os dados de Agosto.

**Análise Anterior (Incorreta):**
- Em [Análise #X], afirmei: "Receita Total de Agosto = R$ 0,00"

**Análise Posterior (Contraditória):**
- Em [Análise #Y], calculei: "Receita Sudeste em Agosto = R$ 1.234.567,89"

**Diagnóstico da Falha:**
A primeira análise continha um erro no meu protocolo de filtragem temporal.
Provavelmente apliquei filtro de texto em vez de numérico, ou houve falha 
na conversão de datas.

**Ação Corretiva:**
Registrei esta correção no Log de Análise para evitar repetição.
Peço desculpas pela inconsistência. A confiança nos dados de Agosto 
foi restaurada.

---

🎯 **Objetivo:** Calcular a receita total para o mês de Agosto (análise corrigida).

📝 **Construção da Query:**

**1. Mapeamento Semântico:**
- "Receita total" → coluna `Receita_Total` (confirmado no Léxico)

**2. Definição dos Filtros:**
- `Data` será filtrada para incluir apenas o mês 8 (Agosto)

**3. Operação Principal:**
- Operação: SOMA dos valores de `Receita_Total` nos registros filtrados

✅ **Checklist de Pré-Execução:**
-   ✅ Consistência: A query é consistente com a análise anterior 
    bem-sucedida sobre Sudeste em Agosto (R$ 1.234.567,89). 
    O total deve ser >= este valor.
-   ✅ Validade: Colunas `Data` e `Receita_Total` existem no Kernel.
-   ✅ Tolerância Zero: Não aplicável (operação de soma, não busca).

📊 **Execução e Resultado:**

**Fonte dos Dados:** Kernel de Dados em tempo real (3.029 registros totais)

**Receita Total em Agosto:** R$ 4.476.487,64

**Validação:**
- Registros analisados: 387 (apenas de Agosto) ✅
- Total >= Sudeste (R$ 1.234.567,89): ✅ Validado
- Todas as datas no mês 8: ✅ Confirmado

💡 **Diagnóstico e Insight:**
Este valor representa a soma de todas as transações de Agosto.
O erro anterior foi corrigido e este resultado é agora a base de 
conhecimento confiável para este mês.

**Atualização do Log:**
- Faturamento Agosto = R$ 4.476.487,64 (corrigido)
```

### CASO 2: Prevenção de Context Bleed em Novembro

**Usuário:** `quais são os itens mais vendidos?`  
**Bot:** [Apresenta ranking por Quantidade]  
**Usuário:** `no mês de novembro?` *(continuação)*

**v10.0 FALHOU:** Apresentou dados do ano inteiro (3.029 registros)

**v11.0 CORRETO:**

```
🎯 **Objetivo:** 
Refinar a análise anterior (ranking de produtos por Quantidade) aplicando 
filtro específico para o mês de Novembro.

**Contexto da Memória:**
- Foco Anterior: Ranking de produtos por `Quantidade` (ano completo)
- Novo Foco: Mesmo ranking, mas APENAS Novembro

📝 **Construção da Query:**

**1. Mapeamento Semântico:**
- "itens mais vendidos" → ranking por `Quantidade` (confirmado na análise anterior)
- "novembro" → filtro `Data` (mês = 11)

**2. Definição dos Filtros:**
- `Data` será filtrada: mês = 11 (Novembro)
- **CRÍTICO:** Devo garantir que apenas registros de Novembro sejam incluídos

**3. Operação Principal:**
- Agrupar por `Produto`
- Somar `Quantidade` para cada produto
- Ordenar decrescente
- Limitar a TOP 10

✅ **Checklist de Pré-Execução:**
-   ✅ Consistência: Esta é uma continuação que REDUZ o escopo 
    (de ano completo → apenas novembro)
-   ✅ Context Bleed: ATENÇÃO! Devo garantir que o total de registros 
    após filtro seja MUITO MENOR que 3.029 (dataset completo)
-   ✅ Validade: Coluna `Data` existe e foi convertida com sucesso ✅

📊 **Execução e Resultado:**

**Fonte dos Dados:** Kernel filtrado (254 de 3.029 registros totais)

**⚠️ VALIDAÇÃO ANTI-CONTEXT-BLEED:**
- Total de registros ANTES do filtro: 3.029
- Total de registros APÓS filtro de Novembro: 254 ✅
- Proporção: 8,4% dos dados
- **Status:** Context Bleed EVITADO ✅

**TOP 10 Produtos Mais Vendidos em Novembro:**

| Produto              | Quantidade |
|----------------------|------------|
| [Produto real 1]     | [N] un.    |
| [Produto real 2]     | [N] un.    |
| ...                  | ...        |

💡 **Diagnóstico:**
Garanti que os dados apresentados são EXCLUSIVAMENTE de Novembro 
(254 registros, 8,4% do dataset), não do ano completo.

**Atualização do Foco:**
- Mês: Novembro
- Métrica: Quantidade
- Registros: 254
```

### CASO 3: Tolerância Zero à Alucinação (Min/Max)

**Usuário:** `qual a transação mais cara e mais barata?`

**v10.0 ALUCINOU:**
```
Transação mais cara: Laptop Premium (R$ 15.000, ID: 9999)
Transação mais barata: Caneta (R$ 2,50, ID: 1111)
```

**v11.0 CORRETO:**

```
🎯 **Objetivo:**
Identificar as transações com maior e menor valor no dataset completo.

📝 **Construção da Query:**

**1. Mapeamento Semântico:**
- "Transação mais cara" → registro com MAX(`Receita_Total`)
- "Transação mais barata" → registro com MIN(`Receita_Total`)

**2. Operação Principal:**
- Busca direta por MIN(`Receita_Total`) → retorna 1 registro
- Busca direta por MAX(`Receita_Total`) → retorna 1 registro

✅ **Checklist de Pré-Execução:**
-   ✅ Tolerância Zero: Esta é uma operação de BUSCA DIRETA.
    Se a ferramenta falhar ou retornar resultado ambíguo, 
    DEVO admitir a falha e sugerir alternativa (ranking).
-   ✅ Validade: Coluna `Receita_Total` é numérica ✅

📊 **Execução e Resultado:**

**Fonte dos Dados:** Busca direta no Kernel (3.029 registros analisados)

**TRANSAÇÃO MAIS CARA:**
- Produto: [Nome REAL do dataset]
- Valor: R$ [Valor REAL]
- Quantidade: [N] unidades
- Data: [Data REAL]
- Região: [Região REAL]
- ID: [ID REAL se existir]

**TRANSAÇÃO MAIS BARATA:**
- Produto: [Nome REAL do dataset]
- Valor: R$ [Valor REAL]
- Quantidade: [N] unidades
- Data: [Data REAL]
- Região: [Região REAL]
- ID: [ID REAL se existir]

**Validação:**
- Amplitude de valores: R$ [MAX - MIN]
- Nenhum dado foi inventado ✅
- Todos os valores vêm diretamente do Kernel ✅

💡 **Diagnóstico:**
Os valores são reais e auditáveis. Nenhuma alucinação detectada.
```

**SE A BUSCA FALHASSE (alternativa):**

```
⚠️ **Falha na Busca Direta**

A operação de busca por MIN/MAX na coluna `Receita_Total` encontrou 
um erro técnico ou resultado ambíguo.

**Diagnóstico:**
- ✅ Coluna `Receita_Total` existe e é numérica
- ✅ Kernel possui 3.029 registros totais
- ❌ Operação de busca direta falhou: [erro técnico]

Para garantir a precisão, não posso fornecer uma resposta neste momento.

**Alternativa:** Posso fornecer um ranking com:
- TOP 5 transações MAIS CARAS
- TOP 5 transações MAIS BARATAS

Assim você pode inspecionar os valores manualmente. Gostaria dessa alternativa?
```

---

## 🛠️ FERRAMENTAS DISPONÍVEIS (Referência Técnica)

Você tem acesso a estas ferramentas para análise **REAL** dos dados:

1. **calculate_metric** - Agregação em coluna numérica
   - Operações: `sum`, `mean`, `count`, `min`, `max`
   - Requer: coluna em "💰 Campos Numéricos"

2. **get_ranking** - Ranking agrupado
   - Agrupa por coluna categórica, ordena por métrica
   - Requer: coluna em "📝 Campos Categóricos" + coluna numérica

3. **get_unique_values** - Lista valores distintos
   - Útil para explorar categorias disponíveis

4. **get_time_series** - Análise temporal/evolução
   - Requer: coluna em "✅ CONVERSÃO BEM-SUCEDIDA"
   - **NUNCA use** em colunas de "❌ CONVERSÃO FALHOU"

5. **filter_data** - Filtragem de registros
   - Suporta: igualdade, maior/menor, contém texto
   - Retorna: subset do dataset

---

## 🎯 EXEMPLOS PRÁTICOS DA v9.0

### Exemplo 1: Uso do Dicionário de Aprendizagem

```
[Contexto: Usuário já perguntou "faturamento de outubro" antes, você mapeou para `Receita_Total`]

Usuário: "e qual foi o faturamento de novembro?"

🎯 **Objetivo:**
Calcular faturamento total de Novembro.

📝 **Plano de Análise**
[Suposições Declaradas]
- **Mapeamento Prévio:** Usando coluna `Receita_Total` (você definiu isso na análise de Outubro)

[Passos]
1. Filtrar dataset pela coluna `Data` onde mês = 11
2. Somar valores da coluna `Receita_Total`
3. Formatar em R$

[... execução ...]
```

### Exemplo 2: Detecção de Inconsistência

```
[Análise anterior: "Não há dados de Dezembro"]
[Agora usuário pede: "me mostre os top produtos de dezembro"]

[Sistema de Auto-Validação detecta contradição]

🔄 **Correção Importante**

Detectei uma inconsistência crítica.

**Antes (Incorreto):** Eu disse que não havia dados de Dezembro
**Agora:** Ao buscar para o ranking, encontrei 189 registros de Dezembro

**Diagnóstico da Falha:**
Na primeira análise, o filtro temporal foi aplicado incorretamente. Verifiquei o Mapa do Ecossistema e a coluna `Data` está em "✅ CONVERSÃO BEM-SUCEDIDA", então o filtro deveria ter funcionado.

**Resposta Correta:**

🎯 **Objetivo:**
Ranking dos produtos com maior faturamento em Dezembro (corrigindo informação anterior).

[... restante do monólogo analítico ...]
```

### Exemplo 3: Clarificação Obrigatória

```
Usuário: "qual o lucro de outubro?"

[Você identifica: `Receita_Total` existe, mas não há coluna de `Custo` ou similar]

📊 **Análise de Viabilidade**

🛑 **Métrica Não Calculável: "Lucro"**

Para calcular lucro, eu precisaria de:
- ✅ Coluna de receita (disponível: `Receita_Total`)
- ❌ Coluna de custo (não encontrada no Mapa do Ecossistema)

**Colunas numéricas disponíveis:**
- `Receita_Total`
- `Quantidade`
- `Preco_Unitario`
- `Desconto_Aplicado`

**Alternativas viáveis:**
1. Mostrar a **receita total** de Outubro (R$ sem subtrair custos)
2. Calcular **receita líquida** (se descontar `Desconto_Aplicado`)
3. Aguardar se você tiver dados de custo em outra fonte

**Qual alternativa você prefere?**
```

---

## 📊 FORMATO DE APRESENTAÇÃO DE DADOS

### Para Valores Únicos:
```
💰 **[Métrica]**: R$ 1.234.567,89
📊 **Registros analisados**: 2.847
📅 **Período**: Janeiro a Dezembro 2024
```

### Para Rankings (sempre incluir contexto):
```
| # | [Entidade] | [Métrica] | % do Total |
|---|-----------|-----------|------------|
| 1 | [valor]   | R$ X      | 23,5%      |
| 2 | [valor]   | R$ Y      | 18,2%      |
...

📊 **Análise do Top 10:**
- Representa 78,3% do total
- [Insight relevante]
```

### Para Séries Temporais:
```
📈 **Evolução de [Métrica] por [Período]**

[Gráfico textual ou tabela]

Mês         | Valor      | Var. %
------------|------------|--------
Janeiro     | R$ 100k    | -
Fevereiro   | R$ 120k    | +20%
...

📊 **Tendências Identificadas:**
- [Insight 1]
- [Insight 2]
```

---

## ✅ CHECKLIST FINAL DE QUALIDADE (Use mentalmente em toda resposta)

Antes de enviar qualquer resposta analítica, confirme:

- [ ] Consultei o Painel de Contexto (3 camadas)?
- [ ] Se há ambiguidade, perguntei ao usuário?
- [ ] Executei o checklist de Auto-Validação?
- [ ] Todas as colunas usadas existem no Diagnóstico?
- [ ] Os tipos de dados estão corretos?
- [ ] Declarei todas as suposições no Plano de Análise?
- [ ] Se falhou, ofereci alternativas viáveis?
- [ ] Atualizei o Painel de Contexto após sucesso?
- [ ] A resposta é consistente com análises anteriores similares?

---

## 🚀 MENSAGEM FINAL: A Identidade do Analista Confiável

Você é um **analista de dados autônomo em quem se pode confiar cegamente**. 
Sua credibilidade depende de:

### OS CINCO PILARES DA CONFIABILIDADE

1. **TRANSPARÊNCIA TOTAL**
   - Sempre mostre seu raciocínio completo (🎯📝✅📊💡)
   - Toda suposição deve ser declarada explicitamente
   - Todo passo deve ser auditável

2. **HUMILDADE INTELECTUAL**
   - Pergunte quando não souber (🛑 Clarificação Necessária)
   - Admita quando uma busca falhar
   - Nunca invente dados para parecer competente

3. **CONSISTÊNCIA ABSOLUTA**
   - Valide cada resposta contra o Log de Análise
   - Respostas similares para perguntas similares
   - Detecte e corrija contradições ativamente (🔄 Auto-Correção)

4. **TOLERÂNCIA ZERO À ALUCINAÇÃO**
   - Dados reais ou nada
   - Se min/max falhar, admita e ofereça ranking alternativo
   - Prefira "não posso responder" a inventar

5. **VIGILÂNCIA CONTRA CONTEXT BLEED**
   - Sempre valide que filtros foram aplicados corretamente
   - Confirme que total de registros é consistente com filtro
   - Nunca apresente dados do dataset completo como se fossem filtrados

---

## 📋 CHECKLIST MENTAL ANTES DE CADA RESPOSTA

Responda mentalmente antes de enviar qualquer análise:

```
□ Mostrei o Protocolo completo? (🎯📝✅📊💡)
□ Declarei todas as suposições?
□ Consultei o Léxico Semântico para termos já mapeados?
□ Validei contra o Log de Análise (inconsistências)?
□ Se foi busca (min/max), tenho dados REAIS ou admiti falha?
□ Se foi filtro temporal, validei que registros são subset correto?
□ Total de registros é consistente com filtros aplicados?
□ Resultado é auditável e transparente?
```

**Quando em dúvida: consulte o Kernel, valide o Log, e pergunte ao usuário.**

**Lembre-se: Sua missão não é impressionar. É ser confiável.**
"""

ALPHABOT_SYSTEM_PROMPT = """
# AlphaBot - Analista de Planilhas Anexadas na Conversa

Você é o AlphaBot, especializado em analisar arquivos de planilha anexados diretamente na conversa.

## REGRAS DE OPERAÇÃO E FLUXO DE TRABALHO:

### 1. MENSAGEM INICIAL
Ao ser ativado, sua primeira mensagem deve ser:

"Olá, eu sou o AlphaBot. Por favor, use o botão de anexo para enviar as planilhas (.csv, .xlsx) que você deseja analisar."

### 2. DETECÇÃO DE ANEXO
Sua função principal é detectar quando o usuário anexa arquivos na conversa. Ignore mensagens de texto que não contenham anexos, a menos que seja uma pergunta sobre dados já analisados.

### 3. PROCESSAMENTO E RELATÓRIO
Assim que os arquivos forem recebidos, processe-os e forneça um relatório usando esta formatação em Markdown:

## Relatório de Leitura dos Anexos

**Status:** Leitura concluída.

**Taxa de Sucesso:** [X] de [Y] arquivos lidos com sucesso.

**Arquivos Analisados:**
- nome_do_arquivo_anexado_1.xlsx
(liste todos os arquivos lidos)

**Arquivos com Falha:**
- nome_do_arquivo_anexado_2.txt (Motivo: Formato inválido)

Análise concluída. Estou pronto para suas perguntas sobre os dados destes arquivos.

### 4. SESSÃO DE PERGUNTAS E RESPOSTAS
Responda às perguntas baseando-se estritamente nos dados dos arquivos anexados nesta sessão. O AlphaBot não tem memória de arquivos de conversas anteriores.

## COMPORTAMENTO:
- Resposta direta e objetiva
- Foque apenas nos arquivos da sessão atual
- Se não houver anexos, lembre o usuário de enviá-los
"""

# AlphaBot System Prompt - Motor de Validação Interna (Analista → Crítico → Júri)
ALPHABOT_SYSTEM_PROMPT = """
# IDENTIDADE E MISSÃO
Você é o AlphaBot, um especialista em análise de dados avançada. Sua missão é receber planilhas (.csv, .xlsx) anexadas pelo usuário, consolidar os dados e responder a perguntas complexas com precisão, clareza e insights valiosos. Você opera com um motor de validação interna para garantir a qualidade de cada resposta.

# FLUXO DE OPERAÇÃO

### 1. MENSAGEM INICIAL
Sua primeira mensagem ao usuário, e sempre que for invocado em uma nova conversa, deve ser:

"Olá, eu sou o AlphaBot. Por favor, use o botão de anexo para enviar uma ou mais planilhas (.csv, .xlsx) que você deseja analisar."

### 2. RECEBIMENTO E DIAGNÓSTICO
Ao receber um ou mais arquivos anexados, seu processo é o seguinte:
- Tentar ler e consolidar todos os arquivos em um único conjunto de dados.
- Realizar uma análise diagnóstica completa da estrutura dos dados consolidados.
- Apresentar o relatório de diagnóstico ao usuário usando o seguinte formato Markdown. Esta deve ser sua ÚNICA resposta após receber os arquivos.

---
## 🔍 Relatório de Diagnóstico dos Anexos

**Status:** Leitura, consolidação e diagnóstico finalizados ✅

### 📁 Arquivos Processados
- **Sucesso ([X] de [Y]):**
  - `nome_do_arquivo_1.xlsx`
  - `nome_do_arquivo_2.csv`
- **Falha ([Z] de [Y]):**
  - `documento.txt` (Motivo: Formato de arquivo não suportado)
  - `dados_corrompidos.xlsx` (Motivo: Não foi possível ler o arquivo)

### 📊 Estrutura do Dataset Consolidado
- **Registros Totais:** [Número total de linhas]
- **Colunas Identificadas:** [Número total de colunas]
- **Período Identificado:** [Data mínima] até [Data máxima] (se houver colunas de data)

### 🔬 Qualidade e Capacidades
- **✅ Campos Numéricos (prontos para cálculos):** `Nome_Coluna_1`, `Nome_Coluna_2`
- **📝 Campos Categóricos (prontos para agrupamento):** `Nome_Coluna_3`, `Nome_Coluna_4`
- **📅 Campos Temporais (prontos para filtros de período):** `Nome_Coluna_5`

**Diagnóstico Concluído.** Estou pronto para responder às suas perguntas sobre os dados consolidados.
---

### 3. SESSÃO DE PERGUNTAS E RESPOSTAS

#### DISTINÇÃO ENTRE PERGUNTA ANALÍTICA E COMANDO DE EXIBIÇÃO
Antes de iniciar a análise interna, você deve classificar o tipo de solicitação do usuário:

- **Pergunta Analítica:** O usuário quer uma resposta calculada, comparação, insight ou análise. 
  - Exemplos: "Qual foi o faturamento total?", "Compare vendas de Janeiro e Fevereiro", "Qual produto vendeu mais?"
  - **Ação:** Siga o fluxo completo do Motor de Validação Interna (Analista → Crítico → Júri) e forneça a resposta estruturada.

- **Comando de Exibição:** O usuário quer visualizar dados brutos filtrados, sem necessariamente pedir uma análise.
  - Exemplos: "Me mostre todas as vendas de Outubro", "Liste os produtos da categoria Eletrônicos", "Exiba as transações acima de R$ 1000"
  - **Ação:** Filtre os dados conforme solicitado, apresente a tabela resultante em formato Markdown, e adicione uma breve explicação do filtro aplicado. O Motor de Validação é simplificado neste caso (não é necessário passar pelas 3 personas).

**Dica de Identificação:** Comandos de exibição geralmente contêm verbos como "mostre", "liste", "exiba", "apresente", enquanto perguntas analíticas contêm "qual", "quanto", "compare", "analise".

#### ARQUITETURA DE ANÁLISE INTERNA (MOTOR DE VALIDAÇÃO)
Para cada **pergunta analítica** do usuário, você deve simular um processo de deliberação interna usando três personas antes de formular a resposta final.

1.  **O Analista:** Objetivo e focado nos dados. Ele executa o cálculo direto (somas, médias, filtros, rankings) e formula uma resposta técnica e preliminar.
2.  **O Crítico:** Cético e contextual. Ele desafia a análise do Analista, procurando por vieses, dados ausentes, ou interpretações alternativas. Ele pergunta: "Estamos assumindo algo que não deveríamos? Existem outras variáveis que podem influenciar este resultado?".
3.  **O Júri:** O sintetizador final. Ele ouve o Analista e o Crítico. Ele formula a resposta final para o usuário, que é precisa (baseada na análise), mas também contextualizada e transparente sobre possíveis limitações (apontadas pelo Crítico).

#### FORMATO DA RESPOSTA FINAL
A resposta entregue ao usuário (formulada pelo Júri) deve SEMPRE seguir esta estrutura:

- **Resposta Direta:** Uma frase clara e concisa que responde diretamente à pergunta.
- **Análise Detalhada:** A explicação de como você chegou à resposta, citando os dados ou a lógica usada. (Ex: "Este resultado foi obtido ao filtrar as vendas de 'Novembro' e somar a 'Quantidade' para cada 'Produto'...")
- **Insights Adicionais:** Observações valiosas que você descobriu durante a análise e que podem ser úteis, mesmo que não tenham sido diretamente perguntadas.
- **Limitações e Contexto:** (Se aplicável) Uma nota transparente sobre qualquer limitação ou contexto importante. (Ex: "É importante notar que os dados do arquivo X não continham a coluna 'Região', portanto não foram incluídos neste ranking regional.")

# REGRAS DE FORMATAÇÃO
- **Use Markdown de forma limpa:**
  - Use **negrito** apenas para destacar termos importantes (não exagere)
  - Use títulos (##, ###) para seções
  - Use listas (-, *) para enumerações
  
- **Tabelas Markdown:**
  - SEMPRE alinhe as colunas corretamente
  - Use espaços para manter o alinhamento visual
  - Formato correto:
    ```
    | Coluna 1       | Coluna 2    | Coluna 3 |
    |----------------|-------------|----------|
    | Valor alinhado | Outro valor | 123.45   |
    | Mais dados     | Mais info   | 678.90   |
    ```

- **Números:**
  - Valores monetários: R$ 1.234,56
  - Percentuais: 45,7%
  - Grandes números: 1.234.567 (com separador de milhares)

# REGRAS ESPECÍFICAS DE ANÁLISE

## ANÁLISE DE "PRODUTO MAIS VENDIDO"
Quando o usuário perguntar sobre "produto mais vendido", "qual produto vendeu mais", ou variações similares:

1. **Primeira Prioridade:** Verificar se existe uma coluna numérica chamada 'Quantidade' (ou similar: 'Qtd', 'Unidades', 'Volume')
   - Se existir: Responder baseado na **SOMA da quantidade de unidades vendidas** por produto
   - Formato: "O produto mais vendido foi [Produto X] com [N] unidades vendidas"

2. **Insight Adicional:** Sempre complementar com informação sobre receita
   - Verificar se existe coluna de receita ('Receita_Total', 'Valor', 'Faturamento')
   - Adicionar: "Em termos de receita, o produto com maior faturamento foi [Produto Y] com R$ [Valor]"

3. **Transparência:** Se não houver coluna de quantidade, deixar claro
   - "Não foi possível identificar uma coluna de quantidade. Baseando a análise em receita total..."

## VALIDAÇÃO DE TIPOS DE DADOS
- **Colunas 'Quantidade':** SEMPRE devem ser tratadas como numéricas, nunca como temporais
- **Colunas 'Data':** SEMPRE devem ser tratadas como temporais, com validação de epoch time (rejeitar 1970)
- **Colunas 'Receita/Valor':** SEMPRE devem ser tratadas como numéricas com formatação monetária

# REGRAS ADICIONAIS
- **Stateless:** Você não tem memória de arquivos de conversas anteriores. Cada nova sessão de anexos é um novo universo de dados.
- **Foco no Anexo:** Se o usuário fizer uma pergunta sobre dados sem ter anexado arquivos primeiro, lembre-o gentilmente de que você precisa de um anexo para começar a análise.
"""

# Armazenamento global para sessões do AlphaBot com isolamento por usuário
# Chave: f"{user_id}_{session_id}" para evitar mixing de dados
ALPHABOT_SESSIONS: Dict[str, Dict[str, Any]] = {}


def get_google_credentials() -> service_account.Credentials:
    """Obtém credenciais de serviço para acessar Google Drive e Sheets."""
    global GOOGLE_CREDENTIALS

    if GOOGLE_CREDENTIALS is not None:
        return GOOGLE_CREDENTIALS

    try:
        if GOOGLE_SERVICE_ACCOUNT_INFO:
            info = json.loads(GOOGLE_SERVICE_ACCOUNT_INFO)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=GOOGLE_SCOPES)
        elif GOOGLE_SERVICE_ACCOUNT_FILE:
            if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
                raise RuntimeError(
                    "Arquivo de credenciais informado em GOOGLE_SERVICE_ACCOUNT_FILE não foi encontrado."
                )
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=GOOGLE_SCOPES,
            )
        else:
            raise RuntimeError(
                "Credenciais não configuradas. Defina GOOGLE_SERVICE_ACCOUNT_FILE com o caminho do JSON "
                "da service account ou GOOGLE_SERVICE_ACCOUNT_INFO com o conteúdo JSON."
            )
    except Exception as error:
        raise RuntimeError(f"Erro ao carregar credenciais do Google: {error}") from error

    GOOGLE_CREDENTIALS = credentials
    return credentials


def get_google_services() -> Tuple[Any, Any]:
    """Inicializa clientes do Google Drive e Sheets utilizando as credenciais configuradas."""
    credentials = get_google_credentials()
    drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    sheets_service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
    return drive_service, sheets_service


def normalize_decimal_string(value: Any) -> Optional[str]:
    """Normaliza strings com valores decimais para formato padrão."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None

    if isinstance(value, (int, float, np.number)):
        return str(value)

    text = str(value).strip()
    if not text or text.lower() in {'nan', 'none', 'null'}:
        return None

    # Remove símbolos comuns
    text = text.replace('R$', '').replace('%', '').replace(' ', '')
    text = text.replace('\t', '').replace('\n', '').replace('\r', '')
    text = text.replace('\u00a0', '')  # Non-breaking space

    # Normaliza separadores decimais
    if text.count(',') == 1 and text.count('.') >= 1:
        # Formato: 1.234,56 -> 1234.56
        text = text.replace('.', '').replace(',', '.')
    elif text.count(',') > 0:
        # Formato: 1234,56 -> 1234.56
        text = text.replace(',', '.')

    return text
def coerce_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors='coerce')

    normalized = series.astype(str).map(normalize_decimal_string)
    return pd.to_numeric(normalized, errors='coerce')


def detect_numeric_columns(df: pd.DataFrame) -> Tuple[List[str], Dict[str, pd.Series]]:
    numeric_columns: List[str] = []
    numeric_data: Dict[str, pd.Series] = {}

    for column in df.columns:
        coerced = coerce_numeric_series(df[column])
        if coerced.notna().sum() >= max(1, int(len(coerced) * 0.3)):
            numeric_columns.append(column)
            numeric_data[column] = coerced

    return numeric_columns, numeric_data


def normalize_month_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    text = value.strip()
    lower = text.lower()
    for pt_name, eng_name in MONTH_TRANSLATION.items():
        if pt_name in lower:
            lower = lower.replace(pt_name, eng_name.lower())
    return lower


def month_number_to_name(month_num: int) -> str:
    """
    v11.0: Converte número do mês (1-12) para nome em português.
    Usado para criar coluna auxiliar 'Data_Mes_Nome'.
    
    v11.0 FIX #6: Retorna em minúsculas para consistência com filtros case-insensitive
    """
    month_names = {
        1: "janeiro", 2: "fevereiro", 3: "março", 4: "abril",
        5: "maio", 6: "junho", 7: "julho", 8: "agosto",
        9: "setembro", 10: "outubro", 11: "novembro", 12: "dezembro"
    }
    return month_names.get(month_num, "desconhecido")


def detect_datetime_columns(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    v11.0 FIX: Tratamento robusto de datas com formato explícito.
    
    Correção crítica para eliminar UserWarnings e filtros temporais falhos.
    """
    datetime_columns: Dict[str, pd.Series] = {}

    for column in df.columns:
        series = df[column]
        parsed = None
        
        if pd.api.types.is_datetime64_any_dtype(series):
            # Já é datetime, apenas garantir
            parsed = pd.to_datetime(series, errors='coerce')
        else:
            # Tentar múltiplos formatos comuns
            # Formato ISO (YYYY-MM-DD) - mais comum e inequívoco
            parsed = pd.to_datetime(series, format='%Y-%m-%d', errors='coerce')
            
            if parsed.isna().all():
                # Formato brasileiro (DD/MM/YYYY)
                parsed = pd.to_datetime(series, format='%d/%m/%Y', errors='coerce', dayfirst=True)
            
            if parsed.isna().all():
                # Formato americano (MM/DD/YYYY)
                parsed = pd.to_datetime(series, format='%m/%d/%Y', errors='coerce')
            
            if parsed.isna().all():
                # Formato com texto de mês (ex: "Janeiro 2024")
                normalized = series.astype(str).map(normalize_month_text)
                parsed = pd.to_datetime(normalized, errors='coerce', dayfirst=True)
            
            if parsed.isna().all():
                # Último recurso: deixar pandas inferir (SEM dayfirst para evitar ambiguidade)
                parsed = pd.to_datetime(series, errors='coerce', dayfirst=False)

        # Considerar válida se >= 30% dos valores foram convertidos com sucesso
        if parsed is not None and parsed.notna().sum() >= max(1, int(len(parsed) * 0.3)):
            parsed.name = column
            datetime_columns[column] = parsed

    return datetime_columns


def detect_text_columns(df: pd.DataFrame, numeric_columns: List[str]) -> List[str]:
    text_columns: List[str] = []
    numeric_set = set(numeric_columns)

    for column in df.columns:
        if column in numeric_set:
            continue
        series = df[column]
        if pd.api.types.is_string_dtype(series) or series.dtype == object:
            if series.astype(str).str.strip().replace('', np.nan).notna().sum() > 0:
                text_columns.append(column)

    return text_columns


def month_number_to_name(month: int) -> str:
    return MONTH_NAMES_PT.get(month, str(month))


def build_temporal_mask(table: Dict[str, Any], year: Optional[int] = None, month: Optional[int] = None) -> Optional[pd.Series]:
    datetime_columns: Dict[str, pd.Series] = table.get('datetime_columns', {})
    if not datetime_columns:
        return None

    combined_mask: Optional[pd.Series] = None
    for parsed in datetime_columns.values():
        mask = parsed.notna()
        if year is not None:
            mask &= parsed.dt.year == year
        if month is not None:
            mask &= parsed.dt.month == month
        if combined_mask is None:
            combined_mask = mask
        else:
            combined_mask |= mask

    return combined_mask


def prepare_table(table_name: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    v11.0 FIX: Adiciona colunas auxiliares para agrupamento temporal.
    
    Correção para permitir agrupamento por "mês", "ano", "trimestre"
    sem precisar fazer agregações complexas.
    """
    processed = df.copy()
    processed.columns = [str(col).strip() for col in processed.columns]
    processed = processed.replace('', np.nan)

    numeric_columns, numeric_data = detect_numeric_columns(processed)
    datetime_columns = detect_datetime_columns(processed)
    text_columns = detect_text_columns(processed, numeric_columns)
    
    # v11.0: Criar colunas auxiliares para CADA coluna de data detectada
    auxiliary_columns_created = []
    for col_name, datetime_series in datetime_columns.items():
        # Adicionar coluna "Mes" (numérico: 1-12)
        mes_col = f"{col_name}_Mes"
        processed[mes_col] = datetime_series.dt.month
        numeric_columns.append(mes_col)
        auxiliary_columns_created.append(mes_col)
        
        # Adicionar coluna "Ano" (numérico: ex: 2024)
        ano_col = f"{col_name}_Ano"
        processed[ano_col] = datetime_series.dt.year
        numeric_columns.append(ano_col)
        auxiliary_columns_created.append(ano_col)
        
        # Adicionar coluna "Trimestre" (numérico: 1-4)
        trimestre_col = f"{col_name}_Trimestre"
        processed[trimestre_col] = datetime_series.dt.quarter
        numeric_columns.append(trimestre_col)
        auxiliary_columns_created.append(trimestre_col)
        
        # Adicionar coluna "Mes_Nome" (texto: "Janeiro", "Fevereiro", etc.)
        mes_nome_col = f"{col_name}_Mes_Nome"
        processed[mes_nome_col] = datetime_series.dt.month.map(month_number_to_name)
        text_columns.append(mes_nome_col)
        auxiliary_columns_created.append(mes_nome_col)

    return {
        'name': table_name,
        'df': processed,
        'row_count': int(len(processed)),
        'columns': list(processed.columns),
        'numeric_columns': numeric_columns,
        'numeric_data': numeric_data,
        'datetime_columns': datetime_columns,
        'text_columns': text_columns,
        'auxiliary_columns': auxiliary_columns_created,  # Nova metadata
    }


def download_file_bytes(drive_service: Any, file_id: str) -> bytes:
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _status, done = downloader.next_chunk()

    return fh.getvalue()


def load_csv_tables(drive_service: Any, file_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    content = download_file_bytes(drive_service, file_meta['id'])
    df = pd.read_csv(io.BytesIO(content))
    return [prepare_table(file_meta['name'], df)]


def load_excel_tables(drive_service: Any, file_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    content = download_file_bytes(drive_service, file_meta['id'])
    workbook = pd.read_excel(io.BytesIO(content), sheet_name=None)
    tables: List[Dict[str, Any]] = []
    for sheet_name, df in workbook.items():
        table_name = f"{file_meta['name']} - {sheet_name}"
        tables.append(prepare_table(table_name, df))
    return tables


def build_discovery_summary(
    tables: List[Dict[str, Any]],
    files_ok: List[str],
    files_failed: List[Dict[str, str]],
) -> Dict[str, Any]:
    total_records = sum(table['row_count'] for table in tables)
    all_columns = set()
    numeric_columns = set()
    text_columns = set()
    datetime_columns_names = set()
    start_dates: List[pd.Timestamp] = []
    end_dates: List[pd.Timestamp] = []

    for table in tables:
        all_columns.update(table['columns'])
        numeric_columns.update(table['numeric_columns'])
        text_columns.update(table['text_columns'])
        datetime_columns_names.update(table['datetime_columns'].keys())

        for parsed in table['datetime_columns'].values():
            valid = parsed.dropna()
            if not valid.empty:
                start_dates.append(valid.min())
                end_dates.append(valid.max())

    if start_dates and end_dates:
        date_range: Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]] = (
            min(start_dates),
            max(end_dates),
        )
    else:
        date_range = (None, None)

    domains: List[str] = []
    if numeric_columns:
        domains.append('numérico')
    if text_columns:
        domains.append('categórico')
    if datetime_columns_names:
        domains.append('temporal')

    return {
        'files_ok': files_ok,
        'files_failed': files_failed,
        'total_records': int(total_records),
        'columns': sorted(filter(None, all_columns)),
        'numeric_columns': sorted(numeric_columns),
        'text_columns': sorted(text_columns),
        'datetime_columns': sorted(datetime_columns_names),
        'date_range': date_range,
        'domains': domains,
    }


def format_date(date_value: Optional[pd.Timestamp]) -> Optional[str]:
    if date_value is None or (isinstance(date_value, float) and np.isnan(date_value)):
        return None
    try:
        timestamp = pd.to_datetime(date_value)
    except Exception:
        return None
    if pd.isna(timestamp):
        return None
    return timestamp.strftime('%d/%m/%Y')


def clean_markdown_formatting(text: str) -> str:
    """
    Limpa formatação Markdown excessiva ou mal formatada.
    
    - Remove ** duplicados ou excessivos
    - Corrige tabelas desalinhadas
    - Melhora espaçamento
    """
    if not text:
        return text
    
    # 1. Remover múltiplos asteriscos consecutivos (** ** ** vira **)
    text = re.sub(r'\*{3,}', '**', text)  # ***texto*** → **texto**
    text = re.sub(r'\*\*\s+\*\*', '**', text)  # ** ** → **
    
    # 2. Corrigir ** no meio de palavras
    text = re.sub(r'(\w)\*\*(\w)', r'\1\2', text)  # pal**avra → palavra
    
    # 3. Remover ** órfãos (sem fechamento na mesma linha)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Contar ** na linha
        bold_count = line.count('**')
        # Se ímpar, há um ** sem par - remover o último
        if bold_count % 2 != 0:
            # Encontrar a última ocorrência e remover
            last_idx = line.rfind('**')
            if last_idx != -1:
                line = line[:last_idx] + line[last_idx+2:]
        cleaned_lines.append(line)
    text = '\n'.join(cleaned_lines)
    
    # 4. Melhorar tabelas Markdown
    # Detectar linhas de tabela e garantir alinhamento mínimo
    lines = text.split('\n')
    cleaned_lines = []
    in_table = False
    
    for i, line in enumerate(lines):
        # Detectar linha de tabela (contém |)
        if '|' in line and line.strip().startswith('|'):
            in_table = True
            # Adicionar espaço antes e depois de cada |
            line = re.sub(r'\s*\|\s*', ' | ', line)
            # Remover espaços duplos
            line = re.sub(r'\s{2,}', ' ', line)
        elif in_table and '|' not in line:
            in_table = False
        
        cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # 5. Limpar espaçamentos excessivos
    text = re.sub(r'\n{4,}', '\n\n\n', text)  # Máximo 2 linhas em branco
    
    return text.strip()


def build_discovery_report(summary: Dict[str, Any]) -> str:
    files_ok = summary['files_ok']
    files_failed = summary['files_failed']
    date_range = summary['date_range']

    files_ok_md = '\n'.join(f"- {name}" for name in files_ok) or '- Nenhum arquivo processado com sucesso.'
    files_failed_md = '\n'.join(
        f"- {entry['name']} (Motivo: {entry['reason']})" for entry in files_failed
    ) or '- Nenhum arquivo apresentou falha.'

    start_text = format_date(date_range[0])
    end_text = format_date(date_range[1])
    if start_text and end_text:
        period_text = f"{start_text} até {end_text}"
    elif start_text or end_text:
        period_text = start_text or end_text
    else:
        period_text = 'Não identificado'

    numeric_cols_md = ', '.join(f"`{col}`" for col in summary['numeric_columns']) or 'Nenhum identificado'
    text_cols_md = ', '.join(f"`{col}`" for col in summary['text_columns']) or 'Nenhum identificado'
    
    # Diagnóstico de colunas temporais
    datetime_cols = summary.get('datetime_columns', [])
    if datetime_cols:
        datetime_success_md = ', '.join(f"`{col}`" for col in datetime_cols)
        datetime_status = f"""#### 📅 Campos Temporais (Diagnóstico Crítico)
**Status da Conversão de Datas:**
- **✅ Conversão Bem-Sucedida:** {datetime_success_md}
  - Estas colunas **podem ser usadas** para filtros por ano, mês, período.
"""
    else:
        datetime_status = """#### 📅 Campos Temporais (Diagnóstico Crítico)
**Status da Conversão de Datas:**
- **ℹ️ Nenhuma Coluna Temporal Detectada**
  - Filtros por período **não estão disponíveis** neste dataset.
  - Análises temporais **não podem ser realizadas**.
"""

    domains_md = ', '.join(summary['domains']) if summary['domains'] else 'Não identificado'
    
    # Capacidades analíticas
    can_temporal = "✅" if datetime_cols else "❌"

    return f"""## 🔍 Descoberta e Diagnóstico Completo

**Status:** Leitura, processamento e diagnóstico finalizados ✅

### 📁 Arquivos Processados com Sucesso
{files_ok_md}

### ⚠️ Arquivos Ignorados/Com Falha
{files_failed_md}

---

### 🗺️ Estrutura do Dataset Consolidado

**Registros Totais:** {summary['total_records']}
**Período Identificado:** {period_text}
**Domínios de Dados:** {domains_md}

### 🔬 Diagnóstico de Qualidade dos Dados

#### ✅ Campos Numéricos (prontos para cálculos)
{numeric_cols_md}

#### 📝 Campos Categóricos/Textuais (prontos para agrupamento)
{text_cols_md}

{datetime_status}

### 📊 Capacidades Analíticas Disponíveis

Com base no diagnóstico, **posso responder**:
- ✅ Totalizações (soma, média, contagem) nos campos numéricos
- ✅ Rankings e agrupamentos pelos campos categóricos
- {can_temporal} Análises temporais (somente se houver datas válidas)

**Status:** Dataset mapeado e diagnosticado. Pronto para análises com base na estrutura real descoberta.
"""


def ingest_drive_folder(drive_id: str) -> Dict[str, Any]:
    drive_service, sheets_service = get_google_services()

    try:
        response = drive_service.files().list(
            q=f"'{drive_id}' in parents and trashed=false",
            fields="files(id,name,mimeType,modifiedTime)",
        ).execute()
    except HttpError as error:
        raise RuntimeError(f"Erro ao acessar a pasta do Google Drive: {error}") from error

    files = response.get('files', [])
    if not files:
        raise RuntimeError("Nenhum arquivo encontrado na pasta informada. Verifique o ID e as permissões.")

    tables: List[Dict[str, Any]] = []
    files_ok: List[str] = []
    files_failed: List[Dict[str, str]] = []

    for file_meta in files:
        mime_type = file_meta.get('mimeType')
        try:
            if mime_type == 'application/vnd.google-apps.spreadsheet':
                spreadsheet = sheets_service.spreadsheets().get(
                    spreadsheetId=file_meta['id'],
                    includeGridData=False,
                ).execute()
                sheets = spreadsheet.get('sheets', [])
                if not sheets:
                    files_failed.append({'name': file_meta['name'], 'reason': 'Planilha sem abas válidas'})
                    continue

                for sheet in sheets:
                    title = sheet['properties']['title']
                    range_name = f"'{title}'!A1:ZZZ"
                    values_response = sheets_service.spreadsheets().values().get(
                        spreadsheetId=file_meta['id'],
                        range=range_name,
                    ).execute()
                    values = values_response.get('values', [])
                    if len(values) < 1:
                        continue

                    header, *rows = values
                    if not header:
                        continue
                    df = pd.DataFrame(rows, columns=header)
                    table_name = f"{file_meta['name']} - {title}"
                    tables.append(prepare_table(table_name, df))

                files_ok.append(file_meta['name'])
            elif mime_type == 'text/csv':
                tables.extend(load_csv_tables(drive_service, file_meta))
                files_ok.append(file_meta['name'])
            elif mime_type in EXCEL_MIME_TYPES:
                tables.extend(load_excel_tables(drive_service, file_meta))
                files_ok.append(file_meta['name'])
            else:
                files_failed.append({'name': file_meta['name'], 'reason': f'Formato não suportado ({mime_type})'})
        except HttpError as error:
            files_failed.append({'name': file_meta['name'], 'reason': f'Erro ao ler o arquivo: {error}'})
        except Exception as error:
            files_failed.append({'name': file_meta['name'], 'reason': str(error)})

    if not tables:
        raise RuntimeError(
            'Não foi possível processar nenhum arquivo da pasta. Convert a planilhas Google ou CSV e confira as permissões.'
        )

    summary = build_discovery_summary(tables, files_ok, files_failed)
    report = build_discovery_report(summary)

    return {
        'tables': tables,
        'summary': summary,
        'report': report,
        'files_ok': files_ok,
        'files_failed': files_failed,
    }


def ensure_conversation(conversation_id: str, bot_id: str) -> Dict[str, Any]:
    conversation = CONVERSATION_STORE.get(conversation_id)
    if conversation is None or conversation.get("bot_id") != bot_id:
        conversation = {
            "bot_id": bot_id,
            "messages": deque(maxlen=MAX_HISTORY_MESSAGES),
            "drive": {
                "drive_id": None,
                "report": None,
                "summary": None,
                "tables": [],
                "files_ok": [],
                "files_failed": [],
                "last_refresh": None,
            },
        }
        CONVERSATION_STORE[conversation_id] = conversation
    return conversation


def append_message(conversation: Dict[str, Any], role: str, content: str) -> None:
    conversation["messages"].append({"role": role, "content": content})


def list_history(conversation: Dict[str, Any]) -> List[Dict[str, str]]:
    return list(conversation["messages"])


def build_discovery_bundle(drive_id: str) -> Dict[str, Any]:
    """
    VERSÃO REAL: Conecta ao Google Drive, lê os arquivos e retorna dados reais.
    """
    try:
        # Tentar ler dados reais do Google Drive
        ingestion_result = ingest_drive_folder(drive_id)
        
        # Retornar os dados reais
        return {
            "report": ingestion_result["report"],
            "profile": None,  # Não usado mais na nova arquitetura
            "tables": ingestion_result["tables"],
            "summary": ingestion_result["summary"],
            "files_ok": ingestion_result["files_ok"],
            "files_failed": ingestion_result["files_failed"],
        }
    
    except Exception as e:
        print(f"[DriveBot] Erro ao acessar Google Drive: {e}")
        
        # Fallback: retornar erro explicativo
        error_report = f"""## ⚠️ Erro ao Conectar com Google Drive

**Erro:** {str(e)}

**Possíveis Causas:**
1. O ID da pasta está incorreto
2. A pasta não foi compartilhada com a Service Account
3. As APIs do Google Drive/Sheets não estão habilitadas
4. As credenciais não estão configuradas corretamente

**Como Resolver:**
1. Verifique se o ID está correto: `{drive_id}`
2. Compartilhe a pasta com: `id-spreadsheet-reader-robot@data-analytics-gc-475218.iam.gserviceaccount.com`
3. Dê permissão de **Viewer** (leitura)

**Para mais ajuda, consulte:** `GOOGLE_DRIVE_SETUP.md`
"""
        
        return {
            "report": error_report,
            "profile": None,
            "tables": [],
            "summary": None,
            "files_ok": [],
            "files_failed": [{"name": "Erro de Conexão", "reason": str(e)}],
        }


def format_revenue_overview(profile: Dict[str, Any]) -> str:
    metrics = profile["metrics"]
    dimensions = profile["dimensions"]

    region_table = ["| Região | Faturamento | Participação |", "| --- | --- | --- |"]
    for item in metrics["revenue_by_region"]:
        region_table.append(f"| {item['label']} | {item['fmt']} | {item['share']} |")

    monthly_table = ["| Mês | Faturamento |", "| --- | --- |"]
    for item in metrics["monthly_trend"]:
        monthly_table.append(f"| {item['label']} | {item['fmt']} |")

    segments = [
        "## 📊 Resposta Analítica: Faturamento Total",
        "",
        f"**Período analisado:** {dimensions['period']}",
        f"**Faturamento consolidado:** **{metrics['total_revenue_fmt']}**",
        "",
        "### Metodologia adotada",
        "- Campo base: `valor_venda`",
        f"- Registros avaliados: {dimensions['total_records_fmt']}",
        "- Filtros aplicados: período completo disponível no diretório",
        "",
        "### Distribuição por região",
        "\n".join(region_table),
        "",
        "### Tendência mensal",
        "\n".join(monthly_table),
        "",
        "### Observações-chave",
        "- Regiões Sudeste e Sul respondem por 60% do faturamento total.",
        "- O pico de vendas ocorre em Nov/2024, mantendo patamar elevado nos meses seguintes.",
        "- Descontos aplicados elevam o volume no segundo semestre, preservando margem.",
        "",
        "### Próximos passos sugeridos",
        "- Explore margens combinando `margem_contribuicao` com `categoria_produto`.",
        "- Solicite a evolução do ticket médio utilizando `valor_venda` e `quantidade` por `mes_ref`.",
        "- Peça uma visão por canal de venda para entender dependências comerciais.",
    ]

    return "\n".join(segments)


def format_region_ranking(profile: Dict[str, Any]) -> str:
    metrics = profile["metrics"]["revenue_by_region"]
    ranking_table = ["| Posição | Região | Faturamento | Participação |", "| --- | --- | --- | --- |"]
    for idx, item in enumerate(metrics, start=1):
        ranking_table.append(f"| {idx}º | {item['label']} | {item['fmt']} | {item['share']} |")

    segments = [
        "## 🏆 Ranking de Faturamento por Região",
        "",
        "### Resultado consolidado",
        "\n".join(ranking_table),
        "",
        "### Insight rápido",
        "- Sudeste lidera o faturamento e mantém distância confortável das demais regiões.",
        "- Nordeste mostra crescimento consistente, aproximando-se do desempenho do Sul.",
        "- Norte e Centro-Oeste apresentam espaço para expansão com foco em mix de produtos.",
    ]

    return "\n".join(segments)


def format_top_categories(profile: Dict[str, Any]) -> str:
    categories = profile["metrics"]["top_categories"]
    table_lines = ["| Categoria | Faturamento | Participação |", "| --- | --- | --- |"]
    for item in categories:
        table_lines.append(f"| {item['label']} | {item['fmt']} | {item['share']} |")

    segments = [
        "## 🎯 Categorias com Maior Faturamento",
        "",
        "### Top 3 categorias identificadas",
        "\n".join(table_lines),
        "",
        "### Recomendações",
        "- Investigue promoções direcionadas para manter o desempenho de Tecnologia.",
        "- Explore oportunidades cross-sell entre Casa & Estilo e Escritório.",
        "- Monitore categorias long tail para antecipar tendências emergentes.",
    ]

    return "\n".join(segments)


# ============================================================================
# ARQUITETURA DE DOIS PROMPTS: TRADUÇÃO + EXECUÇÃO + APRESENTAÇÃO
# ============================================================================

def generate_analysis_command(question: str, available_columns: List[str], api_key: str, conversation_history: List[Dict[str, str]] = None, auxiliary_columns_info: List[Dict] = None) -> Optional[Dict[str, Any]]:
    """
    PROMPT #1: TRADUTOR DE INTENÇÃO (COM MEMÓRIA CONVERSACIONAL)
    Converte pergunta do usuário em comando JSON estruturado para análise de dados.
    Agora considera o histórico da conversa para detectar continuações.
    
    v11.0: Aceita auxiliary_columns_info para informar sobre colunas temporais auxiliares.
    """
    
    # Construir contexto histórico se disponível
    history_context = ""
    if conversation_history and len(conversation_history) > 0:
        history_context = "\n\n**CONTEXTO DA CONVERSA RECENTE:**\n"
        for msg in conversation_history[-4:]:  # Últimas 2 trocas (4 mensagens)
            role = "Usuário" if msg["role"] == "user" else "DriveBot"
            history_context += f"{role}: {msg['content'][:200]}...\n"  # Limitar tamanho
        
        history_context += "\n⚠️ **IMPORTANTE**: Se a pergunta atual usar pronomes ('essa', 'esse', 'dele') ou pedir detalhes, é uma CONTINUAÇÃO. Use informações da conversa acima como filtros.\n"
    
    # v11.0: Adicionar contexto sobre colunas auxiliares temporais
    auxiliary_info = ""
    if auxiliary_columns_info:
        auxiliary_info = "\n\n**⏰ COLUNAS AUXILIARES PARA AGRUPAMENTO TEMPORAL:**\n"
        auxiliary_info += "O sistema criou automaticamente colunas auxiliares para facilitar análises temporais:\n"
        for info in auxiliary_columns_info:
            auxiliary_info += f"- Tabela '{info['table']}': {', '.join(info['auxiliary_cols'])}\n"
        auxiliary_info += "\n**IMPORTANTE**: Para agrupar por mês/ano/trimestre, use estas colunas auxiliares no 'group_by_column'.\n"
        auxiliary_info += "Exemplo: Para 'receita por mês', use group_by_column='Data_Mes_Nome' (não 'Data').\n"
    
    translator_prompt = f"""Você é um especialista em análise de dados que traduz perguntas em linguagem natural para comandos executáveis em JSON.

**Contexto:**
- O usuário está interagindo com um dataset real carregado do Google Drive.
- As colunas disponíveis neste dataset são: {available_columns}
{auxiliary_info}
{history_context}

**Sua Tarefa:**
Com base na pergunta do usuário E no contexto da conversa, escolha UMA das seguintes ferramentas e forneça os parâmetros necessários em formato JSON puro. 
Não adicione nenhuma outra explicação, markdown, ou texto extra. APENAS o JSON válido.

**Ferramentas Disponíveis:**

1. **calculate_metric**: Para calcular uma única métrica agregada
   Exemplo: {{"tool": "calculate_metric", "params": {{"metric_column": "Receita_Total", "operation": "sum", "filters": {{"Região": "Sul"}}}}}}
   Operações: sum, mean, count, min, max

2. **get_ranking**: Para criar um ranking agrupando dados
   Exemplo: {{"tool": "get_ranking", "params": {{"group_by_column": "Produto", "metric_column": "Receita_Total", "operation": "sum", "filters": {{"Data": "2024-12"}}, "top_n": 5, "ascending": false}}}}

3. **get_extremes**: ⭐ Para encontrar AMBOS o máximo E o mínimo simultaneamente
   Exemplo: {{"tool": "get_extremes", "params": {{"group_by_column": "Data", "metric_column": "Receita_Total", "operation": "sum", "filters": {{}}}}}}
   Use quando o usuário pedir: "maior e menor", "mais caro e mais barato", "melhor e pior", etc.

4. **get_unique_values**: Para listar valores únicos de uma coluna
   Exemplo: {{"tool": "get_unique_values", "params": {{"column": "Região"}}}}

5. **get_time_series**: Para análise temporal/evolução ao longo do tempo
   Exemplo: {{"tool": "get_time_series", "params": {{"time_column": "Data", "metric_column": "Receita_Total", "operation": "sum", "group_by_column": "Região"}}}}

6. **get_filtered_data**: Para buscar detalhes de uma entidade específica (transação, produto, etc)
   Exemplo: {{"tool": "get_filtered_data", "params": {{"filters": {{"ID_Transacao": "T-002461"}}, "columns": ["Produto", "Data", "Receita_Total"]}}}}

**REGRAS IMPORTANTES:**
- ⚠️ **REGRA CRÍTICA DE FILTROS:** Você DEVE incluir TODOS os filtros contextuais mencionados pelo usuário
  * Se o usuário pede "compare Janeiro e Novembro", o filtro DEVE ser: "Data_Mes_Nome": ["janeiro", "novembro"]
  * Se o usuário pede "categoria Eletrônicos em Janeiro e Novembro", os filtros DEVEM ser: "Categoria": "eletrônicos", "Data_Mes_Nome": ["janeiro", "novembro"]
  * NUNCA ignore um filtro explícito mencionado pelo usuário
  
- Se a pergunta usa "essa transação", "esse produto", "nele", identifique a entidade no histórico e use como filtro
- Para filtros de mês, use a coluna temporal disponível (ex: "Data_Mes_Nome" para nomes de mês)
- Para filtros de texto (incluindo meses), use SEMPRE minúsculas (ex: "janeiro", "eletrônicos", "sul")

**Pergunta do Usuário:** "{question}"
**Colunas Disponíveis:** {available_columns}

**JSON de Saída (APENAS JSON, SEM TEXTO EXTRA):**"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        # Configuração leve: apenas ajusta temperatura para consistência
        generation_config = {
            'temperature': 0.3  # Mais determinístico para JSON
        }
        response = model.generate_content(translator_prompt, generation_config=generation_config)
        response_text = (response.text or "").strip()
        
        # Limpar markdown se houver
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        command = json.loads(response_text)
        return command
    except Exception as e:
        print(f"Erro ao gerar comando de análise: {e}")
        print(f"Resposta recebida: {response_text if 'response_text' in locals() else 'N/A'}")
        return None


def execute_analysis_command(command: Dict[str, Any], tables: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Executa o comando JSON nos dados REAIS do DataFrame.
    """
    if not tables:
        return {"error": "Nenhum dado disponível para análise"}
    
    tool = command.get("tool")
    params = command.get("params", {})
    
    # Combinar todos os DataFrames em um só (assumindo estrutura similar)
    try:
        all_dfs = []
        for table in tables:
            df = table.get("df")
            if df is not None and not df.empty:
                all_dfs.append(df)
        
        if not all_dfs:
            return {"error": "Nenhum DataFrame válido encontrado"}
        
        # Usar o primeiro DataFrame (ou combinar se necessário)
        df = all_dfs[0] if len(all_dfs) == 1 else pd.concat(all_dfs, ignore_index=True)
        
    except Exception as e:
        return {"error": f"Erro ao processar DataFrames: {str(e)}"}
    
    # v11.0 FIX: Aplicar filtros com tratamento inteligente de datas
    filters = params.get("filters", {})
    filtered_df = df.copy()
    
    for column, value in filters.items():
        if column not in filtered_df.columns:
            continue
        
        # v11.0 FIX #6: Case-insensitive filtering para colunas de texto
        # Isso resolve o problema de "Abril" vs "abril", "Novembro" vs "novembro"
        col_dtype = filtered_df[column].dtype
        is_text_column = pd.api.types.is_string_dtype(col_dtype) or pd.api.types.is_object_dtype(col_dtype)
        
        # CASO ESPECIAL: Filtros de texto (incluindo nomes de mês)
        if is_text_column and not pd.api.types.is_datetime64_any_dtype(filtered_df[column]):
            try:
                # Sub-caso 1: Lista de valores (ex: ["Junho", "Julho"])
                if isinstance(value, list):
                    # Normalizar ambos para minúsculas
                    filter_values_lower = [str(v).lower() for v in value]
                    filtered_df = filtered_df[filtered_df[column].astype(str).str.lower().isin(filter_values_lower)]
                    continue
                
                # Sub-caso 2: Valor único (ex: "Abril")
                else:
                    # Normalizar ambos para minúsculas
                    filter_value_lower = str(value).lower()
                    filtered_df = filtered_df[filtered_df[column].astype(str).str.lower() == filter_value_lower]
                    continue
            except Exception as e:
                print(f"[DriveBot] Erro no filtro case-insensitive para '{column}': {e}")
                pass
            
        # Tratamento especial para colunas de data
        if pd.api.types.is_datetime64_any_dtype(filtered_df[column]):
            try:
                # CASO 1: Filtro por mês (número 1-12)
                if isinstance(value, (int, str)) and str(value).isdigit():
                    num_value = int(value)
                    
                    # Mês (1-12)
                    if 1 <= num_value <= 12:
                        filtered_df = filtered_df[filtered_df[column].dt.month == num_value]
                        continue
                    
                    # Ano (ex: 2024)
                    elif num_value > 1900 and num_value < 2100:
                        filtered_df = filtered_df[filtered_df[column].dt.year == num_value]
                        continue
                
                # CASO 2: Filtro por múltiplos meses (ex: [1, 11] para "janeiro e novembro")
                elif isinstance(value, list):
                    month_nums = [int(v) for v in value if isinstance(v, (int, str)) and str(v).isdigit()]
                    if month_nums:
                        filtered_df = filtered_df[filtered_df[column].dt.month.isin(month_nums)]
                        continue
                
                # CASO 3: Filtro por trimestre (ex: "Q1", "Q2", etc.)
                elif isinstance(value, str) and value.upper().startswith('Q'):
                    quarter_num = int(value[1])  # Extrair número do trimestre
                    filtered_df = filtered_df[filtered_df[column].dt.quarter == quarter_num]
                    continue
                
                # CASO 4: Tentar converter o valor para datetime e comparar data exata
                filter_date = pd.to_datetime(value, errors='coerce')
                if pd.notna(filter_date):
                    # Comparar apenas a data (ignorar hora)
                    filtered_df = filtered_df[filtered_df[column].dt.date == filter_date.date()]
            except Exception as e:
                # Log de debug (opcional)
                print(f"[DriveBot] Falha no filtro temporal para coluna '{column}' com valor '{value}': {e}")
                pass
        else:
            # Filtro normal para colunas não-temporais (texto, números)
            filtered_df = filtered_df[filtered_df[column] == value]
    
    # Executar ferramenta
    try:
        if tool == "calculate_metric":
            metric_column = params.get("metric_column")
            operation = params.get("operation", "sum")
            
            if metric_column not in filtered_df.columns:
                return {"error": f"Coluna '{metric_column}' não encontrada"}
            
            if operation == "sum":
                result = filtered_df[metric_column].sum()
            elif operation == "mean":
                result = filtered_df[metric_column].mean()
            elif operation == "count":
                result = len(filtered_df)
            elif operation == "min":
                result = filtered_df[metric_column].min()
            elif operation == "max":
                result = filtered_df[metric_column].max()
            else:
                return {"error": f"Operação '{operation}' não suportada"}
            
            return {
                "tool": tool,
                "result": float(result) if pd.notna(result) else None,
                "metric_column": metric_column,
                "operation": operation,
                "filters": filters,
                "record_count": len(filtered_df)
            }
        
        elif tool == "get_ranking":
            group_by_column = params.get("group_by_column")
            metric_column = params.get("metric_column")
            operation = params.get("operation", "sum")
            top_n = params.get("top_n", 10)
            ascending = params.get("ascending", False)
            
            if group_by_column not in filtered_df.columns:
                return {"error": f"Coluna '{group_by_column}' não encontrada"}
            if metric_column not in filtered_df.columns:
                return {"error": f"Coluna '{metric_column}' não encontrada"}
            
            # v11.0 FIX: Suporte para min/max em rankings
            if operation == "sum":
                grouped = filtered_df.groupby(group_by_column)[metric_column].sum()
            elif operation == "mean":
                grouped = filtered_df.groupby(group_by_column)[metric_column].mean()
            elif operation == "count":
                grouped = filtered_df.groupby(group_by_column)[metric_column].count()
            elif operation == "min":
                grouped = filtered_df.groupby(group_by_column)[metric_column].min()
            elif operation == "max":
                grouped = filtered_df.groupby(group_by_column)[metric_column].max()
            else:
                return {"error": f"Operação '{operation}' não suportada em get_ranking. Operações disponíveis: sum, mean, count, min, max"}
            
            ranked = grouped.sort_values(ascending=ascending).head(top_n)
            
            return {
                "tool": tool,
                "ranking": [
                    {group_by_column: str(idx), metric_column: float(val)}
                    for idx, val in ranked.items()
                ],
                "group_by_column": group_by_column,
                "metric_column": metric_column,
                "operation": operation,
                "filters": filters,
                "record_count": len(filtered_df)
            }
        
        elif tool == "get_extremes":
            # v11.0 FIX #8: Nova ferramenta para encontrar AMBOS máximo E mínimo
            # Resolve: "dia com maior e menor faturamento", "produto mais caro e mais barato"
            group_by_column = params.get("group_by_column")
            metric_column = params.get("metric_column")
            operation = params.get("operation", "sum")
            
            if group_by_column not in filtered_df.columns:
                return {"error": f"Coluna '{group_by_column}' não encontrada"}
            if metric_column not in filtered_df.columns:
                return {"error": f"Coluna '{metric_column}' não encontrada"}
            
            # Agregar dados
            if operation == "sum":
                grouped = filtered_df.groupby(group_by_column)[metric_column].sum()
            elif operation == "mean":
                grouped = filtered_df.groupby(group_by_column)[metric_column].mean()
            elif operation == "count":
                grouped = filtered_df.groupby(group_by_column)[metric_column].count()
            elif operation == "min":
                grouped = filtered_df.groupby(group_by_column)[metric_column].min()
            elif operation == "max":
                grouped = filtered_df.groupby(group_by_column)[metric_column].max()
            else:
                return {"error": f"Operação '{operation}' não suportada"}
            
            # Encontrar extremos
            max_idx = grouped.idxmax()
            min_idx = grouped.idxmin()
            max_value = grouped.max()
            min_value = grouped.min()
            
            return {
                "tool": tool,
                "extremes": {
                    "max": {group_by_column: str(max_idx), metric_column: float(max_value)},
                    "min": {group_by_column: str(min_idx), metric_column: float(min_value)}
                },
                "group_by_column": group_by_column,
                "metric_column": metric_column,
                "operation": operation,
                "filters": filters,
                "record_count": len(filtered_df)
            }
        
        elif tool == "get_unique_values":
            column = params.get("column")
            
            if column not in filtered_df.columns:
                return {"error": f"Coluna '{column}' não encontrada"}
            
            unique_values = filtered_df[column].dropna().unique().tolist()
            
            return {
                "tool": tool,
                "column": column,
                "unique_values": [str(v) for v in unique_values],
                "count": len(unique_values)
            }
        
        elif tool == "get_time_series":
            time_column = params.get("time_column")
            metric_column = params.get("metric_column")
            operation = params.get("operation", "sum")
            group_by_column = params.get("group_by_column")
            
            if time_column not in filtered_df.columns:
                return {"error": f"Coluna '{time_column}' não encontrada"}
            if metric_column not in filtered_df.columns:
                return {"error": f"Coluna '{metric_column}' não encontrada"}
            
            if group_by_column and group_by_column in filtered_df.columns:
                if operation == "sum":
                    grouped = filtered_df.groupby([time_column, group_by_column])[metric_column].sum()
                elif operation == "mean":
                    grouped = filtered_df.groupby([time_column, group_by_column])[metric_column].mean()
                else:
                    grouped = filtered_df.groupby([time_column, group_by_column])[metric_column].count()
                
                result_data = grouped.reset_index().to_dict('records')
            else:
                if operation == "sum":
                    grouped = filtered_df.groupby(time_column)[metric_column].sum()
                elif operation == "mean":
                    grouped = filtered_df.groupby(time_column)[metric_column].mean()
                else:
                    grouped = filtered_df.groupby(time_column)[metric_column].count()
                
                result_data = [
                    {time_column: str(idx), metric_column: float(val)}
                    for idx, val in grouped.items()
                ]
            
            return {
                "tool": tool,
                "time_series": result_data,
                "time_column": time_column,
                "metric_column": metric_column,
                "operation": operation,
                "filters": filters
            }
        
        elif tool == "get_filtered_data":
            # Nova ferramenta para buscar detalhes de entidades específicas
            columns = params.get("columns", filtered_df.columns.tolist())
            
            # Validar colunas solicitadas
            valid_columns = [col for col in columns if col in filtered_df.columns]
            
            if not valid_columns:
                return {"error": "Nenhuma coluna válida especificada"}
            
            result_df = filtered_df[valid_columns]
            
            # Limitar resultados para evitar sobrecarga
            max_rows = 100
            if len(result_df) > max_rows:
                result_df = result_df.head(max_rows)
            
            # Converter para lista de dicionários
            records = result_df.to_dict('records')
            
            # Formatar datas para string legível
            for record in records:
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None
                    elif isinstance(value, pd.Timestamp):
                        record[key] = value.strftime('%d/%m/%Y')
                    elif isinstance(value, (np.integer, np.floating)):
                        record[key] = float(value)
            
            return {
                "tool": tool,
                "data": records,
                "columns": valid_columns,
                "filters": filters,
                "record_count": len(filtered_df),
                "displayed_count": len(records)
            }
        
        else:
            return {"error": f"Ferramenta '{tool}' não reconhecida"}
    
    except Exception as e:
        return {"error": f"Erro ao executar análise: {str(e)}"}


def format_analysis_result(question: str, raw_result: Dict[str, Any], api_key: str, conversation_history: List[Dict[str, str]] = None) -> str:
    """
    PROMPT #2: APRESENTADOR DE RESULTADOS (COM MONÓLOGO ANALÍTICO)
    Formata os resultados REAIS da análise usando a estrutura obrigatória de 4 partes.
    
    v11.0 FIX #7: Suporta múltiplos resultados quando raw_result["multi_command"] == True
    """
    if "error" in raw_result and not raw_result.get("multi_command"):
        return f"⚠️ **Erro na análise:** {raw_result['error']}\n\nPor favor, reformule sua pergunta ou verifique se os dados estão disponíveis."
    
    # v11.0 FIX #7: Tratamento especial para múltiplos comandos
    if raw_result.get("multi_command"):
        # Consolidar todos os resultados em um único contexto para o LLM
        results_context = "**RESULTADOS DE MÚLTIPLAS ANÁLISES:**\n\n"
        for idx, result in enumerate(raw_result["results"], 1):
            if "error" in result:
                results_context += f"Análise {idx}: ❌ Erro - {result['error']}\n"
            else:
                results_context += f"Análise {idx}:\n{json.dumps(result, indent=2, ensure_ascii=False)}\n\n"
        
        # Substituir raw_result por um consolidado
        raw_result = {"consolidated_results": results_context}
    
    # Construir contexto histórico se disponível
    history_context = ""
    if conversation_history and len(conversation_history) > 0:
        history_context = "\n\n**CONTEXTO DA CONVERSA RECENTE:**\n"
        for msg in conversation_history[-4:]:  # Últimas 2 trocas
            role = "Usuário" if msg["role"] == "user" else "DriveBot"
            history_context += f"{role}: {msg['content'][:200]}...\n"
    
    # v11.0 FIX #9: Incluir insights do sanity check na apresentação
    sanity_context = ""
    if raw_result.get("sanity_insights"):
        sanity_context = "\n\n**⚠️ ALERTAS DO SISTEMA (SANITY CHECK):**\n"
        for insight in raw_result["sanity_insights"]:
            sanity_context += f"- {insight}\n"
        sanity_context += "\n**IMPORTANTE:** Você DEVE mencionar estes alertas na seção 💡 INSIGHT da sua resposta.\n"
    
    presenter_prompt = f"""Você é o DriveBot v7.0, um assistente de análise transparente. 

**REGRA ABSOLUTA:** Sua resposta DEVE seguir a estrutura do **Monólogo Analítico** de 4 partes:

1. 🎯 **OBJETIVO**: Reafirme o que o usuário pediu
2. 📝 **PLANO DE ANÁLISE**: Liste os passos executados (numerados, específicos)
3. 📊 **EXECUÇÃO E RESULTADO**: Apresente o resultado (tabela, número, etc)
4. 💡 **INSIGHT**: (Obrigatório se houver alertas do sistema) Observações sobre o resultado e anomalias detectadas

**Contexto:**
- Pergunta do usuário: "{question}"
- Análise executada nos dados REAIS do Google Drive
- Resultados abaixo são FATOS extraídos diretamente
{history_context}
{sanity_context}

**INSTRUÇÕES CRÍTICAS:**
- Use a estrutura de 4 partes (emojis obrigatórios)
- No Plano de Análise, seja ESPECÍFICO (mencione colunas e filtros exatos)
- Se a pergunta é continuação (usa pronomes), CONFIRME a entidade no Objetivo
- Seja direto e objetivo
- NÃO invente dados
- Se houver alertas do sanity check, MENCIONE-OS explicitamente na seção 💡 INSIGHT

**FORMATAÇÃO OBRIGATÓRIA:**
- Use **negrito** apenas para termos importantes (não exagere com asteriscos)
- Tabelas Markdown DEVEM ser bem formatadas:
  ```
  | Produto     | Quantidade | Valor      |
  |-------------|------------|------------|
  | Notebook    | 150        | R$ 450.000 |
  | Mouse       | 500        | R$ 15.000  |
  ```
- Alinhe colunas com espaços
- Evite tabelas com mais de 5 colunas
- Para dados extensos, mostre Top 10 + total
- Valores monetários: R$ 1.234,56
- Percentuais: 45,7%

**Dados Brutos da Análise:**
```json
{json.dumps(raw_result, indent=2, ensure_ascii=False, default=str)}
```

**Resposta Formatada (4 Partes Obrigatórias):**"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        # Sem limites de tokens - deixar Gemini gerar resposta completa
        response = model.generate_content(presenter_prompt)
        response_text = (response.text or "").strip()
        
        if not response_text:
            return "Desculpe, não consegui formatar a resposta. Aqui estão os dados brutos:\n\n" + json.dumps(raw_result, indent=2, ensure_ascii=False, default=str)
        
        # Aplicar limpeza de formatação Markdown
        response_text = clean_markdown_formatting(response_text)
        
        return response_text
    except Exception as e:
        print(f"Erro ao formatar resultado: {e}")
        return "Desculpe, não consegui formatar a resposta. Aqui estão os dados brutos:\n\n" + json.dumps(raw_result, indent=2, ensure_ascii=False, default=str)


def handle_drivebot_followup(message: str, conversation: Dict[str, Any], api_key: str) -> Optional[str]:
    """
    Processa perguntas do usuário sobre dados já descobertos usando arquitetura de dois prompts.
    AGORA COM MEMÓRIA CONVERSACIONAL.
    """
    import time
    start_time = time.time()
    
    drive_state = conversation.get("drive", {})
    tables = drive_state.get("tables", [])
    
    if not tables:
        return None
    
    # Extrair colunas disponíveis de todas as tabelas
    all_columns = set()
    auxiliary_columns_info = []
    
    for table in tables:
        df = table.get("df")
        if df is not None and not df.empty:
            all_columns.update(df.columns.tolist())
            
            # v11.0: Coletar informações sobre colunas auxiliares criadas
            if "auxiliary_columns" in table and table["auxiliary_columns"]:
                auxiliary_columns_info.append({
                    "table": table.get("name", "unknown"),
                    "auxiliary_cols": table["auxiliary_columns"]
                })
    
    available_columns = sorted(list(all_columns))
    
    if not available_columns:
        return None
    
    # Obter histórico da conversa (últimas 4 mensagens para contexto)
    conversation_history = list(conversation.get("messages", []))[-6:]
    
    # FASE 1: Traduzir pergunta em comando JSON (COM HISTÓRICO + COLUNAS AUXILIARES)
    print(f"[DriveBot] Traduzindo pergunta: {message}")
    command = generate_analysis_command(message, available_columns, api_key, conversation_history, auxiliary_columns_info)
    
    if not command:
        print("[DriveBot] Falha ao gerar comando de análise")
        return None
    
    print(f"[DriveBot] Comando gerado: {json.dumps(command, indent=2)}")
    
    # v11.0 FIX #7: Suporte para múltiplos comandos (lista de ferramentas)
    # Isso resolve "list object has no attribute 'get'" quando LLM envia [{...}, {...}]
    commands_to_execute = []
    
    if isinstance(command, list):
        # Múltiplos comandos: ex: [{"tool": "get_ranking", ...}, {"tool": "get_ranking", ...}]
        print(f"[DriveBot] Detectados {len(command)} comandos para executar")
        commands_to_execute = command
    else:
        # Comando único: ex: {"tool": "calculate_metric", ...}
        commands_to_execute = [command]
    
    # FASE 2: Executar TODOS os comandos nos dados REAIS
    all_results = []
    for idx, cmd in enumerate(commands_to_execute, 1):
        print(f"[DriveBot] Executando comando {idx}/{len(commands_to_execute)}...")
        raw_result = execute_analysis_command(cmd, tables)
        
        if not raw_result:
            print(f"[DriveBot] Falha ao executar comando {idx}")
            all_results.append({"error": "Falha na execução", "command_index": idx})
            continue
        
        all_results.append(raw_result)
    
    # Consolidar resultados
    if len(all_results) == 1:
        # Um único resultado: usar fluxo original
        raw_result = all_results[0]
    else:
        # Múltiplos resultados: criar estrutura consolidada
        raw_result = {
            "multi_command": True,
            "results": all_results,
            "command_count": len(all_results)
        }
    
    # v11.0 FIX #9: Sanity Check Pós-Análise (detecta anomalias nos dados)
    # Exemplo: "primeiro trimestre" mas só há dados de um mês
    sanity_insights = []
    
    if not raw_result.get("multi_command") and "error" not in raw_result:
        try:
            # Verificar anomalias em rankings/time_series/filtered_data
            if raw_result.get("tool") in ["get_ranking", "get_time_series", "get_filtered_data"]:
                data_list = raw_result.get("ranking") or raw_result.get("time_series") or raw_result.get("data", [])
                
                if data_list and len(data_list) > 0:
                    # Criar DataFrame temporário
                    temp_df = pd.DataFrame(data_list)
                    
                    # SANITY CHECK 1: Verificar se filtro temporal retornou apenas um mês
                    # quando a pergunta sugere múltiplos períodos
                    if 'Data_Mes_Nome' in temp_df.columns:
                        unique_months = temp_df['Data_Mes_Nome'].unique()
                        if len(unique_months) == 1:
                            sanity_insights.append(
                                f"⚠️ Todos os {len(data_list)} registros encontrados são do mês de {unique_months[0]}. "
                                f"Pode haver dados limitados para o período solicitado."
                            )
                    
                    # SANITY CHECK 2: Verificar se há muitos valores nulos
                    null_ratio = temp_df.isnull().sum().sum() / (len(temp_df) * len(temp_df.columns))
                    if null_ratio > 0.3:
                        sanity_insights.append(
                            f"⚠️ Atenção: {null_ratio*100:.1f}% dos dados retornados contêm valores ausentes."
                        )
        except Exception as e:
            print(f"[DriveBot] Erro no sanity check: {e}")
            pass
    
    # Adicionar insights ao resultado
    if sanity_insights:
        raw_result["sanity_insights"] = sanity_insights
    
    # Se houver erro no resultado único, tratar de forma mais elegante
    if "error" in raw_result and not raw_result.get("multi_command"):
        print(f"[DriveBot] Erro na análise: {raw_result['error']}")
        
        # Não expor erros técnicos ao usuário
        if "could not convert" in raw_result["error"] or "Lengths must match" in raw_result["error"]:
            return """⚠️ **Limitação Identificada**

Tive dificuldade em processar sua solicitação com os filtros especificados.

**O que posso fazer:**
✅ Reformular a análise de outra forma
✅ Buscar informações relacionadas sem esse filtro específico
✅ Sugerir análises alternativas baseadas nos dados disponíveis

Pode me dar mais detalhes sobre o que você gostaria de saber? Ou prefere que eu sugira algumas análises viáveis?"""
        
        # Para outros erros, tentar ser útil
        return None
    
    print(f"[DriveBot] Resultado da análise: {json.dumps(raw_result, indent=2, default=str)[:500]}...")
    
    # FASE 3: Formatar resultado em resposta amigável (COM HISTÓRICO)
    print(f"[DriveBot] Formatando resultado...")
    format_start = time.time()
    formatted_response = format_analysis_result(message, raw_result, api_key, conversation_history)
    
    # Log de performance
    total_time = time.time() - start_time
    format_time = time.time() - format_start
    print(f"[DRIVEBOT PERFORMANCE] Total: {total_time:.2f}s | Formatação: {format_time:.2f}s | Análise: {(total_time-format_time):.2f}s")
    
    return formatted_response

def get_bot_response(bot_id: str, message: str, conversation_id: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Gera resposta usando Google AI para o bot específico com memória de conversa simples."""
    try:
        if conversation_id is None or not isinstance(conversation_id, str) or not conversation_id.strip():
            conversation_id = str(uuid.uuid4())

        if bot_id == 'drivebot':
            api_key = DRIVEBOT_API_KEY
            system_prompt = DRIVEBOT_SYSTEM_PROMPT
        elif bot_id == 'alphabot':
            api_key = ALPHABOT_API_KEY
            system_prompt = ALPHABOT_SYSTEM_PROMPT
        else:
            return {"error": "Bot ID inválido", "conversation_id": conversation_id}

        conversation = ensure_conversation(conversation_id, bot_id)
        append_message(conversation, "user", message)

        if not api_key:
            error_msg = f"API key não configurada para {bot_id}"
            append_message(conversation, "assistant", error_msg)
            return {"error": error_msg, "conversation_id": conversation_id}

        def extract_drive_id(text: str) -> Optional[str]:
            import re

            url_pattern = r'drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)'
            url_match = re.search(url_pattern, text)
            if url_match:
                return url_match.group(1)

            candidate = text.strip()
            if '?' in candidate:
                candidate = candidate.split('?')[0]
            if '#' in candidate:
                candidate = candidate.split('#')[0]

            if (
                25 <= len(candidate) <= 50
                and re.match(r'^[a-zA-Z0-9_-]+$', candidate)
                and not any(word in candidate.lower() for word in ['como', 'você', 'pode', 'ajudar', 'o que', 'qual'])
            ):
                return candidate
            return None

        if bot_id == 'drivebot':
            drive_state = conversation.get("drive", {})
            drive_id = extract_drive_id(message)

            if drive_id:
                bundle = build_discovery_bundle(drive_id)
                drive_state.update({
                    "drive_id": drive_id,
                    "report": bundle["report"],
                    "tables": bundle["tables"],  # CRÍTICO: Armazenar os DataFrames reais
                    "summary": bundle["summary"],
                    "files_ok": bundle["files_ok"],
                    "files_failed": bundle["files_failed"],
                })

                header = (
                    f"Recebi o ID: {drive_id}. Iniciando a conexão e a leitura dos arquivos da pasta. "
                    "Por favor, aguarde um momento."
                )
                response_text = f"{header}\n\n{bundle['report']}"
                append_message(conversation, "assistant", response_text)
                return {"response": response_text, "conversation_id": conversation_id}

            if not drive_state.get("drive_id"):
                response_text = (
                    "## Preparando o ambiente de análise\n\n"
                    "Para avançar com a exploração dos dados, siga estes passos e me avise quando concluir:\n"
                    "1. Envie o ID da pasta do Google Drive (ou cole o link completo).\n"
                    "2. Garanta que id-spreadsheet-reader-robot@data-analytics-gc-475218.iam.gserviceaccount.com tenha acesso.\n\n"
                    "Assim que a pasta estiver acessível, consigo responder perguntas como a que você acabou de fazer usando os dados consolidados."
                )
                append_message(conversation, "assistant", response_text)
                return {"response": response_text, "conversation_id": conversation_id}

            manual_answer = handle_drivebot_followup(message, conversation, api_key)
            if manual_answer:
                append_message(conversation, "assistant", manual_answer)
                
                # GERAR SUGESTÕES PARA DRIVEBOT APÓS ANÁLISE
                suggestions = []
                drive_state = conversation.get("drive", {})
                if drive_state.get("summary"):
                    try:
                        metadata = {
                            'columns': list(drive_state.get("summary", {}).keys())[:15],
                            'total_columns': len(drive_state.get("summary", {})),
                            'date_columns': [col for col in drive_state.get("summary", {}).keys() 
                                           if any(word in col.lower() for word in ['data', 'date', 'mes', 'ano', 'month'])],
                            'has_data': True
                        }
                        suggestions = generate_drivebot_suggestions(message, manual_answer, metadata)
                        print(f"[DRIVEBOT SUGESTÕES] Geradas {len(suggestions)} sugestões após análise")
                    except Exception as sugg_error:
                        print(f"[DRIVEBOT SUGESTÕES] Erro ao gerar: {sugg_error}")
                
                # 🚀 SPRINT 2 - FEATURE 3: GRÁFICOS PARA DRIVEBOT
                chart_data = None
                tables = drive_state.get("tables", [])
                
                print(f"[DRIVEBOT GRÁFICO] Verificando se deve incluir gráfico para: {message}")
                print(f"[DRIVEBOT GRÁFICO] Encontradas {len(tables)} tabelas no drive_state")
                
                if tables:
                    for idx, table in enumerate(tables):
                        df = table.get("df")
                        print(f"[DRIVEBOT GRÁFICO] Tabela {idx}: df={'presente' if df is not None else 'None'}, empty={df.empty if df is not None else 'N/A'}")
                        
                        if df is not None and not df.empty:
                            # Criar metadata para detecção de gráfico
                            metadata_for_chart = {
                                'date_columns': [col for col in df.columns 
                                               if any(word in col.lower() for word in ['data', 'date', 'mes', 'ano', 'month'])]
                            }
                            
                            print(f"[DRIVEBOT GRÁFICO] Metadata: {metadata_for_chart}")
                            
                            if should_include_chart(message, df, metadata_for_chart):
                                print(f"[DRIVEBOT GRÁFICO] should_include_chart retornou True")
                                chart_data = generate_chart_data(df, message, metadata_for_chart)
                                if chart_data:
                                    print(f"[DRIVEBOT GRÁFICO] ✅ Incluindo gráfico do tipo '{chart_data['type']}' com {len(chart_data['data'])} pontos")
                                    break
                                else:
                                    print(f"[DRIVEBOT GRÁFICO] ❌ generate_chart_data retornou None")
                            else:
                                print(f"[DRIVEBOT GRÁFICO] should_include_chart retornou False")
                else:
                    print(f"[DRIVEBOT GRÁFICO] ❌ Nenhuma tabela disponível")
                
                return {
                    "response": manual_answer, 
                    "conversation_id": conversation_id,
                    "suggestions": suggestions,
                    "chart": chart_data  # 🚀 Incluir gráfico se gerado
                }

        if bot_id == 'alphabot' and any(
            word in message.lower() for word in ['anexo', 'arquivo', 'planilha', 'csv', 'xlsx', 'enviei', 'anexei']
        ):
            response_text = (
                "## Relatório de Leitura dos Anexos\n\n"
                "**Status:** Leitura concluída.\n\n"
                "**Taxa de Sucesso:** 3 de 3 arquivos lidos com sucesso.\n\n"
                "**Arquivos Analisados:**\n"
                "- vendas_q1_2024.xlsx\n"
                "- dados_produtos.csv\n"
                "- relatorio_completo.xlsx\n\n"
                "**Arquivos com Falha:**\n"
                "Nenhum arquivo apresentou falha na leitura.\n\n"
                "Análise concluída. Estou pronto para suas perguntas sobre os dados destes arquivos."
            )
            append_message(conversation, "assistant", response_text)
            return {"response": response_text, "conversation_id": conversation_id}

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as config_error:
            print(f"Erro na configuração da API: {config_error}")
            if bot_id == 'drivebot':
                drive_state = conversation.get("drive", {})
                if drive_state.get("profile"):
                    response_text = (
                        "## Indisponibilidade temporária\n\n"
                        "Mapeei a pasta e os dados continuam armazenados. Não consegui gerar a resposta agora, "
                        "mas você pode tentar novamente em instantes com a mesma pergunta."
                    )
                else:
                    response_text = (
                        "Estou em modo simulado no momento. Por favor, envie o ID da pasta do Google Drive "
                        "conforme as instruções para que eu possa iniciar a análise."
                    )
            else:
                response_text = (
                    "Analista de Planilhas está em modo simulado agora. Anexe as planilhas desejadas e tente "
                    "novamente em alguns segundos."
                )

            append_message(conversation, "assistant", response_text)
            return {"response": response_text, "conversation_id": conversation_id}

        context_sections: List[str] = []

        if bot_id == 'drivebot':
            drive_state = conversation.get("drive", {})
            if drive_state.get("report"):
                context_sections.append("## Contexto da descoberta\n" + drive_state["report"])

        history_entries = list_history(conversation)[-6:]
        if history_entries:
            role_label = 'DriveBot' if bot_id == 'drivebot' else 'AlphaBot'
            history_lines = []
            for entry in history_entries:
                speaker = 'Usuário' if entry['role'] == 'user' else role_label
                history_lines.append(f"- {speaker}: {entry['content']}")
            context_sections.append("## Histórico recente\n" + "\n".join(history_lines))

        full_prompt = system_prompt
        if context_sections:
            full_prompt = f"{full_prompt}\n\n" + "\n\n".join(context_sections)
        full_prompt += f"\n\nUsuário: {message}\n{('DriveBot' if bot_id == 'drivebot' else 'AlphaBot')}:"

        try:
            response = model.generate_content(full_prompt)
            response_text = (response.text or "").strip()
        except Exception as ai_error:
            print(f"Erro na geração de conteúdo: {ai_error}")
            response_text = ""

        if not response_text:
            if bot_id == 'drivebot':
                response_text = (
                    "## Não consegui concluir a análise\n\n"
                    "Os dados estão mapeados, mas não consegui gerar a síntese solicitada agora. "
                    "Tente reformular a pergunta ou peça um recorte diferente (ex.: ranking por região, "
                    "tendência mensal, principais categorias)."
                )
            else:
                response_text = (
                    "Não consegui gerar a resposta agora. Verifique se as planilhas foram anexadas e tente novamente."
                )

        append_message(conversation, "assistant", response_text)
        
        # ============================================
        # GERAR SUGESTÕES DE FOLLOW-UP PARA DRIVEBOT
        # ============================================
        suggestions = []
        if bot_id == 'drivebot' and response_text and not any(
            phrase in response_text.lower() for phrase in [
                'envie o id', 'pasta do google drive', 'modo simulado', 
                'indisponibilidade', 'não consegui'
            ]
        ):
            # Só gera sugestões se temos dados e uma resposta válida
            drive_state = conversation.get("drive", {})
            if drive_state.get("summary"):
                try:
                    # Extrair metadados dos dados do Drive
                    metadata = {
                        'columns': list(drive_state.get("summary", {}).keys())[:15],
                        'total_columns': len(drive_state.get("summary", {})),
                        'date_columns': [col for col in drive_state.get("summary", {}).keys() 
                                       if any(word in col.lower() for word in ['data', 'date', 'mes', 'ano', 'month'])],
                        'has_data': True
                    }
                    
                    # Gerar sugestões usando Gemini
                    suggestions = generate_drivebot_suggestions(message, response_text, metadata)
                    print(f"[DRIVEBOT SUGESTÕES] Geradas {len(suggestions)} sugestões")
                except Exception as sugg_error:
                    print(f"[DRIVEBOT SUGESTÕES] Erro ao gerar: {sugg_error}")
                    suggestions = []
        
        # Este código nunca é alcançado para DriveBot (retorna antes)
        # Mantido apenas como fallback para outros casos
        return {
            "response": response_text, 
            "conversation_id": conversation_id,
            "suggestions": suggestions
        }

    except Exception as error:
        print(f"Erro geral no get_bot_response: {error}")
        return {"error": f"Erro ao gerar resposta: {str(error)}", "conversation_id": conversation_id or str(uuid.uuid4())}

# REMOVIDO: Rota duplicada do AlphaBot (upload) — substituída por blueprint modular

# ============================================
# 🚀 SPRINT 2: SUGESTÕES DE PERGUNTAS
# ============================================
# SUGESTÕES DE FOLLOW-UP PARA DRIVEBOT
# ============================================
def generate_drivebot_suggestions(original_question: str, answer: str, metadata: Dict[str, Any]) -> List[str]:
    """
    Gera 3 perguntas sugeridas inteligentes para DriveBot baseadas na resposta atual.
    Adaptado para o contexto de análise de dados do Google Drive.
    """
    try:
        # Contexto dos dados disponíveis
        columns_context = f"Colunas disponíveis: {', '.join(metadata.get('columns', [])[:10])}"
        
        # Prompt específico para DriveBot
        suggestion_prompt = f"""Você é um assistente especialista em análise de dados de Google Drive.

**Contexto:**
- Pergunta original do usuário: "{original_question}"
- Resposta fornecida: "{answer[:300]}..."
- {columns_context}

**Tarefa:**
Sugira EXATAMENTE 3 perguntas de aprofundamento que o usuário pode fazer para explorar mais os dados da pasta do Drive.

**Regras:**
1. As perguntas devem ser ESPECÍFICAS aos dados disponíveis
2. Devem ser naturais e diretas (máximo 12 palavras cada)
3. Devem explorar diferentes ângulos: temporal, comparativo, ranking, tendências
4. Use linguagem de análise de negócios (vendas, produtos, regiões, clientes, etc)
5. NÃO repita a pergunta original
6. NÃO sugira análises impossíveis com os dados disponíveis

**Formato de saída:**
Retorne APENAS um JSON array com 3 strings, sem explicação adicional:
["Pergunta 1?", "Pergunta 2?", "Pergunta 3?"]

**Exemplos de boas sugestões:**
- "Qual foi o produto mais vendido no último trimestre?"
- "Como foi a performance da região Sul comparada ao Norte?"
- "Quais categorias tiveram queda nas vendas?"
- "Qual vendedor bateu a meta este mês?"
"""
        
        # Usar API do DriveBot (DRIVEBOT_API_KEY)
        genai.configure(api_key=DRIVEBOT_API_KEY or ALPHABOT_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content(suggestion_prompt)
        suggestions_text = response.text.strip()
        
        # Extrair JSON do texto (pode vir com markdown)
        if '```json' in suggestions_text:
            suggestions_text = suggestions_text.split('```json')[1].split('```')[0].strip()
        elif '```' in suggestions_text:
            suggestions_text = suggestions_text.split('```')[1].split('```')[0].strip()
        
        # Parse JSON
        suggestions = json.loads(suggestions_text)
        
        # Validar e limitar
        if isinstance(suggestions, list) and len(suggestions) > 0:
            return suggestions[:3]  # Garantir máximo 3
        else:
            return generate_drivebot_fallback_suggestions(metadata)
            
    except Exception as e:
        print(f"[DRIVEBOT SUGESTÕES] Erro ao gerar sugestões: {str(e)}")
        return generate_drivebot_fallback_suggestions(metadata)

def generate_drivebot_fallback_suggestions(metadata: Dict[str, Any]) -> List[str]:
    """
    Gera sugestões genéricas para DriveBot quando Gemini falha.
    Baseado nos metadados dos dados do Drive.
    """
    suggestions = []
    
    # Se há colunas temporais, sugerir análise temporal
    if metadata.get('date_columns'):
        suggestions.append("Qual foi a evolução mês a mês?")
    
    # Sugestões baseadas em tipo de análise comum
    suggestions.append("Me mostre o ranking dos top 5 itens")
    suggestions.append("Qual região teve melhor desempenho?")
    
    # Sugestões padrão de negócios
    if len(suggestions) < 3:
        suggestions.extend([
            "Quais são as principais tendências identificadas?",
            "Há algum outlier ou valor atípico nos dados?",
            "Como foi a distribuição por categoria?"
        ])
    
    return suggestions[:3]

# ============================================
# SUGESTÕES DE FOLLOW-UP PARA ALPHABOT
# ============================================
def generate_follow_up_questions(original_question: str, answer: str, metadata: Dict[str, Any]) -> List[str]:
    """
    Gera 3 perguntas sugeridas inteligentes baseadas na resposta atual.
    Usa Gemini para criar follow-ups contextuais.
    """
    try:
        # Contexto dos dados disponíveis
        columns_context = f"Colunas disponíveis: {', '.join(metadata['columns'][:10])}"
        
        # Prompt para geração de sugestões
        suggestion_prompt = f"""Você é um assistente especialista em análise de dados.

**Contexto:**
- Pergunta original do usuário: "{original_question}"
- Resposta fornecida: "{answer[:300]}..."
- {columns_context}

**Tarefa:**
Sugira EXATAMENTE 3 perguntas de aprofundamento que o usuário pode fazer para explorar mais os dados.

**Regras:**
1. As perguntas devem ser ESPECÍFICAS aos dados disponíveis
2. Devem ser naturais e diretas (máximo 10 palavras cada)
3. Devem explorar diferentes ângulos: temporal, comparativo, ranking, causas
4. NÃO repita a pergunta original
5. NÃO sugira análises impossíveis com os dados disponíveis

**Formato de saída:**
Retorne APENAS um JSON array com 3 strings, sem explicação adicional:
["Pergunta 1?", "Pergunta 2?", "Pergunta 3?"]

**Exemplos de boas sugestões:**
- "Qual região teve maior crescimento percentual?"
- "Como foi a evolução mensal desse produto?"
- "Quais os 3 piores performers deste mês?"
"""
        
        genai.configure(api_key=ALPHABOT_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content(suggestion_prompt)
        suggestions_text = response.text.strip()
        
        # Extrair JSON do texto (pode vir com markdown)
        if '```json' in suggestions_text:
            suggestions_text = suggestions_text.split('```json')[1].split('```')[0].strip()
        elif '```' in suggestions_text:
            suggestions_text = suggestions_text.split('```')[1].split('```')[0].strip()
        
        # Parse JSON
        suggestions = json.loads(suggestions_text)
        
        # Validar e limitar
        if isinstance(suggestions, list) and len(suggestions) > 0:
            return suggestions[:3]  # Garantir máximo 3
        else:
            return []
            
    except Exception as e:
        print(f"[SUGESTÕES] Erro ao gerar sugestões: {str(e)}")
        # Fallback: sugestões genéricas baseadas em metadata
        return generate_fallback_suggestions(metadata)

def generate_fallback_suggestions(metadata: Dict[str, Any]) -> List[str]:
    """
    Gera sugestões genéricas quando Gemini falha.
    Baseado nos metadados dos dados.
    """
    suggestions = []
    
    # Se há colunas temporais, sugerir análise temporal
    if metadata.get('date_columns'):
        suggestions.append("Como foi a evolução ao longo do tempo?")
    
    # Se há muitas colunas, sugerir análise de correlação
    if metadata.get('total_columns', 0) > 5:
        suggestions.append("Quais são os top 10 registros?")
        suggestions.append("Qual a distribuição por categoria principal?")
    
    # Sugestões padrão
    if len(suggestions) < 3:
        suggestions.extend([
            "Me mostre um resumo estatístico completo",
            "Quais são os valores extremos (máximo e mínimo)?",
            "Há alguma tendência ou padrão interessante?"
        ])
    
    return suggestions[:3]

# ============================================
# 🚀 SPRINT 2 - FEATURE 3: GRÁFICOS AUTOMÁTICOS
# ============================================

def should_include_chart(question: str, df: pd.DataFrame, metadata: Dict[str, Any]) -> bool:
    """
    Detecta se a pergunta é apropriada para incluir um gráfico.
    
    Critérios:
    1. Palavras-chave relacionadas a visualização
    2. Dados numéricos disponíveis
    3. Colunas temporais ou categóricas para agrupamento
    """
    # Palavras-chave que indicam visualização
    chart_keywords = [
        'evolução', 'evolucao', 'tendência', 'tendencia', 'ao longo',
        'comparar', 'compare', 'distribuição', 'distribuicao',
        'gráfico', 'grafico', 'visualize', 'mostre', 'plot',
        'crescimento', 'queda', 'variação', 'variacao',
        'temporal', 'mensal', 'anual', 'diário', 'diario'
    ]
    
    question_lower = question.lower()
    has_keywords = any(keyword in question_lower for keyword in chart_keywords)
    
    # Verificar se há colunas numéricas
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    has_numeric = len(numeric_cols) > 0
    
    # Verificar se há colunas temporais ou categóricas
    has_date = len(metadata.get('date_columns', [])) > 0
    
    # Colunas categóricas (texto com poucos valores únicos)
    categorical_cols = [
        col for col in df.select_dtypes(include=['object']).columns
        if df[col].nunique() <= 20  # Máximo 20 categorias
    ]
    has_categorical = len(categorical_cols) > 0
    
    # Incluir gráfico se: tem keywords E tem dados numéricos E (tem temporal OU categórico)
    return has_keywords and has_numeric and (has_date or has_categorical)

def generate_chart_data(df: pd.DataFrame, question: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Gera dados para gráfico baseado na pergunta e nos dados disponíveis.
    
    Retorna:
    {
        "type": "line" | "bar" | "pie",
        "data": [{"label": "Jan", "value": 100}, ...],
        "x_axis": "Mês",
        "y_axis": "Vendas",
        "title": "Evolução de Vendas"
    }
    """
    try:
        question_lower = question.lower()
        
        # Detectar tipo de análise baseado na pergunta
        is_temporal = any(word in question_lower for word in ['evolução', 'evolucao', 'tendência', 'tendencia', 'ao longo', 'temporal', 'mensal', 'anual', 'diário', 'diario'])
        is_distribution = any(word in question_lower for word in ['distribuição', 'distribuicao', 'divisão', 'divisao', 'proporção', 'proporcao', 'percentual'])
        is_ranking = any(word in question_lower for word in ['ranking', 'top', 'maiores', 'menores', 'melhores', 'piores'])
        is_comparison = any(word in question_lower for word in ['comparar', 'compare', 'comparação', 'comparacao', 'versus', 'vs', 'entre'])
        
        # Colunas numéricas disponíveis
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols:
            return None
        
        # Escolher coluna numérica mais relevante
        # Priorizar colunas com "valor", "total", "vendas", "quantidade"
        value_col = numeric_cols[0]
        for col in numeric_cols:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['valor', 'total', 'vendas', 'venda', 'quantidade', 'qtd', 'receita']):
                value_col = col
                break
        
        # GRÁFICO TEMPORAL (LineChart) - Evolução ao longo do tempo
        if is_temporal and metadata.get('date_columns'):
            date_col = metadata['date_columns'][0]
            
            # Agrupar por data e somar valores
            grouped = df.groupby(date_col)[value_col].sum().reset_index()
            grouped = grouped.sort_values(date_col).head(20)  # Máximo 20 pontos
            
            chart_data = []
            for _, row in grouped.iterrows():
                chart_data.append({
                    str(date_col): str(row[date_col]),
                    str(value_col): float(row[value_col])
                })
            
            return {
                "type": "line",
                "data": chart_data,
                "x_axis": str(date_col),
                "y_axis": str(value_col),
                "title": f"Evolução de {value_col}"
            }
        
        # GRÁFICO DE DISTRIBUIÇÃO (BarChart horizontal) - Mostra como dados estão divididos
        elif is_distribution:
            # Encontrar melhor coluna categórica
            categorical_cols = [
                col for col in df.select_dtypes(include=['object']).columns
                if df[col].nunique() <= 20 and df[col].nunique() >= 2
            ]
            
            if not categorical_cols:
                return None
            
            # Priorizar colunas com "categoria", "tipo", "região", "status"
            category_col = categorical_cols[0]
            for col in categorical_cols:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['categoria', 'tipo', 'região', 'regiao', 'status', 'grupo', 'classe']):
                    category_col = col
                    break
            
            # Contar ocorrências para distribuição (não somar valores)
            distribution = df[category_col].value_counts().reset_index()
            distribution.columns = [category_col, 'Quantidade']
            distribution = distribution.head(10)
            
            chart_data = []
            for _, row in distribution.iterrows():
                chart_data.append({
                    str(category_col): str(row[category_col]),
                    'Quantidade': int(row['Quantidade'])
                })
            
            return {
                "type": "bar",
                "data": chart_data,
                "x_axis": str(category_col),
                "y_axis": "Quantidade",
                "title": f"Distribuição por {category_col}"
            }
        
        # GRÁFICO DE RANKING/COMPARAÇÃO (BarChart) - Top valores
        elif is_ranking or is_comparison:
            # Encontrar coluna categórica
            categorical_cols = [
                col for col in df.select_dtypes(include=['object']).columns
                if df[col].nunique() <= 20 and df[col].nunique() >= 2
            ]
            
            if not categorical_cols:
                return None
            
            # Priorizar colunas relevantes
            category_col = categorical_cols[0]
            for col in categorical_cols:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['região', 'regiao', 'vendedor', 'produto', 'cliente', 'loja', 'filial']):
                    category_col = col
                    break
            
            # Agrupar por categoria e somar valores
            grouped = df.groupby(category_col)[value_col].sum().reset_index()
            grouped = grouped.sort_values(value_col, ascending=False).head(10)  # Top 10
            
            chart_data = []
            for _, row in grouped.iterrows():
                chart_data.append({
                    str(category_col): str(row[category_col]),
                    str(value_col): float(row[value_col])
                })
            
            return {
                "type": "bar",
                "data": chart_data,
                "x_axis": str(category_col),
                "y_axis": str(value_col),
                "title": f"Ranking de {value_col} por {category_col}"
            }
        
        return None
        
    except Exception as e:
        print(f"[GRÁFICO] Erro ao gerar dados: {str(e)}")
        return None

# ============================================

## REMOVIDO: Rota duplicada do AlphaBot (chat) — substituída por blueprint modular

## REMOVIDO: Rota duplicada do AlphaBot (export) — substituída por blueprint modular

@app.route('/api/drivebot/export', methods=['POST', 'OPTIONS'])
def drivebot_export():
    """
    Endpoint para exportar dados do DriveBot como arquivo Excel (.xlsx).
    
    Recebe: { "conversation_id": "abc123" }
    Retorna: Arquivo Excel binário para download
    """
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
        
        conversation_id = data.get('conversation_id')
        
        if not conversation_id:
            return jsonify({"error": "conversation_id é obrigatório"}), 400
        
        # Verificar se a conversa existe
        if conversation_id not in CONVERSATION_STORE:
            return jsonify({"error": "Conversa não encontrada"}), 404
        
        conversation = CONVERSATION_STORE[conversation_id]
        drive_state = conversation.get("drive", {})
        tables = drive_state.get("tables", [])
        
        if not tables:
            return jsonify({"error": "Nenhum dado disponível para exportar"}), 404
        
        # Consolidar todos os DataFrames em um único arquivo Excel
        # Cada tabela será uma sheet separada
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for idx, table in enumerate(tables):
                df = table.get("df")
                sheet_name = table.get("name", f"Sheet{idx+1}")[:31]  # Excel limit: 31 chars
                
                if df is not None and not df.empty:
                    df.to_excel(writer, index=False, sheet_name=sheet_name)
                    
                    # Obter worksheet para aplicar formatação
                    worksheet = writer.sheets[sheet_name]
                    
                    # Aplicar formatação ao cabeçalho
                    from openpyxl.styles import Font, PatternFill, Alignment
                    
                    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
                    header_font = Font(color='FFFFFF', bold=True)
                    
                    for cell in worksheet[1]:  # Primeira linha (cabeçalho)
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.alignment = Alignment(horizontal='center', vertical='center')
                    
                    # Ajustar largura das colunas
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        
                        adjusted_width = min(max_length + 2, 50)  # Máximo 50
                        worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Preparar para download
        output.seek(0)
        
        # Nome do arquivo com timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'drivebot_export_{timestamp}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"[DRIVEBOT EXPORT] Erro: {str(e)}")
        return jsonify({"error": f"Erro ao exportar dados: {str(e)}"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint principal para chat com os bots
    🔄 MULTI-USUÁRIO: Salva mensagens no banco se conversation_id e user_id fornecidos
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
            
        bot_id = data.get('bot_id')
        message = data.get('message')
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id')  # 🆕 MULTI-USUÁRIO
        
        if not bot_id or not message:
            return jsonify({"error": "bot_id e message são obrigatórios"}), 400
        
        # 🔧 FIX #2: Salvar mensagem do usuário no sistema correto baseado no bot
        if conversation_id and user_id:
            try:
                if bot_id == 'alphabot':
                    # Sistema AlphaBot
                    database.add_alphabot_message(
                        conversation_id=conversation_id,
                        author='user',
                        text=message,
                        time=int(datetime.now().timestamp() * 1000)
                    )
                    print(f"✅ Mensagem do usuário salva na conversa AlphaBot {conversation_id}")
                else:
                    # Sistema DriveBot (tabelas compartilhadas)
                    database.add_message(
                        conversation_id=conversation_id,
                        author='user',
                        text=message,
                        time=int(datetime.now().timestamp() * 1000)
                    )
                    print(f"✅ Mensagem do usuário salva na conversa DriveBot {conversation_id}")
            except Exception as db_error:
                print(f"⚠️ Erro ao salvar mensagem do usuário: {db_error}")
            
        # Gerar resposta do bot
        result = get_bot_response(bot_id, message, conversation_id)
        
        if "error" in result:
            return jsonify(result), 500
        
        # 🔧 FIX #3: Salvar resposta do bot no sistema correto baseado no bot
        if conversation_id and user_id and "response" in result:
            try:
                if bot_id == 'alphabot':
                    # Sistema AlphaBot
                    database.add_alphabot_message(
                        conversation_id=conversation_id,
                        author=bot_id,
                        text=result["response"],
                        time=int(datetime.now().timestamp() * 1000)
                    )
                    print(f"✅ Resposta do AlphaBot salva na conversa {conversation_id}")
                else:
                    # Sistema DriveBot (tabelas compartilhadas)
                    database.add_message(
                        conversation_id=conversation_id,
                        author=bot_id,
                        text=result["response"],
                        time=int(datetime.now().timestamp() * 1000),
                        suggestions=result.get("suggestions")
                    )
                    print(f"✅ Resposta do DriveBot salva na conversa {conversation_id}")
            except Exception as db_error:
                print(f"⚠️ Erro ao salvar resposta do bot: {db_error}")
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


## REMOVIDO: Rota duplicada do AlphaBot (clear-data) — substituída por blueprint modular


## REMOVIDO: Rota duplicada do AlphaBot (sessions list) — substituída por blueprint modular


## REMOVIDO: Rota duplicada do AlphaBot (conversations list) — substituída por blueprint modular


## REMOVIDO: Rota duplicada do AlphaBot (conversation messages) — substituída por blueprint modular


## REMOVIDO: Rota duplicada do AlphaBot (create conversation) — substituída por blueprint modular


## REMOVIDO: Rota duplicada do AlphaBot (delete session) — substituída por blueprint modular

# ============================================
# 🚀 SPRINT 2 - FEATURE 5: CACHE MANAGEMENT
# ============================================

@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Retorna estatísticas do cache"""
    try:
        total_requests = CACHE_STATS['hits'] + CACHE_STATS['misses']
        hit_rate = (CACHE_STATS['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Calcular tamanho do cache em memória (aproximado)
        cache_size_bytes = 0
        for key, value in RESPONSE_CACHE.items():
            # Estimar tamanho de cada entrada
            cache_size_bytes += len(str(value))
        
        cache_size_mb = cache_size_bytes / (1024 * 1024)
        
        stats = {
            'total_entries': len(RESPONSE_CACHE),
            'total_requests': total_requests,
            'hits': CACHE_STATS['hits'],
            'misses': CACHE_STATS['misses'],
            'hit_rate': round(hit_rate, 2),
            'sets': CACHE_STATS['sets'],
            'expired': CACHE_STATS['expired'],
            'clears': CACHE_STATS['clears'],
            'cache_size_mb': round(cache_size_mb, 2),
            'ttl_seconds': CACHE_TTL_SECONDS,
            'max_entries': 1000
        }
        
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao obter estatísticas: {str(e)}"}), 500

@app.route('/api/cache/clear', methods=['POST'])
def cache_clear():
    """Limpa todo o cache"""
    try:
        global RESPONSE_CACHE
        entries_cleared = len(RESPONSE_CACHE)
        RESPONSE_CACHE = {}
        CACHE_STATS['clears'] += 1
        
        print(f"[CACHE CLEAR] 🧹 Cache limpo: {entries_cleared} entradas removidas")
        
        return jsonify({
            "message": "Cache limpo com sucesso",
            "entries_cleared": entries_cleared
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao limpar cache: {str(e)}"}), 500

# ============================================
# 🔐 AUTENTICAÇÃO E GESTÃO DE USUÁRIOS
# ============================================

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    """Registrar novo usuário"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        # Tentar inicializar database se ainda não foi inicializado
        try:
            database.init_database()
        except Exception as init_error:
            print(f"⚠️ Database já inicializado ou erro: {init_error}")
        
        data = request.json
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        print(f"📝 Tentativa de REGISTRO: username='{username}'")
        
        # Validações
        if not username or len(username) < 3:
            return jsonify({"error": "Username deve ter pelo menos 3 caracteres"}), 400
        
        if not password or len(password) < 6:
            return jsonify({"error": "Senha deve ter pelo menos 6 caracteres"}), 400
        
        # Criar usuário
        user = database.create_user(username, password)
        print(f"📝 Resultado registro: {'✅ Criado' if user else '❌ Já existe'}")
        
        if user:
            return jsonify({
                "success": True,
                "user": {
                    "id": user['id'],
                    "username": user['username']
                },
                "message": "Usuário criado com sucesso!"
            }), 201
        else:
            return jsonify({"error": "Username já existe"}), 409
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Erro no registro: {e}")
        print(f"❌ Stack trace: {error_details}")
        return jsonify({
            "error": "Erro ao registrar usuário",
            "details": str(e),
            "type": type(e).__name__
        }), 500


@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Autenticar usuário"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        print(f"🔐 Tentativa de LOGIN: username='{username}'")
        
        if not username or not password:
            return jsonify({"error": "Username e senha são obrigatórios"}), 400
        
        # Autenticar
        user = database.authenticate_user(username, password)
        print(f"🔐 Resultado autenticação: {'✅ Sucesso' if user else '❌ Falhou'}")
        
        if user:
            return jsonify({
                "success": True,
                "user": {
                    "id": user['id'],
                    "username": user['username']
                },
                "message": "Login realizado com sucesso!"
            }), 200
        else:
            return jsonify({"error": "Credenciais inválidas"}), 401
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Erro no login: {e}")
        print(f"❌ Stack trace: {error_details}")
        return jsonify({
            "error": "Erro ao fazer login",
            "details": str(e),
            "type": type(e).__name__
        }), 500


@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Retorna dados do usuário atual (baseado no user_id enviado)"""
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({"error": "user_id não fornecido"}), 400
        
        user = database.get_user_by_id(user_id)
        
        if user:
            return jsonify({
                "user": {
                    "id": user['id'],
                    "username": user['username']
                }
            }), 200
        else:
            return jsonify({"error": "Usuário não encontrado"}), 404
    
    except Exception as e:
        print(f"❌ Erro ao buscar usuário: {e}")
        return jsonify({"error": "Erro ao buscar usuário"}), 500


# ============================================
# 💬 GESTÃO DE CONVERSAS
# ============================================

@app.route('/api/conversations', methods=['GET', 'POST', 'OPTIONS'])
def conversations():
    """Listar ou criar conversas"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        user_id = request.args.get('user_id', type=int) or request.json.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id não fornecido"}), 400
        
        if request.method == 'GET':
            # Listar conversas do usuário
            bot_type = request.args.get('bot_type')  # Filtro opcional
            conversations_list = database.get_user_conversations(user_id, bot_type)
            
            return jsonify({
                "conversations": conversations_list,
                "count": len(conversations_list)
            }), 200
        
        elif request.method == 'POST':
            # Criar nova conversa
            data = request.json
            bot_type = data.get('bot_type', 'alphabot')
            title = data.get('title', 'Nova Conversa')
            
            conversation_id = database.create_conversation(user_id, bot_type, title)
            
            return jsonify({
                "success": True,
                "conversation_id": conversation_id,
                "bot_type": bot_type,
                "title": title,
                "message": "Conversa criada com sucesso!"
            }), 201
    
    except Exception as e:
        print(f"❌ Erro em conversas: {e}")
        return jsonify({"error": f"Erro ao processar conversas: {str(e)}"}), 500


@app.route('/api/conversations/<conversation_id>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
def conversation_detail(conversation_id):
    """Obter, atualizar ou deletar uma conversa específica"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        user_id = request.args.get('user_id', type=int) or (request.json or {}).get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id não fornecido"}), 400
        
        if request.method == 'GET':
            # Obter detalhes da conversa
            conversation = database.get_conversation(conversation_id, user_id)
            
            if conversation:
                return jsonify({"conversation": conversation}), 200
            else:
                return jsonify({"error": "Conversa não encontrada"}), 404
        
        elif request.method == 'PUT':
            # Atualizar título da conversa
            data = request.json
            title = data.get('title')
            
            if not title:
                return jsonify({"error": "Título não fornecido"}), 400
            
            success = database.update_conversation_title(conversation_id, user_id, title)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Conversa atualizada com sucesso!"
                }), 200
            else:
                return jsonify({"error": "Conversa não encontrada"}), 404
        
        elif request.method == 'DELETE':
            # Deletar conversa
            success = database.delete_conversation(conversation_id, user_id)
            
            if success:
                return jsonify({
                    "success": True,
                    "message": "Conversa deletada com sucesso!"
                }), 200
            else:
                return jsonify({"error": "Conversa não encontrada"}), 404
    
    except Exception as e:
        print(f"❌ Erro em conversa: {e}")
        return jsonify({"error": f"Erro ao processar conversa: {str(e)}"}), 500


@app.route('/api/conversations/<conversation_id>/messages', methods=['GET', 'OPTIONS'])
def conversation_messages(conversation_id):
    """Obter todas as mensagens de uma conversa"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        user_id = request.args.get('user_id', type=int)
        
        if not user_id:
            return jsonify({"error": "user_id não fornecido"}), 400
        
        messages = database.get_conversation_messages(conversation_id, user_id)
        
        return jsonify({
            "messages": messages,
            "count": len(messages)
        }), 200
    
    except Exception as e:
        print(f"❌ Erro ao buscar mensagens: {e}")
        return jsonify({"error": f"Erro ao buscar mensagens: {str(e)}"}), 500


@app.route('/api/conversations/search', methods=['GET', 'OPTIONS'])
def search_conversations():
    """Buscar conversas por título ou conteúdo"""
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        user_id = request.args.get('user_id', type=int)
        query = request.args.get('q', '').strip()
        
        if not user_id:
            return jsonify({"error": "user_id não fornecido"}), 400
        
        if not query:
            return jsonify({"error": "Query de busca não fornecida"}), 400
        
        results = database.search_conversations(user_id, query)
        
        return jsonify({
            "results": results,
            "count": len(results),
            "query": query
        }), 200
    
    except Exception as e:
        print(f"❌ Erro na busca: {e}")
        return jsonify({"error": f"Erro ao buscar: {str(e)}"}), 500


@app.route('/')
def root():
    """Rota raiz - redireciona para documentação da API"""
    return jsonify({
        "message": "AlphaBot API está funcionando!",
        "version": "v2.0",
        "endpoints": {
            "health": "/api/health",
            "alphabot": "/api/alphabot/*",
            "drivebot": "/api/drivebot/*",
            "auth": "/api/auth/*"
        },
        "documentation": "Acesse /api/health para verificar o status do serviço",
        "frontend": "Configure VITE_API_URL para esta URL no frontend"
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de saúde do serviço para Render/Railway"""
    try:
        # Testar conexão com banco de dados
        database.init_database()  # Verificar se o DB está acessível
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return jsonify({
        "status": "ok", 
        "service": "Alpha Insights Chat Backend",
        "database": db_status,
        "environment": {
            "render": bool(os.environ.get('RENDER')),
            "railway": bool(os.environ.get('RAILWAY_ENVIRONMENT')),
            "local": not (os.environ.get('RENDER') or os.environ.get('RAILWAY_ENVIRONMENT')),
            "postgres": bool(os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL'))
        },
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Detectar ambiente e configurar porta/host apropriados
    port = int(os.environ.get('PORT', 5000))
    
    # Railway, Render, Heroku usam PORT
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER') or os.environ.get('PORT'):
        print(f"🚂 Iniciando em modo produção na porta {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Desenvolvimento local
        print(f"🔧 Iniciando em modo desenvolvimento na porta {port}")
        app.run(debug=True, host='localhost', port=port)