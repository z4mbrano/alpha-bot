# 💰 Railway - Custos e Funcionamento

## 🎁 Plano Gratuito (Trial)

### O que você ganha:
- ✅ **$5 de crédito/mês** (renovável)
- ✅ **500 horas de execução/mês**
- ✅ **100 GB de bandwidth/mês**
- ✅ **1 GB de volume grátis** (para SQLite)
- ✅ **Sem cartão de crédito** necessário inicialmente

### Quanto consome o Alpha Bot?

**Estimativa realista:**
- **Uso leve** (você + poucos amigos testando):
  - ~$0.50 - $1.00/mês
  - 100-200 horas de execução
  - 5-10 GB bandwidth
  
- **Uso moderado** (10-20 usuários ocasionais):
  - ~$2.00 - $3.00/mês
  - 300-400 horas de execução
  - 20-30 GB bandwidth

- **Uso intenso** (50+ usuários ativos):
  - ~$5.00 - $8.00/mês
  - 500+ horas de execução
  - 50+ GB bandwidth

**Conclusão:** Para testes e uso pessoal, o plano gratuito é suficiente! ✅

---

## 🌐 O Site Fica Sempre Online?

### ✅ SIM! Railway mantém sua aplicação sempre ativa!

**Diferenças importantes:**

| Plataforma | Comportamento | Cold Start |
|------------|---------------|------------|
| **Railway** | ✅ Sempre online | ❌ Não tem |
| **Vercel** | ⚠️ Serverless | ✅ 2-5 segundos |
| **Render (free)** | ❌ Dorme após 15min | ✅ ~30 segundos |
| **Heroku (free)** | ❌ Descontinuado | - |

### Como funciona no Railway:

1. **Deploy inicial:** App sobe e fica online
2. **Requests:** Responde imediatamente (sem delay)
3. **Inatividade:** App continua rodando (não dorme!)
4. **Redeploy:** Apenas quando você faz push no GitHub

**Vantagens:**
- ✅ Sem cold starts (resposta instantânea)
- ✅ WebSocket e conexões persistentes funcionam
- ✅ Perfeito para aplicações com estado (SQLite)
- ✅ Melhor experiência do usuário

---

## 💳 Quando Railway Começa a Cobrar?

### Cenário 1: Você NÃO Adiciona Cartão
- ✅ Usa os $5 grátis/mês
- ⚠️ Se ultrapassar, app é **pausado** (não cobrado!)
- ✅ No mês seguinte, ganha $5 novos e app volta

### Cenário 2: Você Adiciona Cartão (Developer Plan)
- ✅ Primeiro $5 grátis (Railway paga)
- ⚠️ Depois dos $5, começa a cobrar
- 💰 $0.000231/GB-hora (compute)
- 💰 $0.10/GB (bandwidth além dos 100GB)

**Exemplo com cartão:**
- Mês com $3 de uso: **Paga $0** (dentro dos $5 grátis)
- Mês com $8 de uso: **Paga $3** ($8 - $5 grátis)

---

## 🎯 Recomendação

### Para Começar (Testes):
1. ✅ **NÃO adicione cartão** (use trial gratuito)
2. ✅ Deploy e teste por 1-2 meses
3. ✅ Monitore uso no dashboard
4. ✅ Se ficar abaixo de $5/mês, continua grátis!

### Para Produção (Sério):
1. ⚠️ Adicione cartão (Developer Plan)
2. ✅ Tenha controle total
3. ✅ Sem pausas inesperadas
4. ✅ Suporte prioritário

---

## 📊 Como Monitorar Custos

### No Railway Dashboard:

1. **Usage:**
   - Veja consumo em tempo real
   - Gráfico de uso mensal
   - Breakdown por serviço

2. **Settings → Billing:**
   - Créditos restantes
   - Histórico de uso
   - Estimativa do mês

3. **Alertas:**
   - Configure alerta em 80% dos $5
   - Receba email antes de pausar

---

## 🔔 O que Acontece se Ultrapassar $5?

### SEM Cartão:
1. ⚠️ App é **pausado automaticamente**
2. ✉️ Você recebe email avisando
3. 🔄 No próximo mês, ganha $5 novos
4. ✅ App volta a funcionar

**Importante:** Dados do volume NÃO são perdidos!

### COM Cartão:
1. ✅ App continua rodando
2. 💳 Cobra o excedente (ex: $8 - $5 = $3)
3. ✉️ Você recebe fatura no final do mês

---

## 💡 Dicas para Economizar

### 1. Use Sleep Mode (Opcional):
```json
// railway.json
{
  "deploy": {
    "sleepAfter": "30m"  // Dorme após 30min inativo
  }
}
```
⚠️ Mas isso cria cold starts (não recomendado para o Alpha Bot)

### 2. Optimize Docker Image:
- ✅ Usar `python:3.10-slim` (já estamos!)
- ✅ `--no-cache-dir` no pip (já estamos!)
- ✅ Multi-stage build (opcional)

### 3. Reduza Bandwidth:
- ✅ Habilite GZIP no Flask
- ✅ Use CDN para assets (imagens)
- ✅ Cache de responses (já temos!)

### 4. Monitore Volume:
- ✅ 1GB é suficiente para milhares de conversas
- ✅ Implemente limpeza de mensagens antigas
- ✅ Exporte backup periodicamente

---

## 🆚 Comparação de Custos

| Plataforma | Grátis | Depois | Cold Start | SQLite |
|------------|--------|--------|------------|--------|
| **Railway** | $5 trial | $5-10/mês | ❌ Não | ✅ Sim |
| **Vercel** | Grátis | $20/mês | ✅ 2-5s | ❌ Não |
| **Render** | Grátis* | $7/mês | ✅ 30s | ⚠️ Pago |
| **Fly.io** | $5 trial | $5-10/mês | ❌ Não | ✅ Sim |
| **Heroku** | ❌ Removido | $7/mês | ❌ Não | ⚠️ Add-on |

*Render free: app dorme após 15min de inatividade

**Melhor custo-benefício:** Railway 🏆

---

## ✅ Resumo Final

### Perguntas Respondidas:

**1. Railway vai me cobrar?**
- ❌ **NÃO**, se você usar apenas o trial ($5 grátis/mês)
- ✅ Só cobra se você adicionar cartão E ultrapassar $5/mês
- ⚠️ Se ultrapassar sem cartão, app **pausa** (não cobra!)

**2. O site fica sempre online?**
- ✅ **SIM!** Railway mantém app sempre ativo
- ✅ Sem cold starts (resposta instantânea)
- ✅ Melhor que Vercel/Render para apps stateful
- ✅ Perfeito para SQLite e WebSockets

**3. Quanto vou gastar?**
- 💰 Uso pessoal/testes: **$0-2/mês** (dentro dos $5 grátis!)
- 💰 Uso moderado (10-20 usuários): **$2-4/mês**
- 💰 Uso intenso (50+ usuários): **$5-8/mês**

**4. Vale a pena?**
- ✅ **SIM!** Melhor opção para SQLite persistente
- ✅ Melhor performance (sem cold starts)
- ✅ Melhor custo-benefício que Vercel + PostgreSQL
- ✅ Mais simples que configurar VPS

---

## 🎯 Decisão Recomendada

### Para Seu Caso (Alpha Bot):

1. ✅ **Use Railway no trial** (sem cartão)
2. ✅ Monitore uso por 1 mês
3. ✅ Se ficar < $5/mês → Continue grátis!
4. ✅ Se ultrapassar → Adicione cartão ($5-8/mês é barato)

**Alternativa se quiser 100% grátis:**
- Render.com (mas com cold starts de 30s)
- PythonAnywhere (mas mais lento)

**Mas Railway é a melhor escolha** para o Alpha Bot! 🚂

---

**Última atualização:** Outubro 2025  
**Valores:** Conferidos no site oficial do Railway
