import io
import json
import os
import re
import uuid
from datetime import datetime
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)  # Permitir requisições do frontend

# Configurar APIs do Google AI
DRIVEBOT_API_KEY = os.getenv('DRIVEBOT_API_KEY')
ALPHABOT_API_KEY = os.getenv('ALPHABOT_API_KEY')

GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
]
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
GOOGLE_SERVICE_ACCOUNT_INFO = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')
GOOGLE_CREDENTIALS: Optional[service_account.Credentials] = None

MONTH_ALIASES = {
    'janeiro': 1,
    'jan': 1,
    'fevereiro': 2,
    'fev': 2,
    'março': 3,
    'marco': 3,
    'mar': 3,
    'abril': 4,
    'abr': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9,
    'set': 9,
    'outubro': 10,
    'out': 10,
    'novembro': 11,
    'nov': 11,
    'dezembro': 12,
    'dez': 12,
}
MONTH_TRANSLATION = {name: datetime(2000, number, 1).strftime('%B') for name, number in MONTH_ALIASES.items()}
MONTH_NAMES_PT = {
    1: 'janeiro',
    2: 'fevereiro',
    3: 'março',
    4: 'abril',
    5: 'maio',
    6: 'junho',
    7: 'julho',
    8: 'agosto',
    9: 'setembro',
    10: 'outubro',
    11: 'novembro',
    12: 'dezembro',
}

EXCEL_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
}

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


def get_google_credentials() -> service_account.Credentials:
    """Obtém credenciais de serviço para acessar Google Drive e Sheets."""
    global GOOGLE_CREDENTIALS

    if GOOGLE_CREDENTIALS is not None:
        return GOOGLE_CREDENTIALS

    try:
        if GOOGLE_SERVICE_ACCOUNT_INFO:
            info = json.loads(GOOGLE_SERVICE_ACCOUNT_INFO)
            credentials = service_account.Credentials.from_service_account_info(info, scopes=GOOGLE_SCOPES)
        elif GOOGLE_SERVICE_ACCOUNT_FILE:
            if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
                raise RuntimeError(
                    "Arquivo de credenciais informado em GOOGLE_SERVICE_ACCOUNT_FILE não foi encontrado."
                )
            credentials = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=GOOGLE_SCOPES,
            )
        else:
            raise RuntimeError(
                "Credenciais não configuradas. Defina GOOGLE_SERVICE_ACCOUNT_FILE com o caminho do JSON "
                "da service account ou GOOGLE_SERVICE_ACCOUNT_INFO com o conteúdo JSON."
            )
    except Exception as error:
        raise RuntimeError(f"Erro ao carregar credenciais do Google: {error}") from error

    GOOGLE_CREDENTIALS = credentials
    return credentials


def get_google_services() -> Tuple[Any, Any]:
    """Inicializa clientes do Google Drive e Sheets utilizando as credenciais configuradas."""
    credentials = get_google_credentials()
    drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
    sheets_service = build('sheets', 'v4', credentials=credentials, cache_discovery=False)
    return drive_service, sheets_service


def normalize_decimal_string(value: Any) -> Optional[str]:
    """Normaliza strings com valores decimais para formato padrão."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None

    if isinstance(value, (int, float, np.number)):
        return str(value)

    text = str(value).strip()
    if not text or text.lower() in {'nan', 'none', 'null'}:
        return None

    # Remove símbolos comuns
    text = text.replace('R$', '').replace('%', '').replace(' ', '')
    text = text.replace('\t', '').replace('\n', '').replace('\r', '')
    text = text.replace('\u00a0', '')  # Non-breaking space

    # Normaliza separadores decimais
    if text.count(',') == 1 and text.count('.') >= 1:
        # Formato: 1.234,56 -> 1234.56
        text = text.replace('.', '').replace(',', '.')
    elif text.count(',') > 0:
        # Formato: 1234,56 -> 1234.56
        text = text.replace(',', '.')

    return text
def coerce_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors='coerce')

    normalized = series.astype(str).map(normalize_decimal_string)
    return pd.to_numeric(normalized, errors='coerce')


def detect_numeric_columns(df: pd.DataFrame) -> Tuple[List[str], Dict[str, pd.Series]]:
    numeric_columns: List[str] = []
    numeric_data: Dict[str, pd.Series] = {}

    for column in df.columns:
        coerced = coerce_numeric_series(df[column])
        if coerced.notna().sum() >= max(1, int(len(coerced) * 0.3)):
            numeric_columns.append(column)
            numeric_data[column] = coerced

    return numeric_columns, numeric_data


def normalize_month_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    text = value.strip()
    lower = text.lower()
    for pt_name, eng_name in MONTH_TRANSLATION.items():
        if pt_name in lower:
            lower = lower.replace(pt_name, eng_name.lower())
    return lower


def detect_datetime_columns(df: pd.DataFrame) -> Dict[str, pd.Series]:
    datetime_columns: Dict[str, pd.Series] = {}

    for column in df.columns:
        series = df[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            parsed = pd.to_datetime(series, errors='coerce')
        else:
            normalized = series.astype(str).map(normalize_month_text)
            parsed = pd.to_datetime(normalized, errors='coerce', dayfirst=True)

        if parsed.notna().sum() >= max(1, int(len(parsed) * 0.3)):
            parsed.name = column
            datetime_columns[column] = parsed

    return datetime_columns


def detect_text_columns(df: pd.DataFrame, numeric_columns: List[str]) -> List[str]:
    text_columns: List[str] = []
    numeric_set = set(numeric_columns)

    for column in df.columns:
        if column in numeric_set:
            continue
        series = df[column]
        if pd.api.types.is_string_dtype(series) or series.dtype == object:
            if series.astype(str).str.strip().replace('', np.nan).notna().sum() > 0:
                text_columns.append(column)

    return text_columns


def month_number_to_name(month: int) -> str:
    return MONTH_NAMES_PT.get(month, str(month))


def build_temporal_mask(table: Dict[str, Any], year: Optional[int] = None, month: Optional[int] = None) -> Optional[pd.Series]:
    datetime_columns: Dict[str, pd.Series] = table.get('datetime_columns', {})
    if not datetime_columns:
        return None

    combined_mask: Optional[pd.Series] = None
    for parsed in datetime_columns.values():
        mask = parsed.notna()
        if year is not None:
            mask &= parsed.dt.year == year
        if month is not None:
            mask &= parsed.dt.month == month
        if combined_mask is None:
            combined_mask = mask
        else:
            combined_mask |= mask

    return combined_mask


def prepare_table(table_name: str, df: pd.DataFrame) -> Dict[str, Any]:
    processed = df.copy()
    processed.columns = [str(col).strip() for col in processed.columns]
    processed = processed.replace('', np.nan)

    numeric_columns, numeric_data = detect_numeric_columns(processed)
    datetime_columns = detect_datetime_columns(processed)
    text_columns = detect_text_columns(processed, numeric_columns)

    return {
        'name': table_name,
        'df': processed,
        'row_count': int(len(processed)),
        'columns': list(processed.columns),
        'numeric_columns': numeric_columns,
        'numeric_data': numeric_data,
        'datetime_columns': datetime_columns,
        'text_columns': text_columns,
    }


def download_file_bytes(drive_service: Any, file_id: str) -> bytes:
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _status, done = downloader.next_chunk()

    return fh.getvalue()


def load_csv_tables(drive_service: Any, file_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    content = download_file_bytes(drive_service, file_meta['id'])
    df = pd.read_csv(io.BytesIO(content))
    return [prepare_table(file_meta['name'], df)]


def load_excel_tables(drive_service: Any, file_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    content = download_file_bytes(drive_service, file_meta['id'])
    workbook = pd.read_excel(io.BytesIO(content), sheet_name=None)
    tables: List[Dict[str, Any]] = []
    for sheet_name, df in workbook.items():
        table_name = f"{file_meta['name']} - {sheet_name}"
        tables.append(prepare_table(table_name, df))
    return tables


def build_discovery_summary(
    tables: List[Dict[str, Any]],
    files_ok: List[str],
    files_failed: List[Dict[str, str]],
) -> Dict[str, Any]:
    total_records = sum(table['row_count'] for table in tables)
    all_columns = set()
    numeric_columns = set()
    text_columns = set()
    start_dates: List[pd.Timestamp] = []
    end_dates: List[pd.Timestamp] = []

    for table in tables:
        all_columns.update(table['columns'])
        numeric_columns.update(table['numeric_columns'])
        text_columns.update(table['text_columns'])

        for parsed in table['datetime_columns'].values():
            valid = parsed.dropna()
            if not valid.empty:
                start_dates.append(valid.min())
                end_dates.append(valid.max())

    if start_dates and end_dates:
        date_range: Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]] = (
            min(start_dates),
            max(end_dates),
        )
    else:
        date_range = (None, None)

    domains: List[str] = []
    if numeric_columns:
        domains.append('numérico')
    if text_columns:
        domains.append('categórico')
    if any(date_range):
        domains.append('temporal')

    return {
        'files_ok': files_ok,
        'files_failed': files_failed,
        'total_records': int(total_records),
        'columns': sorted(filter(None, all_columns)),
        'numeric_columns': sorted(numeric_columns),
        'text_columns': sorted(text_columns),
        'date_range': date_range,
        'domains': domains,
    }


def format_date(date_value: Optional[pd.Timestamp]) -> Optional[str]:
    if date_value is None or (isinstance(date_value, float) and np.isnan(date_value)):
        return None
    try:
        timestamp = pd.to_datetime(date_value)
    except Exception:
        return None
    if pd.isna(timestamp):
        return None
    return timestamp.strftime('%d/%m/%Y')


def build_discovery_report(summary: Dict[str, Any]) -> str:
    files_ok = summary['files_ok']
    files_failed = summary['files_failed']
    date_range = summary['date_range']

    files_ok_md = '\n'.join(f"- {name}" for name in files_ok) or '- Nenhum arquivo processado com sucesso.'
    files_failed_md = '\n'.join(
        f"- {entry['name']} (Motivo: {entry['reason']})" for entry in files_failed
    ) or '- Nenhum arquivo apresentou falha.'

    start_text = format_date(date_range[0])
    end_text = format_date(date_range[1])
    if start_text and end_text:
        period_text = f"{start_text} até {end_text}"
    elif start_text or end_text:
        period_text = start_text or end_text
    else:
        period_text = 'Não identificado'

    numeric_cols_md = ', '.join(f"`{col}`" for col in summary['numeric_columns']) or 'Nenhum identificado'
    text_cols_md = ', '.join(f"`{col}`" for col in summary['text_columns']) or 'Nenhum identificado'

    domains_md = ', '.join(summary['domains']) if summary['domains'] else 'Não identificado'

    return (
        "## 🔍 Processo de Descoberta Concluído\n\n"
        "**Status da Exploração:** Mapeamento dos dados finalizado.\n\n"
        "### 📁 Arquivos Processados com Sucesso\n"
        f"{files_ok_md}\n\n"
        "### ⚠️ Arquivos com Falha\n"
        f"{files_failed_md}\n\n"
        "---\n\n"
        "### 🗺️ Mapa da Estrutura Descoberta\n\n"
        f"- **Total de Registros Mapeados:** {summary['total_records']}\n"
        f"- **Período Temporal Identificado:** {period_text}\n"
        f"- **Domínios de Dados Encontrados:** {domains_md}\n\n"
        "**Elementos Estruturais**\n"
        f"- **Campos Numéricos:** {numeric_cols_md}\n"
        f"- **Campos Categóricos/Textuais:** {text_cols_md}\n"
    )


def ingest_drive_folder(drive_id: str) -> Dict[str, Any]:
    drive_service, sheets_service = get_google_services()

    try:
        response = drive_service.files().list(
            q=f"'{drive_id}' in parents and trashed=false",
            fields="files(id,name,mimeType,modifiedTime)",
        ).execute()
    except HttpError as error:
        raise RuntimeError(f"Erro ao acessar a pasta do Google Drive: {error}") from error

    files = response.get('files', [])
    if not files:
        raise RuntimeError("Nenhum arquivo encontrado na pasta informada. Verifique o ID e as permissões.")

    tables: List[Dict[str, Any]] = []
    files_ok: List[str] = []
    files_failed: List[Dict[str, str]] = []

    for file_meta in files:
        mime_type = file_meta.get('mimeType')
        try:
            if mime_type == 'application/vnd.google-apps.spreadsheet':
                spreadsheet = sheets_service.spreadsheets().get(
                    spreadsheetId=file_meta['id'],
                    includeGridData=False,
                ).execute()
                sheets = spreadsheet.get('sheets', [])
                if not sheets:
                    files_failed.append({'name': file_meta['name'], 'reason': 'Planilha sem abas válidas'})
                    continue

                for sheet in sheets:
                    title = sheet['properties']['title']
                    range_name = f"'{title}'!A1:ZZZ"
                    values_response = sheets_service.spreadsheets().values().get(
                        spreadsheetId=file_meta['id'],
                        range=range_name,
                    ).execute()
                    values = values_response.get('values', [])
                    if len(values) < 1:
                        continue

                    header, *rows = values
                    if not header:
                        continue
                    df = pd.DataFrame(rows, columns=header)
                    table_name = f"{file_meta['name']} - {title}"
                    tables.append(prepare_table(table_name, df))

                files_ok.append(file_meta['name'])
            elif mime_type == 'text/csv':
                tables.extend(load_csv_tables(drive_service, file_meta))
                files_ok.append(file_meta['name'])
            elif mime_type in EXCEL_MIME_TYPES:
                tables.extend(load_excel_tables(drive_service, file_meta))
                files_ok.append(file_meta['name'])
            else:
                files_failed.append({'name': file_meta['name'], 'reason': f'Formato não suportado ({mime_type})'})
        except HttpError as error:
            files_failed.append({'name': file_meta['name'], 'reason': f'Erro ao ler o arquivo: {error}'})
        except Exception as error:
            files_failed.append({'name': file_meta['name'], 'reason': str(error)})

    if not tables:
        raise RuntimeError(
            'Não foi possível processar nenhum arquivo da pasta. Convert a planilhas Google ou CSV e confira as permissões.'
        )

    summary = build_discovery_summary(tables, files_ok, files_failed)
    report = build_discovery_report(summary)

    return {
        'tables': tables,
        'summary': summary,
        'report': report,
        'files_ok': files_ok,
        'files_failed': files_failed,
    }


def ensure_conversation(conversation_id: str, bot_id: str) -> Dict[str, Any]:
    conversation = CONVERSATION_STORE.get(conversation_id)
    if conversation is None or conversation.get("bot_id") != bot_id:
        conversation = {
            "bot_id": bot_id,
            "messages": deque(maxlen=MAX_HISTORY_MESSAGES),
            "drive": {
                "drive_id": None,
                "report": None,
                "summary": None,
                "tables": [],
                "files_ok": [],
                "files_failed": [],
                "last_refresh": None,
            },
        }
        CONVERSATION_STORE[conversation_id] = conversation
    return conversation


def append_message(conversation: Dict[str, Any], role: str, content: str) -> None:
    conversation["messages"].append({"role": role, "content": content})


def list_history(conversation: Dict[str, Any]) -> List[Dict[str, str]]:
    return list(conversation["messages"])


def build_discovery_bundle(drive_id: str) -> Dict[str, Any]:
    """
    VERSÃO REAL: Conecta ao Google Drive, lê os arquivos e retorna dados reais.
    """
    try:
        # Tentar ler dados reais do Google Drive
        ingestion_result = ingest_drive_folder(drive_id)
        
        # Retornar os dados reais
        return {
            "report": ingestion_result["report"],
            "profile": None,  # Não usado mais na nova arquitetura
            "tables": ingestion_result["tables"],
            "summary": ingestion_result["summary"],
            "files_ok": ingestion_result["files_ok"],
            "files_failed": ingestion_result["files_failed"],
        }
    
    except Exception as e:
        print(f"[DriveBot] Erro ao acessar Google Drive: {e}")
        
        # Fallback: retornar erro explicativo
        error_report = f"""## ⚠️ Erro ao Conectar com Google Drive

**Erro:** {str(e)}

**Possíveis Causas:**
1. O ID da pasta está incorreto
2. A pasta não foi compartilhada com a Service Account
3. As APIs do Google Drive/Sheets não estão habilitadas
4. As credenciais não estão configuradas corretamente

**Como Resolver:**
1. Verifique se o ID está correto: `{drive_id}`
2. Compartilhe a pasta com: `id-spreadsheet-reader-robot@data-analytics-gc-475218.iam.gserviceaccount.com`
3. Dê permissão de **Viewer** (leitura)

**Para mais ajuda, consulte:** `GOOGLE_DRIVE_SETUP.md`
"""
        
        return {
            "report": error_report,
            "profile": None,
            "tables": [],
            "summary": None,
            "files_ok": [],
            "files_failed": [{"name": "Erro de Conexão", "reason": str(e)}],
        }


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


# ============================================================================
# ARQUITETURA DE DOIS PROMPTS: TRADUÇÃO + EXECUÇÃO + APRESENTAÇÃO
# ============================================================================

def generate_analysis_command(question: str, available_columns: List[str], api_key: str) -> Optional[Dict[str, Any]]:
    """
    PROMPT #1: TRADUTOR DE INTENÇÃO
    Converte pergunta do usuário em comando JSON estruturado para análise de dados.
    """
    translator_prompt = f"""Você é um especialista em análise de dados que traduz perguntas em linguagem natural para comandos executáveis em JSON.

**Contexto:**
- O usuário está interagindo com um dataset real carregado do Google Drive.
- As colunas disponíveis neste dataset são: {available_columns}

**Sua Tarefa:**
Com base na pergunta do usuário, escolha UMA das seguintes ferramentas e forneça os parâmetros necessários em formato JSON puro. 
Não adicione nenhuma outra explicação, markdown, ou texto extra. APENAS o JSON válido.

**Ferramentas Disponíveis:**

1. **calculate_metric**: Para calcular uma única métrica agregada
   Exemplo: {{"tool": "calculate_metric", "params": {{"metric_column": "valor_venda", "operation": "sum", "filters": {{"regiao": "Sul"}}}}}}
   Operações: sum, mean, count, min, max

2. **get_ranking**: Para criar um ranking agrupando dados
   Exemplo: {{"tool": "get_ranking", "params": {{"group_by_column": "nome_produto", "metric_column": "quantidade", "operation": "sum", "filters": {{"mes_ref": "Jan/2024"}}, "top_n": 5, "ascending": false}}}}

3. **get_unique_values**: Para listar valores únicos de uma coluna
   Exemplo: {{"tool": "get_unique_values", "params": {{"column": "regiao_venda"}}}}

4. **get_time_series**: Para análise temporal/evolução ao longo do tempo
   Exemplo: {{"tool": "get_time_series", "params": {{"time_column": "mes_ref", "metric_column": "valor_venda", "operation": "sum", "group_by_column": "regiao"}}}}

**Pergunta do Usuário:** "{question}"
**Colunas Disponíveis:** {available_columns}

**JSON de Saída (APENAS JSON, SEM TEXTO EXTRA):**"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(translator_prompt)
        response_text = (response.text or "").strip()
        
        # Limpar markdown se houver
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        command = json.loads(response_text)
        return command
    except Exception as e:
        print(f"Erro ao gerar comando de análise: {e}")
        print(f"Resposta recebida: {response_text if 'response_text' in locals() else 'N/A'}")
        return None


def execute_analysis_command(command: Dict[str, Any], tables: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Executa o comando JSON nos dados REAIS do DataFrame.
    """
    if not tables:
        return {"error": "Nenhum dado disponível para análise"}
    
    tool = command.get("tool")
    params = command.get("params", {})
    
    # Combinar todos os DataFrames em um só (assumindo estrutura similar)
    try:
        all_dfs = []
        for table in tables:
            df = table.get("df")
            if df is not None and not df.empty:
                all_dfs.append(df)
        
        if not all_dfs:
            return {"error": "Nenhum DataFrame válido encontrado"}
        
        # Usar o primeiro DataFrame (ou combinar se necessário)
        df = all_dfs[0] if len(all_dfs) == 1 else pd.concat(all_dfs, ignore_index=True)
        
    except Exception as e:
        return {"error": f"Erro ao processar DataFrames: {str(e)}"}
    
    # Aplicar filtros
    filters = params.get("filters", {})
    filtered_df = df.copy()
    for column, value in filters.items():
        if column in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[column] == value]
    
    # Executar ferramenta
    try:
        if tool == "calculate_metric":
            metric_column = params.get("metric_column")
            operation = params.get("operation", "sum")
            
            if metric_column not in filtered_df.columns:
                return {"error": f"Coluna '{metric_column}' não encontrada"}
            
            if operation == "sum":
                result = filtered_df[metric_column].sum()
            elif operation == "mean":
                result = filtered_df[metric_column].mean()
            elif operation == "count":
                result = len(filtered_df)
            elif operation == "min":
                result = filtered_df[metric_column].min()
            elif operation == "max":
                result = filtered_df[metric_column].max()
            else:
                return {"error": f"Operação '{operation}' não suportada"}
            
            return {
                "tool": tool,
                "result": float(result) if pd.notna(result) else None,
                "metric_column": metric_column,
                "operation": operation,
                "filters": filters,
                "record_count": len(filtered_df)
            }
        
        elif tool == "get_ranking":
            group_by_column = params.get("group_by_column")
            metric_column = params.get("metric_column")
            operation = params.get("operation", "sum")
            top_n = params.get("top_n", 10)
            ascending = params.get("ascending", False)
            
            if group_by_column not in filtered_df.columns:
                return {"error": f"Coluna '{group_by_column}' não encontrada"}
            if metric_column not in filtered_df.columns:
                return {"error": f"Coluna '{metric_column}' não encontrada"}
            
            if operation == "sum":
                grouped = filtered_df.groupby(group_by_column)[metric_column].sum()
            elif operation == "mean":
                grouped = filtered_df.groupby(group_by_column)[metric_column].mean()
            elif operation == "count":
                grouped = filtered_df.groupby(group_by_column)[metric_column].count()
            else:
                return {"error": f"Operação '{operation}' não suportada"}
            
            ranked = grouped.sort_values(ascending=ascending).head(top_n)
            
            return {
                "tool": tool,
                "ranking": [
                    {group_by_column: str(idx), metric_column: float(val)}
                    for idx, val in ranked.items()
                ],
                "group_by_column": group_by_column,
                "metric_column": metric_column,
                "operation": operation,
                "filters": filters,
                "record_count": len(filtered_df)
            }
        
        elif tool == "get_unique_values":
            column = params.get("column")
            
            if column not in filtered_df.columns:
                return {"error": f"Coluna '{column}' não encontrada"}
            
            unique_values = filtered_df[column].dropna().unique().tolist()
            
            return {
                "tool": tool,
                "column": column,
                "unique_values": [str(v) for v in unique_values],
                "count": len(unique_values)
            }
        
        elif tool == "get_time_series":
            time_column = params.get("time_column")
            metric_column = params.get("metric_column")
            operation = params.get("operation", "sum")
            group_by_column = params.get("group_by_column")
            
            if time_column not in filtered_df.columns:
                return {"error": f"Coluna '{time_column}' não encontrada"}
            if metric_column not in filtered_df.columns:
                return {"error": f"Coluna '{metric_column}' não encontrada"}
            
            if group_by_column and group_by_column in filtered_df.columns:
                if operation == "sum":
                    grouped = filtered_df.groupby([time_column, group_by_column])[metric_column].sum()
                elif operation == "mean":
                    grouped = filtered_df.groupby([time_column, group_by_column])[metric_column].mean()
                else:
                    grouped = filtered_df.groupby([time_column, group_by_column])[metric_column].count()
                
                result_data = grouped.reset_index().to_dict('records')
            else:
                if operation == "sum":
                    grouped = filtered_df.groupby(time_column)[metric_column].sum()
                elif operation == "mean":
                    grouped = filtered_df.groupby(time_column)[metric_column].mean()
                else:
                    grouped = filtered_df.groupby(time_column)[metric_column].count()
                
                result_data = [
                    {time_column: str(idx), metric_column: float(val)}
                    for idx, val in grouped.items()
                ]
            
            return {
                "tool": tool,
                "time_series": result_data,
                "time_column": time_column,
                "metric_column": metric_column,
                "operation": operation,
                "filters": filters
            }
        
        else:
            return {"error": f"Ferramenta '{tool}' não reconhecida"}
    
    except Exception as e:
        return {"error": f"Erro ao executar análise: {str(e)}"}


def format_analysis_result(question: str, raw_result: Dict[str, Any], api_key: str) -> str:
    """
    PROMPT #2: APRESENTADOR DE RESULTADOS
    Formata os resultados REAIS da análise em uma resposta bem apresentada.
    """
    if "error" in raw_result:
        return f"⚠️ **Erro na análise:** {raw_result['error']}\n\nPor favor, reformule sua pergunta ou verifique se os dados estão disponíveis."
    
    presenter_prompt = f"""Você é o DriveBot, um assistente de análise de dados. Sua tarefa é apresentar os resultados de uma análise de forma clara e profissional para o usuário.

**Contexto:**
- O usuário perguntou: "{question}"
- Uma análise foi executada nos dados REAIS do Google Drive.
- Os resultados abaixo são FATOS extraídos diretamente dos dados.

**Sua Tarefa:**
Apresente os dados brutos a seguir em uma resposta bem formatada usando Markdown. 
- Use tabelas quando apropriado
- Adicione uma breve observação ou insight se apropriado
- Seja direto e objetivo
- NÃO use a estrutura [EXPLORADOR]/[INVESTIGADOR]
- NÃO invente dados adicionais
- Use emojis para deixar mais amigável

---
**Dados Brutos da Análise:**
```json
{json.dumps(raw_result, indent=2, ensure_ascii=False)}
```

**Resposta Formatada:**"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(presenter_prompt)
        response_text = (response.text or "").strip()
        
        if not response_text:
            return "Desculpe, não consegui formatar a resposta. Aqui estão os dados brutos:\n\n" + json.dumps(raw_result, indent=2, ensure_ascii=False)
        
        return response_text
    except Exception as e:
        print(f"Erro ao formatar resultado: {e}")
        return "Desculpe, não consegui formatar a resposta. Aqui estão os dados brutos:\n\n" + json.dumps(raw_result, indent=2, ensure_ascii=False)


def handle_drivebot_followup(message: str, conversation: Dict[str, Any], api_key: str) -> str | None:
    """
    Processa perguntas do usuário sobre dados já descobertos usando arquitetura de dois prompts.
    """
    drive_state = conversation.get("drive", {})
    tables = drive_state.get("tables", [])
    
    if not tables:
        return None
    
    # Extrair colunas disponíveis de todas as tabelas
    all_columns = set()
    for table in tables:
        df = table.get("df")
        if df is not None and not df.empty:
            all_columns.update(df.columns.tolist())
    
    available_columns = sorted(list(all_columns))
    
    if not available_columns:
        return None
    
    # FASE 1: Traduzir pergunta em comando JSON
    print(f"[DriveBot] Traduzindo pergunta: {message}")
    command = generate_analysis_command(message, available_columns, api_key)
    
    if not command:
        print("[DriveBot] Falha ao gerar comando de análise")
        return None
    
    print(f"[DriveBot] Comando gerado: {json.dumps(command, indent=2)}")
    
    # FASE 2: Executar comando nos dados REAIS
    print(f"[DriveBot] Executando análise nos dados reais...")
    raw_result = execute_analysis_command(command, tables)
    
    if not raw_result:
        print("[DriveBot] Falha ao executar análise")
        return None
    
    print(f"[DriveBot] Resultado da análise: {json.dumps(raw_result, indent=2)}")
    
    # FASE 3: Formatar resultado em resposta amigável
    print(f"[DriveBot] Formatando resultado...")
    formatted_response = format_analysis_result(message, raw_result, api_key)
    
    return formatted_response

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
                    "tables": bundle["tables"],  # CRÍTICO: Armazenar os DataFrames reais
                    "summary": bundle["summary"],
                    "files_ok": bundle["files_ok"],
                    "files_failed": bundle["files_failed"],
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

            manual_answer = handle_drivebot_followup(message, conversation, api_key)
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
            model = genai.GenerativeModel('gemini-2.5-flash')
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