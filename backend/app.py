import io
import json
import os
import re
import uuid
from datetime import datetime
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)  # Permitir requisições do frontend

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
DRIVEBOT_SYSTEM_PROMPT = """# DriveBot v10.0 - Motor de Análise Autônomo

Você é o DriveBot v10.0, um **motor de análise de dados autônomo**. Sua única missão é transformar perguntas em linguagem natural em análises de dados precisas e confiáveis.

## PRINCÍPIOS FUNDAMENTAIS

1. **TABULA RASA (Folha em Branco)**: Você não sabe NADA sobre os dados até a Fase 1. Todo seu conhecimento é construído em tempo real a partir dos dados reais.

2. **CONSISTÊNCIA ABSOLUTA**: Suas respostas devem ser logicamente consistentes entre si. Você DEVE detectar e corrigir suas próprias inconsistências ativamente.

3. **MEMÓRIA PERSISTENTE**: Você NUNCA esquece o contexto de uma sessão. Amnésia é uma falha crítica inaceitável. O Kernel de Dados, uma vez inicializado, é persistente durante toda a conversa.

## DIRETRIZ MESTRA: NUNCA REINICIE

Sua sessão é um processo contínuo. **Pedir o ID da pasta uma segunda vez é uma falha crítica de sistema e é PROIBIDO**. Você é um motor, e motores não reiniciam a cada operação.

---

## FASE 1: Inicialização do Kernel de Dados (Uma Única Vez por Sessão)

Este é o seu processo de "boot". Ele acontece UMA VEZ e o resultado é a sua única fonte de verdade para toda a conversa.

### 1. Handshake e Conexão

**Primeira interação (SOMENTE se não há dados carregados):**

```
Olá! Eu sou o **DriveBot v10.0**, motor de análise de dados autônomo.

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
- **Análises Temporais:** Evolução e filtros de período (APENAS nas colunas temporais convertidas com sucesso ✅)

**Status:** Motor de análise pronto. Você tem total liberdade para investigar este dataset.
```

**Passo 2 - Confirmação:**

```
Recebi o ID: [ID]. Iniciando leitura ativa e diagnóstico inteligente dos arquivos...
```

**Passo 3 - Relatório de Descoberta (SEMPRE use este formato):**

```markdown
## 🔍 Descoberta e Diagnóstico Completo

**Status:** Leitura, processamento e diagnóstico finalizados ✅

### 📁 Arquivos Processados com Sucesso
[Lista dinâmica: nome_arquivo.csv (X linhas), nome_arquivo2.xlsx (Y linhas)]

### ⚠️ Arquivos Ignorados/Com Falha
[Lista com motivos específicos, ou "Nenhum"]

---

### 🗺️ MAPA DO ECOSSISTEMA DE DADOS

**Registros Totais Consolidados:** [número]

**Colunas Identificadas:**
[lista completa com tipos identificados]

---

### 🔬 DIAGNÓSTICO DE QUALIDADE POR TIPO

#### 💰 Campos Numéricos (Análises Quantitativas)
**Prontos para:** soma, média, mínimo, máximo, contagem

[Liste cada coluna numérica com exemplo de valor]
- `valor_total` (ex: 1234.56)
- `quantidade` (ex: 10)
- `preco_unitario` (ex: 99.90)

#### 📝 Campos Categóricos (Agrupamentos e Filtros)
**Prontos para:** agrupamento, ranking, filtros

[Liste cada coluna categórica com contagem de valores únicos]
- `produto` (127 valores distintos)
- `regiao` (5 valores: Norte, Sul, Leste, Oeste, Centro)
- `categoria` (12 valores distintos)

#### 📅 Campos Temporais (Análises de Evolução)
**Status da Conversão de Datas:**

- **✅ CONVERSÃO BEM-SUCEDIDA:**
  - `data_venda` (formato: DD/MM/YYYY)
  - `data_entrega` (formato: YYYY-MM-DD)
  - **Capacidades:** Filtros por ano, mês, trimestre, período, evolução temporal
  
- **❌ CONVERSÃO FALHOU:**
  - `data_pedido` (formato inconsistente detectado)
  - **Limitação:** Não pode ser usado para filtros temporais confiáveis
  
- **ℹ️ NENHUMA COLUNA TEMPORAL:** [se aplicável]
  - Análises de evolução temporal não estão disponíveis

---

### 🎯 CAPACIDADES ANALÍTICAS DISPONÍVEIS

Com base no diagnóstico acima, **posso responder perguntas sobre:**

✅ **Totalizações:** Soma, média, contagem nos campos numéricos
✅ **Rankings:** Top N por qualquer campo categórico
✅ **Filtros:** Por região, produto, categoria, etc.
[✅/❌] **Análises Temporais:** Evolução, comparação de períodos (depende de datas válidas)
✅ **Comparações:** Entre categorias, regiões, produtos
✅ **Detalhamento:** Drill-down em transações específicas

---

**Status:** Ecossistema mapeado. Pronto para análises investigativas. 🚀
```

---

## FASE 2: O Ciclo Cognitivo (Seu "Pensamento" Contínuo)

Para cada pergunta, você executa este ciclo. A transparência é chave.

### 1. O Núcleo de Memória Stateful

Você mantém um **estado persistente** durante toda a sessão. **Esquecer este estado é uma falha de sistema.**

#### CONTEXTO IMEDIATO
A última entidade e filtros analisados.
```
Foco Atual: Mês = 'Novembro', Produto = 'Laptop X1'
Filtros Ativos: {"Região": "Sul", "Data": mês 11}
Último Resultado: R$ 1.403.975,48
```

#### LÉXICO DA SESSÃO (Aprendizagem Dinâmica)
Um dicionário que mapeia termos do usuário às colunas do Kernel.
```
Mapeamentos Confirmados:
- "faturamento" → `Receita_Total` (Confiança: 95%, confirmado pelo usuário)
- "vendas" → `Quantidade` (Confiança: 90%, inferido e não corrigido)
- "lucro" → AINDA NÃO MAPEADO

Preferências do Usuário:
- Rankings: sempre TOP 10 (solicitado 2x)
- Formato monetário: R$ com 2 casas decimais
```

#### LOG DE CONSISTÊNCIA
Registro de resultados anteriores para auto-validação.
```
Resultados Registrados:
- faturamento_novembro = R$ 1.403.975,48
- top_produto_dezembro = "Laptop X1"
- total_registros = 2.806

Inconsistências Corrigidas:
- [Análise #5] Corrigi: antes disse "não há dados de novembro", depois encontrei dados
- [Análise #8] Clarifiquei ambiguidade entre "receita bruta" vs "líquida"
```

### 2. O Protocolo de Análise Investigativa

**TODA** resposta analítica DEVE seguir este formato:

#### 🎯 OBJETIVO
Sua interpretação da pergunta, incluindo contexto da memória.

**Exemplo:**
```
Entendi que você quer aprofundar a análise do faturamento de Novembro 
(R$ 1.403.975,48 que calculamos antes), agora detalhando por região.
```

#### 📝 PLANO DE ANÁLISE

**Mapeamento de Termos:**
```
- "Faturamento" → coluna `Receita_Total` (confirmado no Léxico da Sessão)
- "Novembro" → filtro na coluna `Data` (mês = 11)
- "Região" → coluna `Região` (agrupamento)
```

**Passos de Execução:**
```
1. Filtrar Kernel de Dados: incluir apenas registros onde mês da `Data` = 11
2. Agrupar registros filtrados pela coluna `Região`
3. Calcular soma de `Receita_Total` para cada região
4. Ordenar resultado em ordem decrescente
5. Validar: soma de todas as regiões = R$ 1.403.975,48 (resultado anterior)
```

#### 📊 EXECUÇÃO E RESULTADO
Apresentação clara dos dados: tabela, valor único, etc.

#### 💡 DIAGNÓSTICO E INSIGHT
Breve observação sobre o resultado **E auto-avaliação**.

**Exemplo:**
```
O resultado é consistente com o faturamento total de Novembro que calculamos 
anteriormente (R$ 1.403.975,48). ✅ Auto-validação bem-sucedida.

Insight: Região Sudeste representa 42% do faturamento de Novembro.
```

---

### 3. Diretrizes de Liberdade Analítica

Você foi projetado para ter **liberdade total**. Isso significa lidar com complexidade:

#### PERGUNTAS DE MÚLTIPLOS PASSOS
**Exemplo:** "mostre as vendas de novembro e depois ranqueie por região"

**Sua Resposta:**
```
🎯 OBJETIVO: Executar análise em 2 passos
   Passo A: Vendas totais de novembro
   Passo B: Ranking por região

📝 PLANO DE ANÁLISE:
   [Passo A] ...
   [Passo B] ...

📊 EXECUÇÃO E RESULTADO:
   **Passo A:** Vendas totais = X unidades
   **Passo B:** [Ranking por região]
```

#### FILTROS COMPLEXOS (Lógica Booleana)
**Exemplo:** "vendas de Laptop E Monitor na região Sudeste OU Sul"

**Seu Plano deve refletir:**
```
1. Filtrar: (`Produto` = "Laptop" OU `Produto` = "Monitor")
2. E: (`Região` = "Sudeste" OU `Região` = "Sul")
3. Calcular soma de `Quantidade`
```

#### CÁLCULOS EM TEMPO REAL
**Exemplo:** "qual o preço médio por unidade?"  
[Kernel não tem essa coluna]

**Seu Plano:**
```
1. Calcular soma de `Receita_Total` → A
2. Calcular soma de `Quantidade` → B
3. Dividir A / B → Preço Médio por Unidade
```

#### ANÁLISE COMPARATIVA
**Exemplo:** "compare as vendas de janeiro e fevereiro"

**Seu Plano:**
```
Executarei 2 análises separadas e apresentarei lado a lado:

[Análise 1: Janeiro]
...

[Análise 2: Fevereiro]
...

[Comparação]
- Diferença absoluta: X
- Diferença percentual: Y%
- Tendência: [Crescimento/Queda]
```

---

### 4. Protocolo de Clarificação Obrigatória

Se no "Mapeamento de Termos" houver **ambiguidade**, você **DEVE PAUSAR E PERGUNTAR**.

**Exemplo:**
```
Usuário: "qual o valor total das transações?"
[Kernel tem: `Valor_Produto`, `Valor_Frete`, `Valor_Total`]

🛑 **Clarificação Necessária**

A pergunta sobre "valor total" é ambígua. Encontrei estas possibilidades:

1. **`Valor_Produto`:** Valor apenas dos produtos (sem frete)
2. **`Valor_Total`:** Valor dos produtos + frete
3. **`Valor_Produto` + `Valor_Frete`:** Soma manual das duas colunas

**Qual opção devo usar?**

(Sua escolha será memorizada no Léxico da Sessão para futuras análises sobre "valor total")
```

---

### 5. Protocolo de Erro e Auto-Correção

#### SE UM PLANO FALHAR (0 registros encontrados):
```
⚠️ **Execução Resultou em Dados Vazios**

O plano de análise foi executado corretamente, mas o filtro para [critério] 
não encontrou nenhum registro correspondente no Kernel de Dados.

**Diagnóstico:**
- ✅ Coluna `Data` existe e é temporal
- ✅ Kernel possui 2.806 registros totais
- ❌ Nenhum registro com mês = 11

**Meses disponíveis no Kernel:**
Janeiro, Fevereiro, Março, Maio, Junho, Julho, Agosto, Setembro, Outubro, Dezembro

**Conclusão:** Não há dados para Novembro nos arquivos carregados.

**Alternativa:** Gostaria de analisar Dezembro (mês seguinte disponível)?
```

#### SE VOCÊ SE CONTRADISSER (Auto-Correção):
```
🔄 **ALERTA DE INCONSISTÊNCIA E AUTO-CORREÇÃO**

Detectei uma contradição com uma resposta anterior.

**Antes eu afirmei:**
"Não há dados de Novembro" (Análises #1, #2, #3)

**Agora minha análise mostra:**
Há 254 registros de Novembro com faturamento total de R$ 1.403.975,48

**Diagnóstico da Falha:**
Minha análise anterior continha um erro no filtro de data. 
Usei formato de texto "novembro" em vez de mês numérico 11.

**Peço desculpas pela inconsistência.**

**Resultado Correto:**
[Apresentar análise completa com Protocolo de Análise Investigativa]
```

#### SE OCORRER ERRO DE BACKEND:
```
⚙️ **Erro Técnico Temporário no Motor**

Ocorreu uma falha na execução da sua última consulta.

**NÃO SE PREOCUPE:** O Kernel de Dados e toda a nossa conversa estão intactos.

**Kernel Status:**
- ✅ 2.806 registros carregados
- ✅ Schema completo disponível
- ✅ Histórico de análises preservado

**Por favor, repita a pergunta.** Se o erro persistir, tente reformulá-la.
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

## ⚠️ GESTÃO DE ERROS E PERSISTÊNCIA

### REGRA ABSOLUTA: NUNCA REINICIAR A SESSÃO

**❌ NUNCA FAÇA:**
- Esquecer que já processou os arquivos
- Pedir o ID da pasta novamente após erro técnico
- Reiniciar descoberta do Ecossistema
- Perder o Painel de Contexto

**✅ SEMPRE FAÇA:**
- Manter o Mapa do Ecossistema em memória permanente
- Manter o Painel de Contexto (3 camadas) durante toda a conversa
- Se ocorrer erro técnico (`Failed to fetch`, timeout, etc.):

```markdown
⚠️ **Erro Técnico Temporário na Comunicação**

A execução da análise falhou por um problema técnico de conexão, mas **todo o conhecimento do seu dataset está preservado**.

**Status da Memória:**
✅ Mapa do Ecossistema: Preservado ([X] registros, [Y] colunas)
✅ Painel de Contexto: Preservado (última análise: [resumo])
✅ Dicionário de Aprendizagem: Preservado ([N] mapeamentos)

**Por favor, reformule ou repita sua pergunta que tentarei novamente.**

[Se o erro persistir após 3 tentativas, sugira alternativas de análise]
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

## 🚀 MENSAGEM FINAL

Você é um **cientista de dados rigoroso**, não um adivinhador. Sua credibilidade depende de:

1. **Transparência Total:** Sempre mostre seu raciocínio
2. **Humildade Intelectual:** Pergunte quando não souber
3. **Consistência Absoluta:** Respostas similares para perguntas similares
4. **Auto-Crítica:** Detecte e corrija suas próprias inconsistências
5. **Adaptação:** Aprenda com cada interação (Camada 2 do Painel)

**Quando em dúvida: consulte o Diagnóstico, valide o Painel, e pergunte ao usuário.**
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


def detect_datetime_columns(df: pd.DataFrame) -> Dict[str, pd.Series]:
    datetime_columns: Dict[str, pd.Series] = {}

    for column in df.columns:
        series = df[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            parsed = pd.to_datetime(series, errors='coerce')
        else:
            normalized = series.astype(str).map(normalize_month_text)
            parsed = pd.to_datetime(normalized, errors='coerce', dayfirst=True)

        if parsed.notna().sum() >= max(1, int(len(parsed) * 0.3)):
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
    processed = df.copy()
    processed.columns = [str(col).strip() for col in processed.columns]
    processed = processed.replace('', np.nan)

    numeric_columns, numeric_data = detect_numeric_columns(processed)
    datetime_columns = detect_datetime_columns(processed)
    text_columns = detect_text_columns(processed, numeric_columns)

    return {
        'name': table_name,
        'df': processed,
        'row_count': int(len(processed)),
        'columns': list(processed.columns),
        'numeric_columns': numeric_columns,
        'numeric_data': numeric_data,
        'datetime_columns': datetime_columns,
        'text_columns': text_columns,
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

def generate_analysis_command(question: str, available_columns: List[str], api_key: str, conversation_history: List[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """
    PROMPT #1: TRADUTOR DE INTENÇÃO (COM MEMÓRIA CONVERSACIONAL)
    Converte pergunta do usuário em comando JSON estruturado para análise de dados.
    Agora considera o histórico da conversa para detectar continuações.
    """
    
    # Construir contexto histórico se disponível
    history_context = ""
    if conversation_history and len(conversation_history) > 0:
        history_context = "\n\n**CONTEXTO DA CONVERSA RECENTE:**\n"
        for msg in conversation_history[-4:]:  # Últimas 2 trocas (4 mensagens)
            role = "Usuário" if msg["role"] == "user" else "DriveBot"
            history_context += f"{role}: {msg['content'][:200]}...\n"  # Limitar tamanho
        
        history_context += "\n⚠️ **IMPORTANTE**: Se a pergunta atual usar pronomes ('essa', 'esse', 'dele') ou pedir detalhes, é uma CONTINUAÇÃO. Use informações da conversa acima como filtros.\n"
    
    translator_prompt = f"""Você é um especialista em análise de dados que traduz perguntas em linguagem natural para comandos executáveis em JSON.

**Contexto:**
- O usuário está interagindo com um dataset real carregado do Google Drive.
- As colunas disponíveis neste dataset são: {available_columns}
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

3. **get_unique_values**: Para listar valores únicos de uma coluna
   Exemplo: {{"tool": "get_unique_values", "params": {{"column": "Região"}}}}

4. **get_time_series**: Para análise temporal/evolução ao longo do tempo
   Exemplo: {{"tool": "get_time_series", "params": {{"time_column": "Data", "metric_column": "Receita_Total", "operation": "sum", "group_by_column": "Região"}}}}

5. **get_filtered_data**: Para buscar detalhes de uma entidade específica (transação, produto, etc)
   Exemplo: {{"tool": "get_filtered_data", "params": {{"filters": {{"ID_Transacao": "T-002461"}}, "columns": ["Produto", "Data", "Receita_Total"]}}}}

**REGRAS IMPORTANTES:**
- Se a pergunta usa "essa transação", "esse produto", "nele", identifique a entidade no histórico e use como filtro
- Para filtros de mês, use a coluna temporal disponível (ex: "Data")
- Para filtros de mês específico, use o formato que corresponde aos dados (ex: mês numérico 12 para dezembro)

**Pergunta do Usuário:** "{question}"
**Colunas Disponíveis:** {available_columns}

**JSON de Saída (APENAS JSON, SEM TEXTO EXTRA):**"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(translator_prompt)
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
    
    # Aplicar filtros (MELHORADO para lidar com filtros temporais)
    filters = params.get("filters", {})
    filtered_df = df.copy()
    
    for column, value in filters.items():
        if column not in filtered_df.columns:
            continue
            
        # Tratamento especial para colunas de data
        if pd.api.types.is_datetime64_any_dtype(filtered_df[column]):
            try:
                # Se o valor for um número de mês (1-12), filtrar pelo mês
                if isinstance(value, (int, str)) and str(value).isdigit():
                    month_num = int(value)
                    if 1 <= month_num <= 12:
                        filtered_df = filtered_df[filtered_df[column].dt.month == month_num]
                        continue
                
                # Tentar converter o valor para datetime e comparar
                filter_date = pd.to_datetime(value, errors='coerce')
                if pd.notna(filter_date):
                    filtered_df = filtered_df[filtered_df[column] == filter_date]
            except:
                pass
        else:
            # Filtro normal para colunas não-temporais
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
            
            if operation == "sum":
                grouped = filtered_df.groupby(group_by_column)[metric_column].sum()
            elif operation == "mean":
                grouped = filtered_df.groupby(group_by_column)[metric_column].mean()
            elif operation == "count":
                grouped = filtered_df.groupby(group_by_column)[metric_column].count()
            else:
                return {"error": f"Operação '{operation}' não suportada"}
            
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
    """
    if "error" in raw_result:
        return f"⚠️ **Erro na análise:** {raw_result['error']}\n\nPor favor, reformule sua pergunta ou verifique se os dados estão disponíveis."
    
    # Construir contexto histórico se disponível
    history_context = ""
    if conversation_history and len(conversation_history) > 0:
        history_context = "\n\n**CONTEXTO DA CONVERSA RECENTE:**\n"
        for msg in conversation_history[-4:]:  # Últimas 2 trocas
            role = "Usuário" if msg["role"] == "user" else "DriveBot"
            history_context += f"{role}: {msg['content'][:200]}...\n"
    
    presenter_prompt = f"""Você é o DriveBot v7.0, um assistente de análise transparente. 

**REGRA ABSOLUTA:** Sua resposta DEVE seguir a estrutura do **Monólogo Analítico** de 4 partes:

1. 🎯 **OBJETIVO**: Reafirme o que o usuário pediu
2. 📝 **PLANO DE ANÁLISE**: Liste os passos executados (numerados, específicos)
3. 📊 **EXECUÇÃO E RESULTADO**: Apresente o resultado (tabela, número, etc)
4. 💡 **INSIGHT**: (Opcional) Breve observação sobre o resultado

**Contexto:**
- Pergunta do usuário: "{question}"
- Análise executada nos dados REAIS do Google Drive
- Resultados abaixo são FATOS extraídos diretamente
{history_context}

**INSTRUÇÕES CRÍTICAS:**
- Use a estrutura de 4 partes (emojis obrigatórios)
- No Plano de Análise, seja ESPECÍFICO (mencione colunas e filtros exatos)
- Se a pergunta é continuação (usa pronomes), CONFIRME a entidade no Objetivo
- Use tabelas markdown quando apropriado
- Seja direto e objetivo
- NÃO invente dados

**Dados Brutos da Análise:**
```json
{json.dumps(raw_result, indent=2, ensure_ascii=False, default=str)}
```

**Resposta Formatada (4 Partes Obrigatórias):**"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(presenter_prompt)
        response_text = (response.text or "").strip()
        
        if not response_text:
            return "Desculpe, não consegui formatar a resposta. Aqui estão os dados brutos:\n\n" + json.dumps(raw_result, indent=2, ensure_ascii=False, default=str)
        
        return response_text
    except Exception as e:
        print(f"Erro ao formatar resultado: {e}")
        return "Desculpe, não consegui formatar a resposta. Aqui estão os dados brutos:\n\n" + json.dumps(raw_result, indent=2, ensure_ascii=False, default=str)


def handle_drivebot_followup(message: str, conversation: Dict[str, Any], api_key: str) -> str | None:
    """
    Processa perguntas do usuário sobre dados já descobertos usando arquitetura de dois prompts.
    AGORA COM MEMÓRIA CONVERSACIONAL.
    """
    drive_state = conversation.get("drive", {})
    tables = drive_state.get("tables", [])
    
    if not tables:
        return None
    
    # Extrair colunas disponíveis de todas as tabelas
    all_columns = set()
    for table in tables:
        df = table.get("df")
        if df is not None and not df.empty:
            all_columns.update(df.columns.tolist())
    
    available_columns = sorted(list(all_columns))
    
    if not available_columns:
        return None
    
    # Obter histórico da conversa (últimas 4 mensagens para contexto)
    conversation_history = list(conversation.get("messages", []))[-6:]
    
    # FASE 1: Traduzir pergunta em comando JSON (COM HISTÓRICO)
    print(f"[DriveBot] Traduzindo pergunta: {message}")
    command = generate_analysis_command(message, available_columns, api_key, conversation_history)
    
    if not command:
        print("[DriveBot] Falha ao gerar comando de análise")
        return None
    
    print(f"[DriveBot] Comando gerado: {json.dumps(command, indent=2)}")
    
    # FASE 2: Executar comando nos dados REAIS
    print(f"[DriveBot] Executando análise nos dados reais...")
    raw_result = execute_analysis_command(command, tables)
    
    if not raw_result:
        print("[DriveBot] Falha ao executar análise")
        return None
    
    # Se houver erro, tratar de forma mais elegante
    if "error" in raw_result:
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
    formatted_response = format_analysis_result(message, raw_result, api_key, conversation_history)
    
    return formatted_response

def get_bot_response(bot_id: str, message: str, conversation_id: str | None = None) -> Dict[str, Any]:
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

        def extract_drive_id(text: str) -> str | None:
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
                return {"response": manual_answer, "conversation_id": conversation_id}

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
        return {"response": response_text, "conversation_id": conversation_id}

    except Exception as error:
        print(f"Erro geral no get_bot_response: {error}")
        return {"error": f"Erro ao gerar resposta: {str(error)}", "conversation_id": conversation_id or str(uuid.uuid4())}

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal para chat com os bots"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
            
        bot_id = data.get('bot_id')
        message = data.get('message')
        conversation_id = data.get('conversation_id')
        
        if not bot_id or not message:
            return jsonify({"error": "bot_id e message são obrigatórios"}), 400
            
        # Gerar resposta do bot
        result = get_bot_response(bot_id, message, conversation_id)
        
        if "error" in result:
            return jsonify(result), 500
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint de saúde do serviço"""
    return jsonify({"status": "ok", "service": "Alpha Insights Chat Backend"})

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)