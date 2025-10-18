# Exemplo Prático: Framework Analista-Crítico-Júri

Este arquivo demonstra como o DriveBot v3.0 processa uma pergunta usando o framework interno.

## Pergunta do Usuário:
"Faça um ranking das categorias com maior faturamento em janeiro"

## Processo Interno do DriveBot v3.0:

### [ANALISTA INTELIGENTE] - Primeira Análise
- **Intenção identificada**: `ranking` (criar uma lista ordenada)
- **Entidades extraídas**: 
  - `categorias` (coluna para agrupar)
  - `faturamento` (métrica para calcular - provavelmente Receita_Total)
  - `janeiro` (filtro temporal)
- **Ferramenta proposta**: `get_ranking`
- **Parâmetros sugeridos**:
  - `group_by_column`: "Categoria"  
  - `metric_column`: "Receita_Total"
  - `operation`: "sum"
  - `filters`: {"Mes": "Janeiro"}

### [CRÍTICO VIGILANTE] - Validação Rigorosa
- **Verificação das colunas disponíveis**:
  - ✅ "Categoria" existe na lista de colunas
  - ✅ "Receita_Total" existe na lista de colunas  
  - ✅ "Mes" existe na lista de colunas
- **Verificação dos filtros**:
  - ✅ Filtro "Mes = Janeiro" é viável
- **Validação final**: ✅ **APROVADA** - Todos os dados necessários estão disponíveis

### [JÚRI CONSTRUTIVO] - Decisão Final
- **Status**: Proposta validada pelo Crítico
- **Ferramenta selecionada**: `get_ranking`
- **Ação**: Executar análise e formatar resposta

## Resposta Final do DriveBot v3.0:

```markdown
Com base nos dados consolidados, aqui está o ranking das categorias por faturamento em janeiro de 2024:

| Posição | Categoria | Faturamento Total |
|:--------|:----------|:------------------|
| 1 | Eletrônicos | **R$ 245.678,90** |
| 2 | Informática | **R$ 189.234,50** |
| 3 | Casa e Jardim | **R$ 156.789,20** |
| 4 | Livros | **R$ 98.456,30** |

**Insights:**
- A categoria **Eletrônicos** liderou com 32% do faturamento total de janeiro
- As top 3 categorias representaram 76% do faturamento do mês
- Total geral analisado: R$ 690.158,90
```

---

## Exemplo de Pergunta IMPOSSÍVEL:

### Pergunta do Usuário:
"Qual é a margem de lucro por produto?"

### [ANALISTA INTELIGENTE]
- **Intenção**: `calculate_metric` (calcular margem)
- **Entidades**: `margem de lucro`, `produto`
- **Fórmula necessária**: (Receita_Total - Custo) / Receita_Total
- **Colunas necessárias**: "Receita_Total", "Custo", "Produto"

### [CRÍTICO VIGILANTE]
- **Verificação das colunas**:
  - ✅ "Receita_Total" existe
  - ✅ "Produto" existe
  - ❌ **"Custo" NÃO existe** na lista de colunas disponíveis
- **Validação final**: ❌ **REJEITADA** - Dados insuficientes

### [JÚRI CONSTRUTIVO]
- **Status**: Proposta rejeitada pelo Crítico
- **Ação**: Explicar limitação de forma clara e útil

### Resposta Final:
```
Não consigo calcular a margem de lucro por produto. Para isso, eu precisaria de uma coluna com os 'custos' dos produtos, que não foi encontrada nos arquivos analisados.

**Colunas disponíveis para análise:** Data, ID_Transacao, Produto, Categoria, Região, Quantidade, Preço_Unitário, Receita_Total, Mes, Arquivo_Origem

**Análises alternativas que posso fazer:**
- Faturamento por produto
- Quantidade vendida por produto  
- Preço médio por produto
```

---

## Vantagens do Framework v3.0:

1. **Precisão**: Valida dados antes de tentar análises
2. **Transparência**: Explica limitações de forma educativa
3. **Inteligência**: Sugere análises alternativas viáveis
4. **Consistência**: Processo padronizado para todas as perguntas
5. **Confiabilidade**: Evita respostas incorretas ou inventadas