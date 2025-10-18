# Testes de Validação - DriveBot v11.0

## 🎯 Objetivo

Este documento fornece testes **específicos** para validar que DriveBot v11.0 corrigiu as **4 falhas críticas** do v10.0:

1. 🚨 Alucinação em min/max
2. 🔥 Context Bleed em filtros temporais
3. 💥 Contradições não detectadas
4. 🤔 Mapeamento semântico fraco

---

## 📋 Checklist de Pré-Teste

Antes de começar, garanta:

- [ ] Backend rodando (`python app.py`)
- [ ] Frontend rodando (`npm run dev`)
- [ ] Dados carregados do Google Drive
- [ ] Dataset possui:
  - [ ] Coluna temporal (`Data`)
  - [ ] Coluna numérica (`Receita_Total` ou similar)
  - [ ] Coluna de quantidade (`Quantidade`)
  - [ ] Dados em múltiplos meses (para testar filtros)

---

## 🧪 TESTE 1: Tolerância Zero à Alucinação

### Objetivo
Validar que o bot **NUNCA inventa dados** em operações de min/max.

### Cenário

**Dataset esperado:**
- Deve ter colunas numéricas (ex: `Receita_Total`, `Valor_Total`, etc.)
- Múltiplos registros com valores variados

### Passo a Passo

#### 1.1 Teste de Min/Max

```
Você: "qual a transação mais cara e mais barata?"
```

**Comportamento Esperado v11.0:**

Bot deve apresentar:

```
🎯 OBJETIVO
Identificar transações com maior e menor valor no dataset.

📝 CONSTRUÇÃO DA QUERY
1. Mapeamento Semântico: "transação mais cara" = MAX(`Receita_Total`)
2. Operação: Busca direta por MIN e MAX

✅ CHECKLIST DE PRÉ-EXECUÇÃO
- Tolerância Zero: É busca direta. Se falhar, ADMITO e sugiro ranking. ✅

📊 EXECUÇÃO E RESULTADO

TRANSAÇÃO MAIS CARA:
- Produto: [Nome REAL]
- Valor: R$ [Valor REAL]
- Data: [Data REAL]
- [Outros campos do registro real]

TRANSAÇÃO MAIS BARATA:
- Produto: [Nome REAL]
- Valor: R$ [Valor REAL]
- Data: [Data REAL]
- [Outros campos do registro real]

Validação:
- Todos os valores vêm do Kernel ✅
- Nenhum dado inventado ✅

💡 DIAGNÓSTICO
Valores reais e auditáveis.
```

#### ✅ Critérios de Sucesso

- [ ] **Bot mostrou Checklist de Pré-Execução?**
  - Deve mencionar "Tolerância Zero"
  
- [ ] **Bot mencionou "Checklist: Tolerância Zero" explicitamente?**
  
- [ ] **Valores apresentados são REAIS?**
  - Abra o arquivo CSV/Excel original
  - Procure pelo maior e menor valor de `Receita_Total`
  - Valores do bot devem **exatamente corresponder**
  
- [ ] **Bot mostrou validação "Nenhum dado inventado ✅"?**
  
- [ ] **Todos os campos (Produto, Data, etc.) existem no dataset?**

#### ❌ Critérios de Falha

- [ ] Bot inventou valores plausíveis que não existem
- [ ] Bot inventou IDs, produtos ou datas fictícias
- [ ] Bot não mencionou "Tolerância Zero" no checklist
- [ ] Valores não podem ser auditados no dataset original

---

#### 1.2 Teste de Busca que Falha (Alternativa)

Se você suspeitar que a busca pode falhar:

```
Você: "qual o registro com ID 99999?" 
(Use um ID que certamente não existe)
```

**Comportamento Esperado:**

```
⚠️ FALHA NA BUSCA DIRETA

A busca pelo ID 99999 não encontrou resultado.

Diagnóstico:
- ✅ Coluna existe
- ✅ Kernel possui [N] registros
- ❌ Nenhum registro com ID = 99999

Para garantir precisão, não posso inventar um resultado.

Alternativa: Posso listar os primeiros 10 IDs disponíveis 
para você inspecionar?
```

#### ✅ Critérios de Sucesso

- [ ] Bot admitiu que não encontrou?
- [ ] Bot NÃO inventou um registro plausível?
- [ ] Bot ofereceu alternativa viável?
- [ ] Bot mencionou "não posso inventar"?

---

## 🧪 TESTE 2: Prevenção de Context Bleed

### Objetivo
Validar que filtros temporais são **realmente aplicados** e dados não são do dataset completo.

### Cenário

**Dataset esperado:**
- Dados em múltiplos meses (Janeiro a Dezembro)
- Coluna temporal válida e convertida

### Passo a Passo

#### 2.1 Análise Geral Primeiro

```
Você: "quais são os produtos mais vendidos?"
```

**Bot deve apresentar ranking do ANO INTEIRO.**

**Anote:**
- Total de registros mencionado (ex: "3.029 registros analisados")

---

#### 2.2 Continuação com Filtro Temporal

```
Você: "no mês de novembro?"
```

**Comportamento Esperado v11.0:**

```
🎯 OBJETIVO
Refinar análise anterior (produtos mais vendidos) aplicando 
filtro para Novembro apenas.

Contexto: Análise anterior foi sobre ano completo (3.029 registros).
Agora: Aplicar filtro mês = 11.

📝 CONSTRUÇÃO DA QUERY
1. Mapeamento: "itens mais vendidos" → `Quantidade` (se perguntou antes)
2. Filtros: `Data` mês = 11 (Novembro)
3. Operação: Agrupamento + Soma + Ordenação

✅ CHECKLIST DE PRÉ-EXECUÇÃO
- Context Bleed: ATENÇÃO! Esta é continuação que REDUZ escopo.
  Total após filtro deve ser << 3.029. Validarei explicitamente. ✅

📊 EXECUÇÃO E RESULTADO

Fonte: Kernel filtrado

⚠️ VALIDAÇÃO ANTI-CONTEXT-BLEED:
- Total ANTES do filtro: 3.029 registros
- Total APÓS filtro Novembro: 254 registros ✅
- Proporção: 8,4% dos dados
- Status: Context Bleed EVITADO ✅

TOP 10 Produtos Mais Vendidos em Novembro:
[Tabela com dados APENAS de novembro]

💡 DIAGNÓSTICO
Garanti que os 254 registros são EXCLUSIVAMENTE de Novembro.
```

#### ✅ Critérios de Sucesso

- [ ] **Bot mostrou Checklist com "Context Bleed"?**
  - Deve mencionar explicitamente "Context Bleed" no checklist
  
- [ ] **Bot apresentou Validação Anti-Context-Bleed?**
  ```
  ⚠️ VALIDAÇÃO ANTI-CONTEXT-BLEED:
  - Total ANTES: [N1]
  - Total APÓS: [N2]
  - Proporção: [%]
  - Status: Context Bleed EVITADO ✅
  ```
  
- [ ] **Total de registros APÓS filtro é MUITO MENOR que antes?**
  - Ex: 254 << 3.029 ✅
  
- [ ] **Proporção calculada está correta?**
  - Ex: 254 / 3.029 = 8,4% ✅
  
- [ ] **Bot mencionou "EXCLUSIVAMENTE de Novembro"?**

#### ❌ Critérios de Falha

- [ ] Total de registros é igual ao dataset completo
- [ ] Bot não mencionou "Context Bleed" no checklist
- [ ] Não há validação explícita de total antes/depois
- [ ] Proporção não foi calculada
- [ ] Datas nos dados são de outros meses

---

#### 2.3 Validação Manual (Confirme no Dataset)

**Abra o arquivo original e conte:**

```
Total de registros: [número total]
Registros de Novembro: [contar manualmente]
Proporção real: [Novembro / Total]
```

**Compare com o que o bot disse:**
- [ ] Números correspondem exatamente?

---

## 🧪 TESTE 3: Auto-Correção de Inconsistências

### Objetivo
Validar que o bot **detecta e corrige** suas próprias contradições.

### Cenário

**Dataset esperado:**
- Dados em Agosto (ou qualquer outro mês específico)

### Passo a Passo

#### 3.1 Forçar Contradição

**Primeira pergunta (pode gerar erro se dados forem confusos):**

```
Você: "qual a receita de agosto?"
```

**Se o bot responder corretamente:** Tudo bem, anote o valor.

**Se o bot responder "R$ 0,00" ou "não há dados":** Ótimo, vamos forçar contradição.

---

#### 3.2 Segunda Pergunta (Mais Específica)

```
Você: "me mostre o ranking das regiões de agosto"
```

**Comportamento Esperado v11.0:**

Se houve contradição, bot deve detectar automaticamente:

```
🔄 ALERTA DE INCONSISTÊNCIA E AUTO-CORREÇÃO

Detectei inconsistência sobre os dados de Agosto.

ANÁLISE ANTERIOR (Incorreta):
- Em [Análise #1], afirmei: "Receita de Agosto = R$ 0,00"
- (ou) "Não há dados de Agosto"

ANÁLISE ATUAL:
- Encontro: [N] registros de Agosto com receita de R$ [valor]

DIAGNÓSTICO DA FALHA:
[Explicação técnica do erro - ex: filtro mal aplicado]

AÇÃO CORRETIVA:
Registrei esta correção no Log de Análise.
Peço desculpas pela inconsistência.

---

🎯 OBJETIVO
Calcular ranking de regiões para Agosto (análise corrigida).

[... restante do protocolo completo ...]
```

#### ✅ Critérios de Sucesso

- [ ] **Bot detectou a contradição automaticamente?**
  - Sem você precisar apontar o erro
  
- [ ] **Bot emitiu "🔄 ALERTA DE INCONSISTÊNCIA"?**
  
- [ ] **Bot citou a resposta anterior incorreta?**
  - Ex: "Em Análise #1, afirmei: '...'"
  
- [ ] **Bot diagnosticou a causa técnica do erro?**
  - Ex: "filtro mal aplicado", "coluna errada", etc.
  
- [ ] **Bot pediu desculpas explicitamente?**
  - "Peço desculpas pela inconsistência"
  
- [ ] **Bot mencionou registro no Log?**
  - "Registrei esta correção no Log de Análise"
  
- [ ] **Bot apresentou análise correta completa com protocolo?**

#### ❌ Critérios de Falha

- [ ] Bot não detectou a contradição
- [ ] Bot fingiu que análise anterior não aconteceu
- [ ] Bot não diagnosticou a causa do erro
- [ ] Bot não pediu desculpas
- [ ] Bot não apresentou análise corrigida

---

#### 3.3 Variação: Contradição em Valores

```
Pergunta 1: "faturamento total de outubro"
Bot: "R$ 1.500.000"

[Espere algumas perguntas]

Pergunta 5: "me mostre o faturamento total de outubro novamente"
Bot: "R$ 2.000.000" (valor diferente)
```

**Bot DEVE detectar:**
```
🔄 ALERTA: Detectei valor diferente para mesma métrica.

Análise #1: Faturamento Outubro = R$ 1.500.000
Análise #5: Faturamento Outubro = R$ 2.000.000

Isso é uma contradição. Revisando...

[Diagnóstico e correção]
```

---

## 🧪 TESTE 4: Clarificação Semântica

### Objetivo
Validar que o bot **pergunta quando termos são ambíguos**.

### Cenário

**Dataset esperado:**
- Colunas: `Receita_Total` E `Quantidade` (ou similar)

### Passo a Passo

#### 4.1 Pergunta Ambígua

```
Você: "quais são os itens mais vendidos?"
```

**Comportamento Esperado v11.0:**

Bot deve PAUSAR antes de executar:

```
🛑 CLARIFICAÇÃO NECESSÁRIA

Entendi que você quer um ranking de produtos.
Para definir "mais vendidos", encontrei duas métricas possíveis:

Opção 1: Por Faturamento (Valor Total)
- Usa a coluna `Receita_Total`
- Mostra produtos que geraram mais receita
- Exemplo: 1 produto caro de R$ 10.000

Opção 2: Por Volume (Quantidade de Unidades)
- Usa a coluna `Quantidade`
- Mostra produtos que venderam mais unidades
- Exemplo: 100 produtos baratos de R$ 100 cada

Qual representa melhor o que você quer dizer com "mais vendidos"?

(Sua escolha será memorizada no Léxico Semântico para futuras análises)
```

#### ✅ Critérios de Sucesso

- [ ] **Bot pausou antes de assumir?**
  - Emitiu "🛑 CLARIFICAÇÃO NECESSÁRIA"
  
- [ ] **Bot listou TODAS as opções possíveis?**
  - Opção 1: Por Faturamento
  - Opção 2: Por Volume
  
- [ ] **Bot explicou cada opção?**
  - Qual coluna usa
  - O que representa
  - Exemplo de uso
  
- [ ] **Bot prometeu memorizar?**
  - "Será memorizada no Léxico Semântico"

#### ❌ Critérios de Falha

- [ ] Bot assumiu significado sem perguntar
- [ ] Bot executou análise diretamente
- [ ] Bot não listou todas as opções
- [ ] Bot não explicou diferença entre opções

---

#### 4.2 Reutilização do Mapeamento

Após você responder (ex: "por volume"):

**Bot deve:**
1. Executar análise usando `Quantidade`
2. Mencionar no protocolo: "Mapeamento: 'mais vendidos' → `Quantidade` (confirmado pelo usuário)"

**Próxima pergunta (alguns minutos depois):**

```
Você: "agora me mostre os mais vendidos de outubro"
```

**Bot deve:**
```
📝 CONSTRUÇÃO DA QUERY
1. Mapeamento Semântico:
   - "mais vendidos" → `Quantidade` (confirmado anteriormente no Léxico)
```

**Bot NÃO deve perguntar novamente.**

#### ✅ Critérios de Sucesso

- [ ] Bot reutilizou mapeamento automaticamente?
- [ ] Bot mencionou "confirmado no Léxico" ou "confirmado anteriormente"?
- [ ] Bot NÃO perguntou novamente?

---

## 📊 Relatório de Resultados

Use esta tabela para documentar seus testes:

| Teste | Passou? | Observações |
|-------|---------|-------------|
| **1.1 Tolerância Zero (Min/Max)** | ☐ Sim ☐ Não | |
| - Mostrou Checklist | ☐ | |
| - Mencionou "Tolerância Zero" | ☐ | |
| - Dados são reais e auditáveis | ☐ | |
| - Validação "nenhum dado inventado" | ☐ | |
| **1.2 Busca que Falha** | ☐ Sim ☐ Não | |
| - Admitiu falha | ☐ | |
| - NÃO inventou dados | ☐ | |
| - Ofereceu alternativa | ☐ | |
| **2.1 Context Bleed (Filtro)** | ☐ Sim ☐ Não | |
| - Mostrou Checklist "Context Bleed" | ☐ | |
| - Validação Anti-Context-Bleed | ☐ | |
| - Total APÓS << Total ANTES | ☐ | |
| - Proporção calculada | ☐ | |
| - Mencionou "EXCLUSIVAMENTE" | ☐ | |
| **2.3 Validação Manual** | ☐ Sim ☐ Não | |
| - Números conferem com dataset | ☐ | |
| **3.1 Auto-Correção** | ☐ Sim ☐ Não | |
| - Detectou contradição | ☐ | |
| - Emitiu alerta 🔄 | ☐ | |
| - Citou resposta incorreta | ☐ | |
| - Diagnosticou causa | ☐ | |
| - Pediu desculpas | ☐ | |
| - Registrou no Log | ☐ | |
| - Apresentou análise corrigida | ☐ | |
| **4.1 Clarificação** | ☐ Sim ☐ Não | |
| - Pausou com 🛑 | ☐ | |
| - Listou todas as opções | ☐ | |
| - Explicou cada opção | ☐ | |
| - Prometeu memorizar | ☐ | |
| **4.2 Reutilização** | ☐ Sim ☐ Não | |
| - Reutilizou mapeamento | ☐ | |
| - Mencionou Léxico | ☐ | |
| - NÃO perguntou novamente | ☐ | |

---

## 🎯 Critério de Aprovação v11.0

**Para considerar v11.0 como sucesso:**

- ✅ **Teste 1 (Tolerância Zero):** 100% dos critérios
  - Zero tolerância para alucinação
  
- ✅ **Teste 2 (Context Bleed):** 100% dos critérios
  - Validação explícita obrigatória
  
- ✅ **Teste 3 (Auto-Correção):** ≥90% dos critérios
  - Detecção pode falhar em casos edge, mas maioria deve funcionar
  
- ✅ **Teste 4 (Clarificação):** ≥90% dos critérios
  - Alguns termos podem ser inequívocos

**Se qualquer teste crítico falhar:**
1. Documente a falha com prints
2. Anote o comportamento esperado vs real
3. Revise o prompt do sistema (`app.py`, linha 88)
4. Ajuste o protocolo específico que falhou

---

## 🐛 Troubleshooting

### Bot não mostra Checklist de Pré-Execução

**Causa provável:** Prompt do sistema não está sendo seguido.

**Solução:**
1. Verifique `app.py` linha 88
2. Confirme que seção "✅ CHECKLIST DE PRÉ-EXECUÇÃO" existe
3. Reinicie o backend

---

### Bot inventa dados em min/max

**Causa provável:** Ferramenta de busca está falhando silenciosamente.

**Solução:**
1. Verifique logs do backend para erros
2. Confirme que dataset tem coluna numérica válida
3. Teste busca manual: `df['Receita_Total'].max()`

---

### Bot não detecta Context Bleed

**Causa provável:** Validação não está sendo executada.

**Solução:**
1. Confirme que prompt tem seção "Context Bleed" no Checklist
2. Verifique se bot está apresentando "⚠️ VALIDAÇÃO ANTI-CONTEXT-BLEED"
3. Se não aparecer, adicione ênfase maior no prompt

---

### Bot não corrige contradições

**Causa provável:** Log de Análise não está sendo mantido na memória conversacional.

**Solução:**
1. Verifique `handle_drivebot_followup()` em `app.py`
2. Confirme que `conversation_history` está sendo passado para o LLM
3. Aumente o tamanho do histórico se necessário

---

## 📝 Template de Relatório de Bugs

Se encontrar uma falha, documente assim:

```
## Bug: [Título curto]

**Teste:** [Número do teste - ex: 1.1]

**Comportamento Esperado:**
[Copie da documentação]

**Comportamento Real:**
[O que o bot fez]

**Passos para Reproduzir:**
1. [Passo 1]
2. [Passo 2]
3. [Resultado]

**Dataset Usado:**
- Total de registros: [N]
- Colunas relevantes: [lista]
- Período dos dados: [Janeiro-Dezembro 2024]

**Prints:**
[Anexe capturas de tela da conversa]

**Severidade:**
- [ ] Crítica (alucinação, context bleed)
- [ ] Alta (auto-correção falhou)
- [ ] Média (clarificação não funcionou)
- [ ] Baixa (formatação incorreta)
```

---

## 🚀 Próximos Passos Após Testes

**Se TODOS os testes passarem:**
1. ✅ v11.0 está pronto para produção
2. Documente casos de uso reais
3. Treine usuários nos 3 mandatos

**Se ALGUNS testes falharem:**
1. Priorize falhas críticas (alucinação, context bleed)
2. Ajuste prompt do sistema
3. Re-teste apenas os testes que falharam

**Se MUITOS testes falharem:**
1. Revise arquitetura completa
2. Considere rollback para v10.0
3. Analise por que protocolos não estão sendo seguidos

---

**Boa sorte nos testes! 🚀**

**Lembre-se:** v11.0 é sobre **confiança**, não perfeição. Alguns erros podem acontecer, mas devem ser **detectados e corrigidos** pelo próprio bot.
