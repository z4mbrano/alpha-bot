"""
AlphaBot API Routes
Endpoints para upload e análise de planilhas anexadas
"""

import io
import uuid
from typing import Dict, Any
from flask import Blueprint, request, jsonify
import pandas as pd

from ..services import get_ai_service, get_data_analyzer
from ..utils import allowed_file, ALLOWED_EXTENSIONS


# Criar blueprint
alphabot_bp = Blueprint('alphabot', __name__, url_prefix='/api/alphabot')

# Armazenamento global para sessões do AlphaBot
ALPHABOT_SESSIONS: Dict[str, Dict[str, Any]] = {}


@alphabot_bp.route('/upload', methods=['POST'])
def upload():
    """
    Upload e processamento de múltiplos arquivos para o AlphaBot.
    
    Aceita arquivos .csv e .xlsx, consolida em um único DataFrame,
    cria colunas auxiliares temporais e armazena em sessão.
    
    Returns:
        JSON com session_id e metadados dos arquivos processados
    """
    try:
        # Verificar se há arquivos na requisição
        if 'files' not in request.files:
            return jsonify({
                "status": "error",
                "message": "Nenhum arquivo foi enviado."
            }), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({
                "status": "error",
                "message": "Lista de arquivos vazia."
            }), 400
        
        # Preparar dados para o analyzer
        files_data = []
        files_failed = []
        
        for file in files:
            if not file or file.filename == '':
                continue
            
            filename = file.filename
            
            # Validar extensão
            if not allowed_file(filename, ALLOWED_EXTENSIONS):
                files_failed.append({
                    "filename": filename,
                    "reason": "Formato não suportado (apenas .csv e .xlsx)"
                })
                continue
            
            try:
                # Ler bytes do arquivo
                file_bytes = file.read()
                files_data.append((file_bytes, filename))
            except Exception as e:
                files_failed.append({
                    "filename": filename,
                    "reason": f"Erro ao ler arquivo: {str(e)}"
                })
        
        # Usar DataAnalyzer para processar arquivos
        analyzer = get_data_analyzer()
        result = analyzer.load_files_from_bytes(files_data)
        
        # Adicionar falhas de validação inicial
        result['files_failed'].extend(files_failed)
        
        # Verificar se pelo menos um arquivo foi lido com sucesso
        if not result['files_ok']:
            return jsonify({
                "status": "error",
                "message": "Nenhum arquivo válido foi processado.",
                "files_success": result['files_ok'],
                "files_failed": result['files_failed']
            }), 400
        
        # Consolidar tabelas
        consolidated_df = analyzer.consolidate_tables()
        
        # Remover duplicatas
        initial_count = len(consolidated_df)
        consolidated_df = consolidated_df.drop_duplicates()
        duplicates_removed = initial_count - len(consolidated_df)
        
        if duplicates_removed > 0:
            print(f"[AlphaBot] ⚠️ Removidas {duplicates_removed} linhas duplicadas")
        
        # Gerar ID de sessão único
        session_id = str(uuid.uuid4())
        
        # Construir sumário
        summary = analyzer.build_summary(result['files_ok'], result['files_failed'])
        
        # Armazenar DataFrame em sessão (formato JSON)
        ALPHABOT_SESSIONS[session_id] = {
            "dataframe": consolidated_df.to_json(orient='split', date_format='iso'),
            "metadata": {
                "total_records": len(consolidated_df),
                "total_columns": len(consolidated_df.columns),
                "columns": list(consolidated_df.columns),
                "date_columns": summary['datetime_columns'],
                "files_success": result['files_ok'],
                "files_failed": result['files_failed']
            }
        }
        
        # Calcular período se houver colunas de data
        date_range = None
        if summary['datetime_columns']:
            date_range = {
                "min": analyzer.format_date(summary['date_range'][0]),
                "max": analyzer.format_date(summary['date_range'][1])
            }
        
        # Retornar resposta de sucesso
        return jsonify({
            "status": "success",
            "message": f"{len(result['files_ok'])} arquivo(s) processado(s) com sucesso.",
            "session_id": session_id,
            "metadata": {
                "total_records": len(consolidated_df),
                "total_columns": len(consolidated_df.columns),
                "columns": list(consolidated_df.columns),
                "date_columns": summary['datetime_columns'],
                "files_success": result['files_ok'],
                "files_failed": result['files_failed'],
                "date_range": date_range,
                "duplicates_removed": duplicates_removed
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro interno ao processar arquivos: {str(e)}"
        }), 500


@alphabot_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint de chat para AlphaBot com motor de validação interna.
    Usa as três personas: Analista → Crítico → Júri
    
    Returns:
        JSON com resposta do bot e metadados
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
        
        session_id = data.get('session_id')
        message = data.get('message')
        
        if not session_id or not message:
            return jsonify({"error": "session_id e message são obrigatórios"}), 400
        
        # Verificar se a sessão existe
        if session_id not in ALPHABOT_SESSIONS:
            return jsonify({
                "error": "Sessão não encontrada. Por favor, faça upload dos arquivos primeiro.",
                "session_id": session_id
            }), 404
        
        # Recuperar dados da sessão
        session_data = ALPHABOT_SESSIONS[session_id]
        df = pd.read_json(io.StringIO(session_data["dataframe"]), orient='split')
        metadata = session_data["metadata"]
        
        # Preparar contexto dos dados para o LLM
        data_context = f"""
**Dados Disponíveis:**
- Total de Registros: {metadata['total_records']}
- Total de Colunas: {metadata['total_columns']}
- Colunas: {', '.join(metadata['columns'])}
- Arquivos: {', '.join(metadata['files_success'])}
"""
        
        if metadata['date_columns']:
            data_context += f"\n- Colunas Temporais: {', '.join(metadata['date_columns'])}"
        
        # Análise estatística básica para contexto
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            data_context += f"\n- Colunas Numéricas: {', '.join(numeric_cols[:5])}..."
        
        # Preparar preview dos dados (primeiras 5 linhas)
        data_preview = df.head(5).to_markdown(index=False)
        
        # Criar serviço de IA
        ai_service = get_ai_service('alphabot')
        
        # PROMPT do motor de validação (Analista → Crítico → Júri)
        validation_prompt = f"""
{data_context}

**Preview dos Dados (5 primeiras linhas):**
```
{data_preview}
```

**Pergunta do Usuário:** {message}

**INSTRUÇÕES INTERNAS (NÃO MOSTRE ISSO AO USUÁRIO):**

Simule internamente o processo de deliberação:

1. **ANALISTA** - Execute a análise técnica nos dados:
   - Identifique quais colunas usar
   - Execute filtros, agregações, rankings necessários
   - Formule uma resposta preliminar baseada nos dados

2. **CRÍTICO** - Desafie a análise:
   - Há vieses ou suposições não validadas?
   - Faltam dados importantes para esta análise?
   - Há interpretações alternativas?
   
3. **JÚRI** - Sintetize a resposta final no formato:
   - **Resposta Direta:** [Uma frase clara]
   - **Análise Detalhada:** [Como chegou ao resultado]
   - **Insights Adicionais:** [Observações valiosas]
   - **Limitações e Contexto:** [Se aplicável]

Apresente APENAS a resposta final do Júri ao usuário.
"""
        
        # Gerar resposta
        answer = ai_service.generate_response(validation_prompt)
        
        return jsonify({
            "answer": answer,
            "session_id": session_id,
            "metadata": {
                "records_analyzed": len(df),
                "columns_available": len(df.columns)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Erro ao processar pergunta: {str(e)}",
            "session_id": session_id if 'session_id' in locals() else None
        }), 500


@alphabot_bp.route('/session/<session_id>', methods=['GET'])
def get_session(session_id: str):
    """
    Obtém informações sobre uma sessão existente.
    
    Args:
        session_id: ID da sessão
    
    Returns:
        JSON com metadados da sessão
    """
    if session_id not in ALPHABOT_SESSIONS:
        return jsonify({
            "error": "Sessão não encontrada",
            "session_id": session_id
        }), 404
    
    metadata = ALPHABOT_SESSIONS[session_id]['metadata']
    
    return jsonify({
        "session_id": session_id,
        "metadata": metadata
    }), 200


@alphabot_bp.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """
    Remove uma sessão existente.
    
    Args:
        session_id: ID da sessão
    
    Returns:
        JSON confirmando a remoção
    """
    if session_id not in ALPHABOT_SESSIONS:
        return jsonify({
            "error": "Sessão não encontrada",
            "session_id": session_id
        }), 404
    
    del ALPHABOT_SESSIONS[session_id]
    
    return jsonify({
        "message": "Sessão removida com sucesso",
        "session_id": session_id
    }), 200
