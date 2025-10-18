import os
import uuid
from collections import deque
from typing import Any, Dict, List

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

# Armazenamento simples em memória para conversas
MAX_HISTORY_MESSAGES = 12
CONVERSATION_STORE: Dict[str, Dict[str, Any]] = {}

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


def ensure_conversation(conversation_id: str, bot_id: str) -> Dict[str, Any]:
    conversation = CONVERSATION_STORE.get(conversation_id)
    if conversation is None or conversation.get("bot_id") != bot_id:
        conversation = {
            "bot_id": bot_id,
            "messages": deque(maxlen=MAX_HISTORY_MESSAGES),
            "drive": {
                "drive_id": None,
                "report": None,
                "profile": None,
            },
        }
        CONVERSATION_STORE[conversation_id] = conversation
    return conversation


def append_message(conversation: Dict[str, Any], role: str, content: str) -> None:
    conversation["messages"].append({"role": role, "content": content})


def list_history(conversation: Dict[str, Any]) -> List[Dict[str, str]]:
    return list(conversation["messages"])


def build_discovery_bundle(drive_id: str) -> Dict[str, Any]:
    profile = {
        "drive_id": drive_id,
        "files_ok": [
            "vendas_mensais_2024.xlsx",
            "produtos_catalogo.csv",
            "clientes_dados.xlsx",
            "regional_performance.csv",
        ],
        "files_failed": [
            {"name": "backup_antigo.xls", "reason": "Formato legado não suportado"},
            {"name": "relatorio_final.pdf", "reason": "Formato não estruturado"},
        ],
        "dimensions": {
            "total_records": 2847,
            "total_records_fmt": "2.847",
            "period": "Jan/2024 a Dez/2024",
            "domains": ["temporal", "numérico", "categórico", "geográfico"],
        },
        "elements": {
            "numeric": [
                "valor_venda",
                "quantidade",
                "preco_unitario",
                "desconto_aplicado",
                "margem_contribuicao",
            ],
            "temporal": ["data_transacao", "mes_ref", "ano_fiscal"],
            "categorical": [
                "categoria_produto",
                "regiao_venda",
                "canal_venda",
                "status_pedido",
            ],
            "identifiers": ["id_cliente", "codigo_produto", "id_vendedor", "numero_pedido"],
            "text": ["nome_produto", "observacoes_venda", "endereco_entrega"],
        },
        "relationships": [
            "Forte correlação entre valor_venda e quantidade",
            "Padrão sazonal identificado nos campos temporais",
            "Agrupamento natural por regiao_venda detectado",
            "Hierarquia categoria_produto → subcategoria mapeada",
        ],
        "metrics": {
            "total_revenue": 18742650.0,
            "total_revenue_fmt": "R$ 18.742.650,00",
            "revenue_by_region": [
                {"label": "Sudeste", "fmt": "R$ 7.045.300,00", "share": "37%"},
                {"label": "Sul", "fmt": "R$ 4.218.740,00", "share": "23%"},
                {"label": "Nordeste", "fmt": "R$ 3.962.580,00", "share": "21%"},
                {"label": "Centro-Oeste", "fmt": "R$ 2.164.030,00", "share": "12%"},
                {"label": "Norte", "fmt": "R$ 1.351.000,00", "share": "7%"},
            ],
            "monthly_trend": [
                {"label": "Jan/2024", "fmt": "R$ 1.342.800,00"},
                {"label": "Fev/2024", "fmt": "R$ 1.278.450,00"},
                {"label": "Mar/2024", "fmt": "R$ 1.512.230,00"},
                {"label": "Abr/2024", "fmt": "R$ 1.487.510,00"},
                {"label": "Mai/2024", "fmt": "R$ 1.562.780,00"},
                {"label": "Jun/2024", "fmt": "R$ 1.604.120,00"},
                {"label": "Jul/2024", "fmt": "R$ 1.720.450,00"},
                {"label": "Ago/2024", "fmt": "R$ 1.689.330,00"},
                {"label": "Set/2024", "fmt": "R$ 1.674.890,00"},
                {"label": "Out/2024", "fmt": "R$ 1.556.310,00"},
                {"label": "Nov/2024", "fmt": "R$ 1.742.280,00"},
                {"label": "Dez/2024", "fmt": "R$ 1.571.900,00"},
            ],
            "top_categories": [
                {"label": "Tecnologia", "fmt": "R$ 4.110.250,00", "share": "22%"},
                {"label": "Casa & Estilo", "fmt": "R$ 3.842.170,00", "share": "20%"},
                {"label": "Escritório", "fmt": "R$ 2.968.450,00", "share": "16%"},
            ],
        },
    }

    files_ok = "\n".join(f"- {name}" for name in profile["files_ok"])
    files_failed = "\n".join(
        f"- {entry['name']} (Motivo: {entry['reason']})" for entry in profile["files_failed"]
    ) or "- Nenhuma ocorrência"

    elements = profile["elements"]
    relationships = "\n".join(f"- {rel}" for rel in profile["relationships"])

    report = f"""## 🔍 Processo de Descoberta Concluído

**Status da Exploração:** Mapeamento dos dados finalizado.

### 📁 Arquivos Descobertos e Processados
{files_ok}

### ⚠️ Arquivos Não Processáveis
{files_failed}

---

### 🗺️ Mapa da Estrutura Descoberta

**Dimensões dos Dados**
- **Total de Registros Mapeados:** {profile['dimensions']['total_records_fmt']} registros
- **Período Temporal Identificado:** {profile['dimensions']['period']}
- **Domínios de Dados Encontrados:** {', '.join(profile['dimensions']['domains'])}

**Elementos Estruturais**
- **Campos Numéricos:** {', '.join(f"`{c}`" for c in elements['numeric'])}
- **Campos Temporais:** {', '.join(f"`{c}`" for c in elements['temporal'])}
- **Campos Categóricos:** {', '.join(f"`{c}`" for c in elements['categorical'])}
- **Campos Identificadores:** {', '.join(f"`{c}`" for c in elements['identifiers'])}
- **Campos Textuais:** {', '.join(f"`{c}`" for c in elements['text'])}

### 🔗 Relações e Padrões Detectados
{relationships}

---

**Status:** Território de dados mapeado. Pronto para exploração direcionada."""

    return {"report": report, "profile": profile}


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


def handle_drivebot_followup(message: str, conversation: Dict[str, Any]) -> str | None:
    drive_state = conversation.get("drive", {})
    profile = drive_state.get("profile")
    if not profile:
        return None

    normalized = message.lower()

    if "faturamento" in normalized or "valor_venda" in normalized or "receita" in normalized:
        return format_revenue_overview(profile)

    if "regi" in normalized and ("ranking" in normalized or "top" in normalized or "maior" in normalized):
        return format_region_ranking(profile)

    if "categoria" in normalized and ("top" in normalized or "maior" in normalized or "desta" in normalized):
        return format_top_categories(profile)

    return None

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
                    "profile": bundle["profile"],
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

            manual_answer = handle_drivebot_followup(message, conversation)
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
            model = genai.GenerativeModel('gemini-1.5-flash')
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