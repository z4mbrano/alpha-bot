# 🧪 Testes de Memória Conversacional - DriveBot v6.0

## Como Testar

Use o frontend e faça as seguintes sequências de perguntas:

---

## ✅ Teste 1: Aprofundamento de Transação (O Bug Original)

### Sequência:
```
1. "Qual foi a transação com maior faturamento?"
2. "em que mes ocorreu essa transação?"
3. "e qual foi o produto?"
4. "qual foi a quantidade?"
```

### Resultado Esperado (v6.0):

**Pergunta 1:**
```
A transação com maior faturamento foi **T-002461** com R$ 17.992,24
```

**Pergunta 2:**
```
A transação **T-002461** ocorreu em **Novembro de 2024**.
```
✅ **DEVE confirmar o ID T-002461** (não esquecer!)

**Pergunta 3:**
```
O produto vendido na transação **T-002461** foi o **Laptop X1**.
```
✅ **DEVE confirmar o ID T-002461** (ainda lembra!)

**Pergunta 4:**
```
A quantidade vendida na transação **T-002461** foi **X unidades**.
```
✅ **DEVE confirmar o ID T-002461** (memória persistente!)

### Resultado INCORRETO (v5.0):
```
❌ Pergunta 2: "As transações foram em janeiro, fevereiro..." (ESQUECEU!)
❌ Pergunta 3: "Os produtos são: Laptop X1, Monitor..." (ESQUECEU!)
```

---

## ✅ Teste 2: Consistência em Filtros (O Bug de Inconsistência)

### Sequência:
```
1. "rank dos produtos com maior faturamento no mes de dezembro"
2. "faça um rank dos produtos com maior receita total no mes de dezembro"
```

### Resultado Esperado (v6.0):

**Ambas as perguntas devem dar EXATAMENTE a mesma resposta!**

```
| Posição | Produto | Receita Total |
|---------|---------|---------------|
| 1       | Laptop X1 | R$ 3.958.061,51 |
| 2       | Laptop Pro Z | R$ 2.456.724,43 |
...
```

✅ **Ranking idêntico nas duas perguntas**

### Resultado INCORRETO (v5.0):
```
❌ Pergunta 1: "Não há dados de dezembro"
❌ Pergunta 2: [Apresenta ranking completo]
```
**INCONSISTÊNCIA INACEITÁVEL!**

---

## ✅ Teste 3: Tratamento Elegante de Erros

### Sequência:
```
1. "q dia q ocorreu a transação T-002461?"
2. "faça um rank dos produtos no mes de novembro, setembro"
```

### Resultado Esperado (v6.0):

**Pergunta 1:**
```
⚠️ **Limitação Identificada**

Tive dificuldade em extrair o dia exato da transação **T-002461**.

**O que posso fazer:**
✅ Informar o **mês** em que a transação ocorreu
✅ Mostrar o **produto** e **valor** da transação
...
```
✅ **Resposta elegante, SEM erro técnico exposto**

**Pergunta 2:**
```
Bot pede esclarecimento: "Você quer analisar novembro E setembro juntos, 
ou fazer dois rankings separados?"
```

### Resultado INCORRETO (v5.0):
```
❌ Pergunta 1: "Erro: could not convert string to float: '2024-11-29'"
❌ Pergunta 2: "Erro: Lengths must match to compare"
```
**NUNCA EXPOR ERROS TÉCNICOS!**

---

## ✅ Teste 4: Memória Através de Múltiplas Entidades

### Sequência:
```
1. "qual foi os produtos com a maior receita total no mes de dezembro"
2. "e em novembro?"
3. "compare os dois"
```

### Resultado Esperado (v6.0):

**Pergunta 1:**
```
Top 3 produtos em **Dezembro**:
- Laptop X1
- Laptop Pro Z
- Monitor Gamer
```
[Memória: Entidade em Foco = Dezembro, Análise = Ranking de Produtos]

**Pergunta 2:**
```
Top 3 produtos em **Novembro**:
- Laptop X1
- Monitor 4K
- Teclado Mecânico
```
✅ **Bot entendeu "e em novembro" = mesma análise, outro mês**

**Pergunta 3:**
```
Comparação Dezembro vs Novembro:
- Laptop X1 aparece em ambos
- Laptop Pro Z só em dezembro
...
```
✅ **Bot lembra dos dois períodos anteriores**

---

## ✅ Teste 5: Reset de Contexto (Nova Análise)

### Sequência:
```
1. "Qual foi a transação com maior faturamento?"
2. "em que mes ocorreu essa transação?"
3. "Agora me mostre a receita total de todos os meses"
4. "qual foi o mes com maior receita?"
```

### Resultado Esperado (v6.0):

**Perguntas 1-2:** Bot foca na transação T-002461

**Pergunta 3:**
```
| Mês | Receita Total |
|-----|---------------|
| Janeiro | R$ 850.000 |
| Fevereiro | R$ 920.000 |
...
```
✅ **Bot detectou que é NOVA análise (não menciona mais T-002461)**

**Pergunta 4:**
```
O mês com maior receita foi **Dezembro** com R$ 1.500.000.
```
✅ **Bot está no contexto da nova análise (meses), não da transação**

---

## 📊 Checklist de Validação

Use esta lista para validar se o v6.0 está funcionando:

- [ ] **Teste 1 Passou:** Bot confirma T-002461 nas perguntas 2, 3, 4
- [ ] **Teste 2 Passou:** Rankings de dezembro são idênticos
- [ ] **Teste 3 Passou:** Nenhum erro técnico exposto ao usuário
- [ ] **Teste 4 Passou:** Bot compara dezembro e novembro corretamente
- [ ] **Teste 5 Passou:** Bot detecta quando é nova análise vs continuação

---

## 🐛 Se Encontrar Bugs

### Bug: Bot ainda esquece o contexto

**Diagnóstico:**
- Verifique se `conversation_history` está sendo passado em `handle_drivebot_followup()`
- Verifique se histórico tem pelo menos 4 mensagens (2 trocas)

**Solução:**
```python
# Em handle_drivebot_followup(), linha ~1200
conversation_history = list(conversation.get("messages", []))[-6:]
```

### Bug: Respostas inconsistentes

**Diagnóstico:**
- Verifique se filtros temporais estão sendo aplicados corretamente
- Verifique logs: `print(f"[DriveBot] Comando gerado: {command}")`

**Solução:**
- Execute o backend em modo debug: `python app.py`
- Analise os comandos JSON gerados

### Bug: Erros técnicos expostos

**Diagnóstico:**
- Verifique se `handle_drivebot_followup()` tem tratamento de erro

**Solução:**
```python
# Em handle_drivebot_followup(), linha ~1220
if "error" in raw_result:
    if "could not convert" in raw_result["error"]:
        return """⚠️ Limitação Identificada..."""
```

---

## 📝 Notas de Teste

Anote aqui os resultados dos seus testes:

**Data:** __/__/____  
**Versão Testada:** v6.0  

**Teste 1 (Memória de Transação):**
- [ ] Passou
- [ ] Falhou: _______________

**Teste 2 (Consistência):**
- [ ] Passou
- [ ] Falhou: _______________

**Teste 3 (Erros Elegantes):**
- [ ] Passou
- [ ] Falhou: _______________

**Teste 4 (Multi-Entidade):**
- [ ] Passou
- [ ] Falhou: _______________

**Teste 5 (Reset de Contexto):**
- [ ] Passou
- [ ] Falhou: _______________

**Observações Gerais:**
_____________________________________________________
_____________________________________________________
_____________________________________________________
