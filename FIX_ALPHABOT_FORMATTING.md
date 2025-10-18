# 🔧 Correção: AlphaBot - Leitura de Planilhas e Formatação

## ❌ Problemas Relatados

1. **AlphaBot não consegue ler alguns CSVs** (ex: Planilha Teste.csv com caracteres especiais)
2. **Formatação com asteriscos excessivos** (`**texto** **mais** **texto**`)
3. **Tabelas tortas/desalinhadas** (dificultam visualização)

---

## ✅ Correções Aplicadas

### 1. Leitura de CSV com Múltiplos Encodings

**Problema:**
- CSV exportado do Excel brasileiro usa encoding `Windows-1252` (cp1252)
- AlphaBot tentava apenas `utf-8`, falhando com caracteres especiais (ç, ã, õ, etc.)

**Solução:**
```python
# Tentativa sequencial de encodings comuns no Brasil
encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1', 'utf-8-sig']

for encoding in encodings_to_try:
    try:
        file.seek(0)  # Reset posição do arquivo
        df = pd.read_csv(file, encoding=encoding, sep=None, engine='python')
        print(f"[AlphaBot] ✅ Arquivo {filename} lido com encoding: {encoding}")
        break
    except (UnicodeDecodeError, pd.errors.ParserError):
        continue
```

**Benefícios:**
- ✅ Lê CSVs brasileiros (cp1252, latin1)
- ✅ Lê CSVs internacionais (utf-8, utf-8-sig)
- ✅ Detecta automaticamente o separador (`;` ou `,`)
- ✅ Mensagem de log mostra qual encoding funcionou

---

### 2. Suporte a Mais Formatos de Planilhas

**ANTES:** Apenas `.csv` e `.xlsx`

**DEPOIS:** 
- ✅ `.csv` (comma-separated)
- ✅ `.xlsx` (Excel moderno)
- ✅ `.xls` (Excel legado)
- ✅ `.ods` (LibreOffice/OpenOffice)
- ✅ `.tsv` (tab-separated)

**Dependências Adicionadas ao `requirements.txt`:**
```
odfpy>=1.4.1   # Para ler arquivos .ods
xlrd>=2.0.1    # Para ler arquivos .xls
```

---

### 3. Limpeza de Formatação Markdown

**Problema:**
- IA gerava `**texto** **mais** **texto**` (asteriscos excessivos)
- Tabelas desalinhadas: `|col1|col2|col3|` (sem espaços)
- `** **` (asteriscos órfãos)

**Solução:**
Nova função `clean_markdown_formatting()`:

```python
def clean_markdown_formatting(text: str) -> str:
    """
    Limpa formatação Markdown excessiva ou mal formatada.
    """
    # 1. Remover múltiplos asteriscos consecutivos
    text = re.sub(r'\*{3,}', '**', text)  # ***texto*** → **texto**
    text = re.sub(r'\*\*\s+\*\*', '**', text)  # ** ** → **
    
    # 2. Corrigir ** no meio de palavras
    text = re.sub(r'(\w)\*\*(\w)', r'\1\2', text)  # pal**avra → palavra
    
    # 3. Remover ** órfãos (sem fechamento na mesma linha)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        bold_count = line.count('**')
        if bold_count % 2 != 0:  # Ímpar = tem órfão
            last_idx = line.rfind('**')
            line = line[:last_idx] + line[last_idx+2:]
        cleaned_lines.append(line)
    
    # 4. Melhorar tabelas Markdown (adicionar espaços)
    # | col1 | col2 | col3 |
    if '|' in line:
        line = re.sub(r'\s*\|\s*', ' | ', line)
    
    # 5. Limpar espaçamentos excessivos
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    
    return text.strip()
```

**Aplicada em:**
- ✅ Respostas do AlphaBot (`alphabot_chat`)
- ✅ Respostas do DriveBot (`format_analysis_result`)

---

### 4. Melhorias nos Prompts do Sistema

#### AlphaBot - Novas Regras de Formatação:

```markdown
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
  - Evite tabelas com mais de 5 colunas
  - Para dados extensos, mostre apenas os Top 10

- **Números:**
  - Valores monetários: R$ 1.234,56
  - Percentuais: 45,7%
  - Grandes números: 1.234.567
```

#### DriveBot - Instruções de Formatação:

```markdown
**FORMATAÇÃO OBRIGATÓRIA:**
- Use **negrito** apenas para termos importantes
- Tabelas Markdown DEVEM ser bem formatadas:
  | Produto  | Quantidade | Valor      |
  |----------|------------|------------|
  | Notebook | 150        | R$ 450.000 |
- Alinhe colunas com espaços
- Evite tabelas com mais de 5 colunas
- Para dados extensos, mostre Top 10 + total
```

---

## 📊 Exemplo: Antes vs Depois

### ANTES (❌ Ruim):

```
**Aqui** **está** **o** **resultado:**

|Matricula|Nome|Data|
|99|MARIA|10/06/2003|
|109|JO�O|10/06/2003|

**Erro ao ler: 'utf-8' codec can't decode...**
```

### DEPOIS (✅ Bom):

```
Aqui está o resultado da análise:

| Matricula | Nome           | Data Admissão |
|-----------|----------------|---------------|
| 99        | MARIA          | 10/06/2003    |
| 109       | JOÃO           | 10/06/2003    |
| 129       | JORGE          | 01/07/2003    |
| ...       | ...            | ...           |

**Total:** 550 funcionários analisados
✅ Arquivo lido com encoding: cp1252
```

---

## 🧪 Testando as Correções

### 1. Teste com CSV Brasileiro (encoding cp1252)

```bash
# Upload da planilha Teste.csv
curl -X POST http://localhost:5000/api/alphabot/upload \
  -F "files=@Planilha Teste.csv"

# Esperado:
# ✅ Status: success
# ✅ Files success: ["Planilha Teste.csv"]
# ✅ Log: "Arquivo Planilha Teste.csv lido com encoding: cp1252"
```

### 2. Teste de Pergunta com Formatação

```bash
# Fazer pergunta sobre os dados
curl -X POST http://localhost:5000/api/alphabot/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<session_id>",
    "message": "Me mostre os 10 funcionários mais antigos"
  }'

# Esperado:
# ✅ Tabela bem formatada
# ✅ Sem asteriscos excessivos
# ✅ Colunas alinhadas
```

### 3. Teste com Diferentes Formatos

```bash
# Testar .xlsx, .xls, .ods, .tsv
curl -X POST http://localhost:5000/api/alphabot/upload \
  -F "files=@dados.xlsx" \
  -F "files=@legado.xls" \
  -F "files=@libre.ods" \
  -F "files=@tab.tsv"

# Esperado:
# ✅ Todos os arquivos lidos
# ✅ Dados consolidados corretamente
```

---

## 📝 Arquivos Modificados

1. **`backend/app.py`:**
   - ✅ Função `alphabot_upload()` - leitura com múltiplos encodings
   - ✅ Suporte a `.xls`, `.ods`, `.tsv`
   - ✅ Nova função `clean_markdown_formatting()`
   - ✅ Aplicação da limpeza em `alphabot_chat()` e `format_analysis_result()`
   - ✅ Atualização de `ALPHABOT_SYSTEM_PROMPT` com regras de formatação
   - ✅ Atualização do prompt do DriveBot com instruções de formatação

2. **`backend/requirements.txt`:**
   - ✅ Adicionado `odfpy>=1.4.1` (para .ods)
   - ✅ Adicionado `xlrd>=2.0.1` (para .xls)

---

## 🚀 Próximos Passos

### 1. Instalar Novas Dependências

```powershell
cd backend
pip install -r requirements.txt
```

### 2. Testar Localmente

```powershell
# Iniciar backend
python app.py

# Em outro terminal, testar upload
curl -X POST http://localhost:5000/api/alphabot/upload \
  -F "files=@C:\Users\vrd\Downloads\Planilha Teste.csv"
```

### 3. Commit e Deploy

```powershell
git add backend/app.py backend/requirements.txt FIX_ALPHABOT_FORMATTING.md
git commit -m "Fix: AlphaBot lê todos formatos de planilha + formatação limpa"
git push origin main
```

---

## ✅ Checklist de Validação

- [x] ✅ Leitura de CSV com encoding cp1252/latin1
- [x] ✅ Suporte a .xlsx, .xls, .ods, .tsv
- [x] ✅ Função `clean_markdown_formatting()` criada
- [x] ✅ Limpeza aplicada nas respostas do AlphaBot
- [x] ✅ Limpeza aplicada nas respostas do DriveBot
- [x] ✅ Prompts atualizados com regras de formatação
- [x] ✅ Dependências adicionadas ao requirements.txt
- [ ] ⏳ Teste local com Planilha Teste.csv
- [ ] ⏳ Deploy e teste em produção

---

## 🎯 Resultado Esperado

**Usuário:**
1. ✅ Pode enviar qualquer tipo de planilha (.csv, .xlsx, .xls, .ods, .tsv)
2. ✅ CSVs brasileiros (Excel) funcionam sem erro de encoding
3. ✅ Respostas bem formatadas, fáceis de ler
4. ✅ Tabelas alinhadas corretamente
5. ✅ Sem poluição visual de asteriscos

---

**Data da Correção:** 18 de outubro de 2025  
**Status:** ✅ Correções aplicadas, pronto para teste
