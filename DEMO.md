# 🎯 Demonstração dos Bots - Alpha Insights

Este arquivo contém exemplos de como interagir com cada bot da aplicação.

# 🎯 Demonstração dos Bots - Alpha Insights

Este arquivo contém exemplos de como interagir com cada bot da aplicação seguindo os fluxos exatos especificados.

## 🗂️ DriveBot v3.0 - Análise de Dados no Google Drive

### Passo 1: Mensagem inicial automática (EXATA)
O DriveBot v3.0 se apresentará automaticamente com:
```
Olá! Eu sou o DriveBot. Para começar, por favor, siga estes dois passos:

1. Envie aqui o ID da pasta do Google Drive que você deseja que eu analise.
2. Compartilhe a pasta comigo, adicionando o e-mail id-spreadsheet-reader-robot@data-analytics-gc-475218.iam.gserviceaccount.com como Editor.

Ficarei aguardando sua confirmação para iniciar a análise.
```

### Passo 2: Captura Inteligente do ID
**Aceita qualquer formato:**
- URL completa: `https://drive.google.com/drive/folders/1hbWmhtJj2VwADiQbSELpxYTDs7Y8gJzb?usp=sharing`
- ID direto: `1hbWmhtJj2VwADiQbSELpxYTDs7Y8gJzb`
- Com parâmetros: `1hbWmhtJj2VwADiQbSELpxYTDs7Y8gJzb?hl=pt`

### Passo 3: Confirmação automática
```
Recebi o ID: 1hbWmhtJj2VwADiQbSELpxYTDs7Y8gJzb. Iniciando a conexão e a leitura dos arquivos da pasta. Por favor, aguarde um momento.
```

### Passo 4: Relatório de Carga e Diagnóstico v3.0
```markdown
## Análise da Pasta Concluída

**Status:** Leitura e consolidação dos dados finalizadas.

**Arquivos Lidos com Sucesso:**
- DADOS_JANUARY.CSV
- DADOS_FEBRUARY.CSV
- DADOS_MARCH.CSV
- VENDAS_Q1_2024.XLSX
- RELATORIO_CATEGORIAS.CSV

**Arquivos com Falha na Leitura:**
- backup_antigo.xls (Motivo: Formato não suportado)
- relatorio_financeiro.pdf (Motivo: Formato não suportado)

**Visão Geral dos Dados Consolidados:**
- **Total de Registros Analisados:** 2.806
- **Período dos Dados:** 01/01/2024 a 31/03/2024
- **Colunas Disponíveis para Análise:** Data, ID_Transacao, Produto, Categoria, Região, Quantidade, Preço_Unitário, Receita_Total, Mes, Arquivo_Origem

Estou pronto para responder às suas perguntas sobre os dados analisados.
```

### Passo 5: Framework Analista-Crítico-Júri
**Processo interno para cada pergunta:**
1. **[ANALISTA]**: Interpreta intenção e entidades
2. **[CRÍTICO]**: Valida se dados existem nas colunas disponíveis  
3. **[JÚRI]**: Decide ferramenta ou explica limitação

**Ferramentas disponíveis:**
- `calculate_metric`: Soma, média, contagem com filtros
- `get_ranking`: Rankings ordenados por métricas
- `get_unique_values`: Lista valores únicos de colunas

**Respostas inteligentes:**
❌ "Essa informação não foi encontrada"
✅ "Não consigo calcular a margem de lucro. Para isso, eu precisaria de uma coluna com os 'custos' dos produtos, que não foi encontrada nos arquivos analisados."

---

## 📊 AlphaBot - Análise de Planilhas Anexadas

### Passo 1: Mensagem inicial automática (EXATA)
```
Olá, eu sou o AlphaBot. Por favor, use o botão de anexo para enviar as planilhas (.csv, .xlsx) que você deseja analisar.
```

### Passo 2: Mencione arquivos anexados
**Exemplo:** "Enviei 3 planilhas xlsx com dados de vendas"

### Passo 3: Relatório automático (Formato Markdown)
```markdown
## Relatório de Leitura dos Anexos

**Status:** Leitura concluída.

**Taxa de Sucesso:** 3 de 3 arquivos lidos com sucesso.

**Arquivos Analisados:**
- vendas_q1_2024.xlsx
- dados_produtos.csv
- relatorio_completo.xlsx

**Arquivos com Falha:**
Nenhum arquivo apresentou falha na leitura.

Análise concluída. Estou pronto para suas perguntas sobre os dados destes arquivos.
```

### Passo 4: Perguntas sobre os dados
Responde baseado apenas nos arquivos anexados na sessão atual. Não tem memória de conversas anteriores.

---

## 🔧 Configuração Técnica

### Backend (Porta 5000)
- Flask + Google AI API
- Detecção automática de fluxos
- Fallback para modo simulado se API falhar

### Frontend (Porta 5174)
- React + TypeScript + Vite
- Indicadores de digitação
- Tema dark/light
- Interface responsiva

### Como testar:
1. Backend: `cd backend && python app.py`
2. Frontend: `npm run dev`
3. Acesse: http://localhost:5174

---

## 📝 Próximos Passos

1. **Integração Real com Google Drive**
   - Implementar Google Drive API
   - Service Account authentication
   - Leitura real de planilhas

2. **Upload de Arquivos no Frontend**
   - Implementar funcionalidade do botão anexo
   - Envio de arquivos para o backend
   - Preview de planilhas

3. **Análises Avançadas**
   - Gráficos e visualizações
   - Export de relatórios
   - Salvamento de análises

4. **Deploy e Produção**
   - Configuração de ambiente
   - Segurança de API keys
   - Monitoramento e logs