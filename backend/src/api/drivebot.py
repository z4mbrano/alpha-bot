"""
DriveBot API Routes
Endpoints para análise de dados do Google Drive
"""

import re
import uuid
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify

from ..services import get_ai_service, get_drive_service, get_data_analyzer
from ..utils import extract_folder_id_from_url, is_valid_google_drive_folder_id


# Criar blueprint
drivebot_bp = Blueprint('drivebot', __name__, url_prefix='/api/drivebot')

# Armazenamento global para conversações do DriveBot
DRIVEBOT_CONVERSATIONS: Dict[str, Dict[str, Any]] = {}


def ensure_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Garante que uma conversação existe, criando se necessário.
    
    Args:
        conversation_id: ID da conversação
    
    Returns:
        Dict da conversação
    """
    if conversation_id not in DRIVEBOT_CONVERSATIONS:
        DRIVEBOT_CONVERSATIONS[conversation_id] = {
            "id": conversation_id,
            "bot_id": "drivebot",
            "history": [],
            "drive": {}
        }
    
    return DRIVEBOT_CONVERSATIONS[conversation_id]


def append_message(conversation: Dict[str, Any], role: str, content: str) -> None:
    """
    Adiciona uma mensagem ao histórico da conversação.
    
    Args:
        conversation: Dict da conversação
        role: 'user' ou 'assistant'
        content: Conteúdo da mensagem
    """
    conversation["history"].append({
        "role": role,
        "content": content
    })


def build_discovery_bundle(folder_id: str) -> Dict[str, Any]:
    """
    Constrói bundle de descoberta para uma pasta do Google Drive.
    
    Args:
        folder_id: ID da pasta no Google Drive
    
    Returns:
        Dict com relatório, tabelas, sumário e arquivos processados
    """
    try:
        # Obter serviços
        drive = get_drive_service()
        analyzer = get_data_analyzer()
        
        # Verificar se pasta existe
        if not drive.folder_exists(folder_id):
            return {
                "error": "Pasta não encontrada ou sem permissão de acesso",
                "report": "❌ Erro: Pasta não acessível",
                "tables": [],
                "summary": {},
                "files_ok": [],
                "files_failed": []
            }
        
        # Listar arquivos da pasta
        mime_types = [
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.google-apps.spreadsheet'
        ]
        
        files = drive.list_folder_files(folder_id, mime_types=mime_types)
        
        # Carregar arquivos
        result = analyzer.load_files_from_drive(drive.drive_service, files)
        
        # Consolidar tabelas
        if analyzer.tables:
            analyzer.consolidate_tables()
        
        # Construir sumário
        summary = analyzer.build_summary(result['files_ok'], result['files_failed'])
        
        # Gerar relatório
        report = analyzer.build_discovery_report(summary)
        
        return {
            "report": report,
            "tables": analyzer.tables,
            "summary": summary,
            "files_ok": result['files_ok'],
            "files_failed": result['files_failed']
        }
    
    except Exception as error:
        return {
            "error": str(error),
            "report": f"❌ Erro ao processar pasta: {error}",
            "tables": [],
            "summary": {},
            "files_ok": [],
            "files_failed": []
        }


@drivebot_bp.route('/chat', methods=['POST'])
def chat():
    """
    Endpoint principal de chat do DriveBot.
    
    Gerencia o fluxo de descoberta de dados e análise.
    
    Returns:
        JSON com resposta do bot
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "JSON inválido"}), 400
        
        message = data.get('message')
        conversation_id = data.get('conversation_id')
        
        if not message:
            return jsonify({"error": "message é obrigatório"}), 400
        
        # Gerar ou usar conversation_id existente
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Garantir que a conversação existe
        conversation = ensure_conversation(conversation_id)
        append_message(conversation, "user", message)
        
        # Extrair ID da pasta do Drive se houver
        folder_id = extract_folder_id_from_url(message)
        
        # Se não encontrou pela URL, tentar validar como ID direto
        if not folder_id and is_valid_google_drive_folder_id(message.strip()):
            folder_id = message.strip()
        
        drive_state = conversation.get("drive", {})
        
        # Se encontrou ID de pasta, processar descoberta
        if folder_id:
            bundle = build_discovery_bundle(folder_id)
            
            if "error" in bundle:
                response_text = bundle["report"]
            else:
                # Atualizar estado do drive na conversação
                drive_state.update({
                    "folder_id": folder_id,
                    "report": bundle["report"],
                    "tables": bundle["tables"],
                    "summary": bundle["summary"],
                    "files_ok": bundle["files_ok"],
                    "files_failed": bundle["files_failed"],
                })
                
                conversation["drive"] = drive_state
                
                header = (
                    f"Recebi o ID: {folder_id}. Iniciando a conexão e a leitura dos arquivos. "
                    "Por favor, aguarde um momento."
                )
                response_text = f"{header}\n\n{bundle['report']}"
            
            append_message(conversation, "assistant", response_text)
            return jsonify({
                "response": response_text,
                "conversation_id": conversation_id
            }), 200
        
        # Se não há dados carregados ainda, pedir ID da pasta
        if not drive_state.get("folder_id"):
            response_text = (
                "## Preparando o ambiente de análise\n\n"
                "Para avançar com a exploração dos dados, siga estes passos:\n"
                "1. Envie o ID da pasta do Google Drive (ou cole o link completo).\n"
                "2. Garanta que a Service Account tenha acesso de visualizador à pasta.\n\n"
                "Assim que a pasta estiver acessível, poderei responder suas perguntas usando os dados consolidados."
            )
            append_message(conversation, "assistant", response_text)
            return jsonify({
                "response": response_text,
                "conversation_id": conversation_id
            }), 200
        
        # Processar pergunta sobre dados já carregados
        ai_service = get_ai_service('drivebot')
        
        # Preparar contexto
        context_sections = []
        
        if drive_state.get("report"):
            context_sections.append("## Contexto da descoberta\n" + drive_state["report"])
        
        # Histórico recente (últimas 6 mensagens)
        history_entries = conversation["history"][-6:]
        if history_entries:
            history_lines = []
            for entry in history_entries:
                speaker = 'Usuário' if entry['role'] == 'user' else 'DriveBot'
                history_lines.append(f"- {speaker}: {entry['content']}")
            context_sections.append("## Histórico recente\n" + "\n".join(history_lines))
        
        # Montar prompt completo
        full_prompt = "\n\n".join(context_sections) + f"\n\nUsuário: {message}\nDriveBot:"
        
        # Gerar resposta
        response_text = ai_service.generate_response(full_prompt)
        
        if not response_text:
            response_text = (
                "## Não consegui concluir a análise\n\n"
                "Os dados estão mapeados, mas não consegui gerar a síntese solicitada. "
                "Tente reformular a pergunta ou peça um recorte diferente."
            )
        
        append_message(conversation, "assistant", response_text)
        
        return jsonify({
            "response": response_text,
            "conversation_id": conversation_id
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Erro ao processar pergunta: {str(e)}",
            "conversation_id": conversation_id if 'conversation_id' in locals() else None
        }), 500


@drivebot_bp.route('/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id: str):
    """
    Obtém informações sobre uma conversação existente.
    
    Args:
        conversation_id: ID da conversação
    
    Returns:
        JSON com dados da conversação
    """
    if conversation_id not in DRIVEBOT_CONVERSATIONS:
        return jsonify({
            "error": "Conversação não encontrada",
            "conversation_id": conversation_id
        }), 404
    
    conversation = DRIVEBOT_CONVERSATIONS[conversation_id]
    
    return jsonify({
        "conversation_id": conversation_id,
        "history_length": len(conversation["history"]),
        "has_drive_data": bool(conversation.get("drive", {}).get("folder_id")),
        "folder_id": conversation.get("drive", {}).get("folder_id")
    }), 200


@drivebot_bp.route('/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id: str):
    """
    Remove uma conversação existente.
    
    Args:
        conversation_id: ID da conversação
    
    Returns:
        JSON confirmando a remoção
    """
    if conversation_id not in DRIVEBOT_CONVERSATIONS:
        return jsonify({
            "error": "Conversação não encontrada",
            "conversation_id": conversation_id
        }), 404
    
    del DRIVEBOT_CONVERSATIONS[conversation_id]
    
    return jsonify({
        "message": "Conversação removida com sucesso",
        "conversation_id": conversation_id
    }), 200
