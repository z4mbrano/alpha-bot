# 🏗️ Arquitetura de Dois Prompts - DriveBot

## 🎯 Problema Resolvido

**Antes:** O LLM recebia a pergunta e "alucinava" uma resposta completa com dados fictícios.

**Agora:** O LLM traduz a pergunta → Python executa nos dados REAIS → LLM formata o resultado REAL.

---

## 🔄 Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. USUÁRIO PERGUNTA                                                  │
│    "me fale o produto mais vendido no mes de janeiro"               │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. PROMPT #1: TRADUTOR DE INTENÇÃO                                  │
│    Função: generate_analysis_command()                              │
│                                                                      │
│    Input: Pergunta + Colunas disponíveis                            │
│    Output: JSON estruturado                                         │
│                                                                      │
│    {                                                                 │
│      "tool": "get_ranking",                                          │
│      "params": {                                                     │
│        "group_by_column": "nome_produto",                            │
│        "metric_column": "quantidade",                                │
│        "operation": "sum",                                           │
│        "filters": {"mes_ref": "Jan/2024"},                           │
│        "top_n": 1                                                    │
│      }                                                               │
│    }                                                                 │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. EXECUÇÃO NOS DADOS REAIS                                         │
│    Função: execute_analysis_command()                               │
│                                                                      │
│    - Lê DataFrames do conversation["drive"]["tables"]               │
│    - Aplica filtros (mes_ref == "Jan/2024")                         │
│    - Agrupa por nome_produto                                        │
│    - Soma quantidade                                                │
│    - Ordena e pega top 1                                            │
│                                                                      │
│    Resultado REAL do Pandas:                                        │
│    {                                                                 │
│      "ranking": [                                                    │
│        {"nome_produto": "Teclado Mecânico K8", "quantidade": 45}    │
│      ]                                                               │
│    }                                                                 │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. PROMPT #2: APRESENTADOR DE RESULTADOS                            │
│    Função: format_analysis_result()                                 │
│                                                                      │
│    Input: Pergunta + Resultado REAL                                 │
│    Output: Markdown formatado                                       │
│                                                                      │
│    ## 📊 Produto Mais Vendido em Janeiro                            │
│                                                                      │
│    **Produto:** Teclado Mecânico K8                                 │
│    **Quantidade:** 45 unidades                                      │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. USUÁRIO RECEBE RESPOSTA BASEADA EM DADOS REAIS                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Ferramentas Disponíveis

### 1. `calculate_metric`
Calcula uma única métrica agregada.

**Exemplo:**
```json
{
  "tool": "calculate_metric",
  "params": {
    "metric_column": "valor_venda",
    "operation": "sum",
    "filters": {"regiao": "Sul"}
  }
}
```

**Operações:** `sum`, `mean`, `count`, `min`, `max`

---

### 2. `get_ranking`
Cria um ranking agrupando dados.

**Exemplo:**
```json
{
  "tool": "get_ranking",
  "params": {
    "group_by_column": "nome_produto",
    "metric_column": "quantidade",
    "operation": "sum",
    "filters": {"mes_ref": "Jan/2024"},
    "top_n": 5,
    "ascending": false
  }
}
```

---

### 3. `get_unique_values`
Lista valores únicos de uma coluna.

**Exemplo:**
```json
{
  "tool": "get_unique_values",
  "params": {
    "column": "regiao_venda"
  }
}
```

---

### 4. `get_time_series`
Análise temporal/evolução ao longo do tempo.

**Exemplo:**
```json
{
  "tool": "get_time_series",
  "params": {
    "time_column": "mes_ref",
    "metric_column": "valor_venda",
    "operation": "sum",
    "group_by_column": "regiao"
  }
}
```

---

## 🔍 Como Funciona Internamente

### 1. Descoberta Inicial
Quando o usuário fornece o ID da pasta:

```python
bundle = build_discovery_bundle(drive_id)
# Chama ingest_drive_folder() para LER DADOS REAIS
# Armazena DataFrames em conversation["drive"]["tables"]
```

### 2. Análise de Perguntas
Quando o usuário faz uma pergunta:

```python
# Fase 1: Traduzir pergunta em comando
command = generate_analysis_command(question, available_columns, api_key)

# Fase 2: Executar nos dados REAIS
result = execute_analysis_command(command, tables)

# Fase 3: Formatar resultado
response = format_analysis_result(question, result, api_key)
```

---

## ✅ Garantias de Dados Reais

1. **DataFrames são armazenados:** `conversation["drive"]["tables"]` contém os pandas DataFrames
2. **Filtros são aplicados:** `filtered_df = df[df[column] == value]`
3. **Operações são do Pandas:** `df.groupby().sum()`, `df.mean()`, etc.
4. **Nenhuma invenção:** O LLM NUNCA vê os dados, apenas traduz e formata

---

## 🐛 Debugging

Para verificar se está funcionando, adicione prints:

```python
print(f"[DriveBot] Comando gerado: {json.dumps(command, indent=2)}")
print(f"[DriveBot] Resultado: {json.dumps(result, indent=2)}")
```

---

## 📝 Logs Esperados

```
[DriveBot] Traduzindo pergunta: me fale o produto mais vendido no mes de janeiro
[DriveBot] Comando gerado: {
  "tool": "get_ranking",
  "params": {
    "group_by_column": "nome_produto",
    "metric_column": "quantidade",
    "operation": "sum",
    "filters": {"mes_ref": "Jan/2024"},
    "top_n": 1
  }
}
[DriveBot] Executando análise nos dados reais...
[DriveBot] Resultado da análise: {
  "ranking": [
    {"nome_produto": "Teclado Mecânico K8", "quantidade": 45.0}
  ]
}
[DriveBot] Formatando resultado...
```

---

## 🎉 Resultado Final

O usuário recebe uma resposta **baseada exclusivamente nos dados reais** do Google Drive, sem nenhuma alucinação ou invenção do LLM.
