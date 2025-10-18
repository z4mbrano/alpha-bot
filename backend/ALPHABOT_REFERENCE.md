# 🤖 AlphaBot - Guia de Referência Rápida

## **O Que É o AlphaBot?**

O **AlphaBot** é um especialista em análise de dados que processa múltiplos arquivos (.csv, .xlsx), consolida os dados e responde perguntas complexas usando um **Motor de Validação Interna** com três personas:

1. **O Analista** - Executa cálculos técnicos
2. **O Crítico** - Desafia suposições e procura vieses
3. **O Júri** - Sintetiza a resposta final com insights e limitações

---

## **Arquitetura**

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND                                                    │
│  - Upload de arquivos (.csv, .xlsx)                         │
│  - Chat interface                                            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  ENDPOINT: /api/alphabot/upload                             │
│  - Recebe múltiplos arquivos                                │
│  - Valida extensões (.csv, .xlsx)                           │
│  - Consolida em DataFrame único                             │
│  - Cria colunas auxiliares temporais                        │
│  - Retorna session_id                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  ARMAZENAMENTO: ALPHABOT_SESSIONS (in-memory)               │
│  session_id → {                                             │
│    "dataframe": "<JSON>",                                   │
│    "metadata": {...}                                        │
│  }                                                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  ENDPOINT: /api/alphabot/chat                               │
│  - Recebe session_id + message                             │
│  - Recupera DataFrame da sessão                             │
│  - Executa Motor de Validação Interna:                     │
│    1. ANALISTA: Análise técnica                            │
│    2. CRÍTICO: Desafios e contexto                         │
│    3. JÚRI: Resposta final estruturada                     │
│  - Retorna resposta formatada                              │
└─────────────────────────────────────────────────────────────┘
```

---

## **Endpoints**

### **1. Upload de Arquivos**

**Endpoint:** `POST /api/alphabot/upload`

**Request:**
```
Content-Type: multipart/form-data

files: [arquivo1.csv, arquivo2.xlsx, ...]
```

**Response (Sucesso):**
```json
{
  "status": "success",
  "message": "2 arquivo(s) processado(s) com sucesso.",
  "session_id": "uuid-da-sessao",
  "files_success": ["vendas_janeiro.csv", "vendas_fevereiro.xlsx"],
  "files_failed": [],
  "metadata": {
    "total_records": 100,
    "total_columns": 8,
    "date_range": {
      "min": "2024-01-01",
      "max": "2024-02-28"
    }
  }
}
```

**Response (Erro):**
```json
{
  "status": "error",
  "message": "Nenhum arquivo válido foi processado.",
  "files_failed": [
    {
      "filename": "documento.txt",
      "reason": "Formato não suportado"
    }
  ]
}
```

---

### **2. Chat com Motor de Validação**

**Endpoint:** `POST /api/alphabot/chat`

**Request:**
```json
{
  "session_id": "uuid-da-sessao",
  "message": "Qual foi o produto mais vendido?"
}
```

**Response (Sucesso):**
```json
{
  "answer": "**Resposta Direta:** O produto mais vendido foi Mouse, com 11 unidades.\n\n**Análise Detalhada:** ...",
  "session_id": "uuid-da-sessao",
  "metadata": {
    "records_analyzed": 100,
    "columns_available": 8
  }
}
```

**Response (Erro - Sessão Inexistente):**
```json
{
  "error": "Sessão não encontrada. Por favor, faça upload dos arquivos primeiro.",
  "session_id": "uuid-invalido"
}
```

---

## **Motor de Validação Interna**

### **Como Funciona:**

Cada pergunta passa por 3 etapas internas (invisíveis ao usuário):

#### **ETAPA 1: O ANALISTA**
- Executa a análise técnica nos dados
- Identifica colunas relevantes
- Aplica filtros, agregações, rankings
- Formula resposta preliminar

**Exemplo Interno:**
```
"Filtrando coluna 'Produto', agrupando por 'Produto', 
somando 'Quantidade'... Mouse: 11 unidades."
```

#### **ETAPA 2: O CRÍTICO**
- Desafia a análise do Analista
- Procura vieses ou suposições não validadas
- Identifica dados ausentes
- Propõe interpretações alternativas

**Exemplo Interno:**
```
"A análise considera apenas quantidade vendida. 
E quanto ao faturamento? Mouse pode ter alto volume mas baixo valor."
```

#### **ETAPA 3: O JÚRI**
- Sintetiza as duas perspectivas
- Formula resposta final estruturada
- Inclui limitações quando relevante

**Formato de Saída:**
```
**Resposta Direta:** [Frase clara e concisa]

**Análise Detalhada:** [Como chegou ao resultado]

**Insights Adicionais:** [Observações valiosas]

**Limitações e Contexto:** [Se aplicável]
```

---

## **Processamento de Dados**

### **Colunas Auxiliares Temporais**

Para cada coluna de data detectada (ex: `Data`), o sistema cria automaticamente:

- `Data_Ano` → Ano (ex: 2024)
- `Data_Mes` → Mês numérico (1-12)
- `Data_Mes_Nome` → Mês por extenso minúsculo (ex: "janeiro")
- `Data_Trimestre` → Trimestre (1-4)

**Exemplo:**
```python
# Dados originais
Data: 2024-01-15

# Colunas criadas automaticamente
Data_Ano: 2024
Data_Mes: 1
Data_Mes_Nome: "january"  # locale-dependent
Data_Trimestre: 1
```

---

## **Exemplo de Uso Completo**

### **1. Upload de Arquivos**

```bash
curl -X POST http://localhost:5000/api/alphabot/upload \
  -F "files=@vendas_jan.csv" \
  -F "files=@vendas_fev.xlsx"
```

**Resposta:**
```json
{
  "status": "success",
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "files_success": ["vendas_jan.csv", "vendas_fev.xlsx"],
  "metadata": {
    "total_records": 50,
    "total_columns": 10
  }
}
```

### **2. Fazer Perguntas**

```bash
curl -X POST http://localhost:5000/api/alphabot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "message": "Qual foi o faturamento total?"
  }'
```

**Resposta:**
```json
{
  "answer": "**Resposta Direta:** O faturamento total foi R$ 15.250,00.\n\n**Análise Detalhada:** Este resultado foi obtido ao somar a coluna 'Preco' multiplicada pela 'Quantidade' para todos os 50 registros consolidados...\n\n**Insights Adicionais:** O mês de fevereiro representou 55% do faturamento total...\n\n**Limitações e Contexto:** Os dados abrangem apenas janeiro e fevereiro de 2024."
}
```

---

## **Testes**

### **Executar Testes Automatizados**

```bash
cd backend
python test_alphabot.py
```

**Testes Incluídos:**
1. ✅ Upload de múltiplos arquivos (.csv + .xlsx)
2. ✅ Chat com motor de validação (3 perguntas)
3. ✅ Validação de sessão inexistente (404)

---

## **Configuração**

### **Variáveis de Ambiente**

```bash
# .env
ALPHABOT_API_KEY=sua-chave-gemini-aqui
```

### **Dependências**

```bash
pip install flask pandas openpyxl google-generativeai
```

---

## **Comparação: DriveBot vs AlphaBot**

| Característica | DriveBot | AlphaBot |
|---------------|----------|----------|
| **Fonte de Dados** | Google Drive (ID de pasta) | Upload direto (.csv, .xlsx) |
| **Sessão** | Por conversation_id | Por session_id |
| **Validação** | Monólogo Analítico (4 partes) | Motor de 3 Personas |
| **Colunas Auxiliares** | Criadas automaticamente | Criadas automaticamente |
| **Stateless** | Não (usa CONVERSATION_STORE) | Sim (ALPHABOT_SESSIONS) |
| **Endpoint** | `/api/chat` (bot_id=drivebot) | `/api/alphabot/chat` |

---

## **Boas Práticas**

### **✅ DO:**
- Upload arquivos com estrutura consistente (mesmas colunas)
- Use nomes descritivos para colunas
- Inclua coluna de data quando possível
- Faça perguntas específicas

### **❌ DON'T:**
- Não misture arquivos com estruturas completamente diferentes
- Não envie arquivos corrompidos ou vazios
- Não assuma que o bot "lembra" de conversas anteriores sem session_id
- Não espere análise de arquivos .txt ou .pdf

---

## **Troubleshooting**

### **Problema: "Sessão não encontrada"**
**Causa:** session_id inválido ou expirado  
**Solução:** Faça upload dos arquivos novamente

### **Problema: "Nenhum arquivo válido processado"**
**Causa:** Arquivos com extensão incorreta ou corrompidos  
**Solução:** Verifique se arquivos são .csv ou .xlsx válidos

### **Problema: Resposta não estruturada**
**Causa:** Prompt do motor de validação não está sendo seguido  
**Solução:** Verifique ALPHABOT_SYSTEM_PROMPT no app.py

---

## **Próximos Passos**

1. ✅ Implementado: Upload + Chat + Motor de Validação
2. 🔄 Próximo: Integração com frontend
3. 🔄 Próximo: Persistência de sessões (Redis/PostgreSQL)
4. 🔄 Próximo: Exportar análises (PDF, Excel)
5. 🔄 Próximo: Visualizações (gráficos, dashboards)

---

**Versão:** AlphaBot v1.0  
**Data:** 2025-10-18  
**Status:** ✅ Implementado e Testado
