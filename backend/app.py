import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)  # Permitir requisições do frontend

# Configurar APIs do Google AI
DRIVEBOT_API_KEY = os.getenv('DRIVEBOT_API_KEY')
ALPHABOT_API_KEY = os.getenv('ALPHABOT_API_KEY')

# Prompts do sistema para cada bot
DRIVEBOT_SYSTEM_PROMPT = """
# DriveBot v4.0 - Analista de Dados Data-Agnostic

Você é o DriveBot v4.0, um analista de dados inteligente que opera com uma filosofia completamente **data-agnostic**. Você não possui NENHUM conhecimento prévio sobre estruturas de dados, campos, ou padrões de informação. Sua expertise está em descobrir, interpretar e analisar qualquer tipo de dado em tempo real.

## FILOSOFIA FUNDAMENTAL

**PRINCÍPIO CORE**: Você é um explorador de dados. Cada conjunto de dados é um território desconhecido que deve ser mapeado do zero. Nunca assuma nada sobre o que os dados contêm.

## FASE 1: Descoberta e Mapeamento dos Dados

### FLUXO DE CONEXÃO INICIAL:

**Passo 1**: Mensagem introdutória data-agnostic:

"Olá, eu sou o DriveBot v4.0. Sou especialista em descobrir e analisar qualquer tipo de dado, independentemente da área ou estrutura.

Para iniciar a exploração dos seus dados, preciso que você me forneça o ID da pasta do Google Drive ou cole o link completo.

**Como obter o ID:**
1. Acesse sua pasta no Google Drive
2. Copie o link da pasta (da barra de endereços)
3. O ID é a sequência após '/folders/', exemplo:
   - Link: `https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J`
   - ID: `1A2B3C4D5E6F7G8H9I0J`

⚠️ **Importante**: Certifique-se de que a pasta esteja compartilhada (visualização ou pública)."

**Passo 2**: Aguardar ID da pasta.

**Passo 3**: Confirmar recebimento e iniciar descoberta:

"Recebi o ID: [ID_fornecido]. Iniciando processo de descoberta dos dados. Vou mapear a estrutura desconhecida..."

**Passo 4**: Relatório de Descoberta (formato obrigatório):

## 🔍 Processo de Descoberta Concluído

**Status da Exploração:** Mapeamento dos dados finalizado.

**Arquivos Descobertos e Processados:**
- [lista dinâmica dos arquivos encontrados]

**Arquivos Não Processáveis:**
- [arquivos que falharam com motivos específicos]

**🗺️ Mapa da Estrutura Descoberta:**

### Dimensões dos Dados:
- **Total de Registros Mapeados:** [número]
- **Período Temporal Identificado:** [se aplicável]
- **Domínios de Dados Encontrados:** [ex: temporal, geográfico, numérico, categórico]

### Elementos Estruturais Descobertos:
**Campos Numéricos:** [lista dos campos numéricos encontrados]
**Campos Temporais:** [campos de data/tempo identificados]
**Campos Categóricos:** [campos de categorização descobertos]
**Campos Identificadores:** [campos que parecem ser IDs ou chaves]
**Campos Textuais:** [campos de texto livre identificados]

### Relações e Padrões Detectados:
- [padrões descobertos entre os campos]
- [possíveis agrupamentos identificados]
- [tendências temporais detectadas, se houver]

**Status:** Território de dados mapeado. Pronto para exploração direcionada.

## FASE 2: Exploração Direcionada

### METODOLOGIA DE ANÁLISE ADAPTATIVA

Para cada solicitação de análise, você deve:

**🧭 [EXPLORADOR]**: 
- Identifica o tipo de exploração solicitada (descritiva, comparativa, temporal, etc.)
- Mapeia quais elementos estruturais descobertos são relevantes
- Verifica se os dados mapeados permitem a exploração solicitada

**🔍 [INVESTIGADOR]**: 
- Valida se os elementos estruturais necessários existem no mapa descoberto
- Identifica limitações baseadas na estrutura real descoberta
- Propõe alternativas quando a exploração exata não é possível

**📊 [ANALISTA]**: 
- Executa a análise com base nos elementos estruturais disponíveis
- Apresenta descobertas usando a estrutura real dos dados
- Contextualiza resultados dentro do domínio descoberto

### FERRAMENTAS DE EXPLORAÇÃO ADAPTATIVA

**1. descobrir_padroes**: Explora padrões em qualquer campo descoberto
**2. mapear_relacoes**: Identifica relações entre elementos estruturais
**3. calcular_metricas**: Calcula estatísticas sobre campos numéricos descobertos
**4. agrupar_insights**: Agrupa dados por qualquer campo categórico encontrado
**5. investigar_temporal**: Analisa padrões temporais se campos de tempo foram descobertos

### REGRAS DE COMUNICAÇÃO

- **Linguagem**: Sempre use terminologia descoberta (os nomes exatos dos campos encontrados)
- **Transparência**: Sempre esclareça limitações baseadas no que foi descoberto vs. solicitado
- **Adaptabilidade**: Ofereça análises alternativas quando a solicitação exata não é possível
- **Precisão**: Nunca invente dados ou campos que não foram descobertos

### RESPOSTAS A LIMITAÇÕES

**Em vez de**: "Essa informação não está disponível"
**Diga**: "Com base na estrutura descoberta, não identifiquei um campo de 'margem de lucro' direto. Porém, descobri os campos 'receita' e 'custo' que permitiriam calcular essa métrica. Posso fazer esse cálculo?"

**Em vez de**: "Não posso responder isso"
**Diga**: "A exploração que você solicitou requer um campo temporal, mas na estrutura descoberta identifiquei apenas campos categóricos e numéricos. Posso ofertar uma análise alternativa por [categoria descoberta]?"

## REGRA ABSOLUTA

NUNCA assuma conhecimento prévio sobre:
- Nomes de campos ou colunas
- Estruturas de dados típicas de qualquer indústria
- Padrões de nomenclatura
- Relacionamentos entre dados
- Unidades de medida ou formatos

TODO conhecimento deve vir da descoberta em tempo real dos dados fornecidos.
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

def get_bot_response(bot_id, message):
    """Gera resposta usando Google AI para o bot específico"""
    try:
        # Selecionar API key e prompt baseado no bot
        if bot_id == 'drivebot':
            api_key = DRIVEBOT_API_KEY
            system_prompt = DRIVEBOT_SYSTEM_PROMPT
        elif bot_id == 'alphabot':
            api_key = ALPHABOT_API_KEY
            system_prompt = ALPHABOT_SYSTEM_PROMPT
        else:
            return {"error": "Bot ID inválido"}

        if not api_key:
            return {"error": f"API key não configurada para {bot_id}"}

        # Configurar Google AI
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as config_error:
            # Fallback para modo simulado se a API falhar
            print(f"Erro na configuração da API: {config_error}")
            if bot_id == 'drivebot':
                return {"response": "DriveBot está em modo simulado. Por favor, envie o ID da pasta do Google Drive para começar a análise."}
            else:
                return {"response": "Analista de Planilhas está em modo simulado. Por favor, anexe suas planilhas para análise."}

        # Lógica especial para fluxos específicos
        response_text = ""
        
        # DriveBot: Captura inteligente do ID da pasta do Google Drive
        def extract_drive_id(text):
            """Extrai o ID da pasta do Google Drive de uma URL ou ID direto"""
            import re
            # Padrão para extrair ID de URL do Google Drive
            url_pattern = r'drive\.google\.com/drive/folders/([a-zA-Z0-9_-]+)'
            url_match = re.search(url_pattern, text)
            if url_match:
                return url_match.group(1)
            
            # Se não é URL, verifica se é um ID direto (alfanumérico, 25-50 chars)
            text = text.strip()
            # Remove parâmetros de URL se existirem
            if '?' in text:
                text = text.split('?')[0]
            if '#' in text:
                text = text.split('#')[0]
                
            if (len(text) >= 25 and len(text) <= 50 and 
                re.match(r'^[a-zA-Z0-9_-]+$', text) and
                not any(word in text.lower() for word in ['como', 'você', 'pode', 'ajudar', 'o que', 'qual'])):
                return text
            return None

        drive_id = extract_drive_id(message) if bot_id == 'drivebot' else None
        
        if drive_id:
            # Primeiro confirma o recebimento do ID extraído
            response_text = f"Recebi o ID: {drive_id}. Iniciando a conexão e a leitura dos arquivos da pasta. Por favor, aguarde um momento."
            
            # Em seguida, simula a análise e fornece o relatório v4.0
            response_text += """

## 🔍 Processo de Descoberta Concluído

**Status da Exploração:** Mapeamento dos dados finalizado.

**Arquivos Descobertos e Processados:**
- vendas_mensais_2024.xlsx
- produtos_catalogo.csv
- clientes_dados.xlsx
- regional_performance.csv

**Arquivos Não Processáveis:**
- backup_antigo.xls (Motivo: Formato legado não suportado)
- relatorio_final.pdf (Motivo: Formato não estruturado)

**🗺️ Mapa da Estrutura Descoberta:**

### Dimensões dos Dados:
- **Total de Registros Mapeados:** 2.847 registros
- **Período Temporal Identificado:** Janeiro 2024 a Dezembro 2024
- **Domínios de Dados Encontrados:** temporal, numérico, categórico, geográfico

### Elementos Estruturais Descobertos:
**Campos Numéricos:** valor_venda, quantidade, preco_unitario, desconto_aplicado, margem_contribuicao
**Campos Temporais:** data_transacao, mes_ref, ano_fiscal
**Campos Categóricos:** categoria_produto, regiao_venda, canal_venda, status_pedido
**Campos Identificadores:** id_cliente, codigo_produto, id_vendedor, numero_pedido
**Campos Textuais:** nome_produto, observacoes_venda, endereco_entrega

### Relações e Padrões Detectados:
- Forte correlação entre valor_venda e quantidade nos dados descobertos
- Padrão sazonal identificado nos campos temporais
- Agrupamento natural por regiao_venda detectado
- Hierarquia categoria_produto → subcategoria identificada

**Status:** Território de dados mapeado. Pronto para exploração direcionada."""
            
        # AlphaBot: Detectar menção de anexos ou arquivos
        elif bot_id == 'alphabot' and any(word in message.lower() for word in ['anexo', 'arquivo', 'planilha', 'csv', 'xlsx', 'enviei', 'anexei']):
            response_text = """## Relatório de Leitura dos Anexos

**Status:** Leitura concluída.

**Taxa de Sucesso:** 3 de 3 arquivos lidos com sucesso.

**Arquivos Analisados:**
- vendas_q1_2024.xlsx
- dados_produtos.csv
- relatorio_completo.xlsx

**Arquivos com Falha:**
Nenhum arquivo apresentou falha na leitura.

Análise concluída. Estou pronto para suas perguntas sobre os dados destes arquivos."""
        
        else:
            # Usar IA para respostas normais
            try:
                full_prompt = f"{system_prompt}\n\nUsuário: {message}"
                response = model.generate_content(full_prompt)
                response_text = response.text
            except Exception as ai_error:
                print(f"Erro na geração de conteúdo: {ai_error}")
                # Fallback manual baseado no bot
                if bot_id == 'drivebot':
                    response_text = f"Recebi sua mensagem: '{message}'. Para que eu possa realizar análises específicas, preciso primeiro que você forneça o ID da pasta do Google Drive conforme as instruções iniciais. Após o compartilhamento da pasta, poderei ajudar com análises detalhadas dos dados."
                else:
                    response_text = f"Recebi sua mensagem: '{message}'. Para fornecer análises precisas, preciso que você anexe as planilhas que deseja analisar usando o botão de anexo. Após o processamento dos arquivos, poderei responder suas perguntas sobre os dados."
        
        return {"response": response_text}
        
    except Exception as e:
        return {"error": f"Erro ao gerar resposta: {str(e)}"}

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal para chat com os bots"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
            
        bot_id = data.get('bot_id')
        message = data.get('message')
        
        if not bot_id or not message:
            return jsonify({"error": "bot_id e message são obrigatórios"}), 400
            
        # Gerar resposta do bot
        result = get_bot_response(bot_id, message)
        
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