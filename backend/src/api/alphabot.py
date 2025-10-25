"""
AlphaBot API Routes
Endpoints para upload e análise de planilhas anexadas

Correções críticas:
- Isolamento de sessão por usuário (user_id + session_id)
- Processamento unificado de dados (força tipagem Quantidade/Receita/Data)
- Persistência completa de histórico de chat (user/assistant)
"""

import io
import uuid
from typing import Dict, Any
from flask import Blueprint, request, jsonify
import pandas as pd

from src.services import get_ai_service, get_data_analyzer
from src.utils import allowed_file, ALLOWED_EXTENSIONS
from src.utils.data_processor import process_dataframe_unified
import database


# Criar blueprint
alphabot_bp = Blueprint('alphabot', __name__, url_prefix='/api/alphabot')

# Armazenamento global para sessões do AlphaBot (ISOLADO POR USUÁRIO)
# Chave composta: f"{user_id}_{session_id}" quando user_id existir; caso contrário, usa apenas session_id
ALPHABOT_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Armazenamento global para conversações do AlphaBot (histórico de mensagens em memória)
# Chave: conversation_id -> { "id", "bot_id", "session_id", "user_id", "history": [...] }
ALPHABOT_CONVERSATIONS: Dict[str, Dict[str, Any]] = {}


def ensure_alphabot_conversation(conversation_id: str, session_id: str = None, user_id: int = None) -> Dict[str, Any]:
    """
    Garante que uma conversação do AlphaBot existe em memória, criando se necessário.
    
    Args:
        conversation_id: ID da conversação
        session_id: ID da sessão (opcional)
        user_id: ID do usuário (opcional)
    
    Returns:
        Dict da conversação
    """
    if conversation_id not in ALPHABOT_CONVERSATIONS:
        ALPHABOT_CONVERSATIONS[conversation_id] = {
            "id": conversation_id,
            "bot_id": "alphabot",
            "session_id": session_id,
            "user_id": user_id,
            "history": []
        }
    
    return ALPHABOT_CONVERSATIONS[conversation_id]


def append_alphabot_message(conversation: Dict[str, Any], role: str, content: str) -> None:
    """
    Adiciona uma mensagem ao histórico da conversação do AlphaBot.
    
    Args:
        conversation: Dict da conversação
        role: 'user' ou 'assistant'
        content: Conteúdo da mensagem
    """
    conversation["history"].append({
        "role": role,
        "content": content
    })


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
        # user_id pode ser enviado como campo de formulário junto aos arquivos
        user_id_raw = request.form.get('user_id')
        user_id = int(user_id_raw) if user_id_raw and user_id_raw.isdigit() else None
        
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

        # Alinhar com DriveBot: NÃO remover duplicatas automaticamente (apenas reportar)
        duplicates_count = int(consolidated_df.duplicated().sum())
        if duplicates_count > 0:
            print(f"[AlphaBot] ℹ️ {duplicates_count} linhas duplicadas detectadas (não removidas para paridade com DriveBot)")
        
        # Gerar ID de sessão único
        session_id = str(uuid.uuid4())
        
        # Construir sumário básico (antes da unificação) para levantar possíveis colunas temporais
        summary = analyzer.build_summary(result['files_ok'], result['files_failed'])

        # 🔧 Aplicar processamento UNIFICADO (corrige Quantidade/Receita/Data)
        try:
            print(f"[AlphaBot Upload] 📊 Iniciando processamento de {len(consolidated_df)} linhas, {len(consolidated_df.columns)} colunas")
            print(f"[AlphaBot Upload] Colunas originais: {list(consolidated_df.columns)}")
            print(f"[AlphaBot Upload] Tipos originais: {dict(consolidated_df.dtypes)}")
            
            consolidated_df, processing_metadata = process_dataframe_unified(
                consolidated_df,
                source_info="AlphaBot_Upload"
            )
            print(f"[AlphaBot Upload] ✅ Processamento unificado concluído: {len(consolidated_df)} linhas")
            print(f"[AlphaBot Upload] Colunas processadas: {list(consolidated_df.columns)}")
            print(f"[AlphaBot Upload] Tipos processados: {dict(consolidated_df.dtypes)}")
            
            # Exibir sumário financeiro se disponível
            if processing_metadata.get('financial_summary'):
                fin_summary = processing_metadata['financial_summary']
                print(f"[AlphaBot Upload] 💰 Sumário Financeiro:")
                print(f"  - Quantidade Total: {fin_summary.get('total_quantidade', 'N/A')}")
                print(f"  - Receita Total: {fin_summary.get('total_receita_formatted', 'N/A')}")
            
        except ValueError as val_error:
            # Erro específico de conversão de valores
            print(f"[AlphaBot Upload] ❌ ValueError - Erro de validação de dados: {val_error}")
            import traceback
            print(f"[AlphaBot Upload] Stack trace completo:")
            traceback.print_exc()
            return jsonify({
                "status": "error",
                "message": f"Erro ao processar dados: {str(val_error)}. Verifique se os dados numéricos estão formatados corretamente."
            }), 400
        except Exception as proc_error:
            # Outros erros de processamento
            print(f"[AlphaBot Upload] ❌ Erro no processamento unificado: {proc_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "status": "error",
                "message": f"Erro interno ao processar dados: {str(proc_error)}"
            }), 500
        
        # Construir chave composta (isolamento por usuário)
        session_key = f"{user_id}_{session_id}" if user_id else session_id

        # Armazenar DataFrame em sessão (formato JSON) isolado por usuário
        ALPHABOT_SESSIONS[session_key] = {
            "dataframe": consolidated_df.to_json(orient='split', date_format='iso'),
            "metadata": {
                "total_records": len(consolidated_df),
                "total_columns": len(consolidated_df.columns),
                "columns": list(consolidated_df.columns),
                "date_columns": [c for c, info in processing_metadata.get('columns_processed', {}).items() if info.get('type') == 'temporal'],
                "files_success": result['files_ok'],
                "files_failed": result['files_failed']
            }
        }

        # Persistir sessão no banco se user_id fornecido
        created_conversation_id = None
        if user_id is not None:
            try:
                success = database.create_alphabot_session(
                    user_id=int(user_id),
                    session_id=session_id,
                    dataframe_json=consolidated_df.to_json(orient='split', date_format='iso'),
                    metadata={
                        "total_records": len(consolidated_df),
                        "total_columns": len(consolidated_df.columns),
                        "columns": list(consolidated_df.columns),
                        "date_columns": [c for c, info in processing_metadata.get('columns_processed', {}).items() if info.get('type') == 'temporal']
                    },
                    files_info=result['files_ok']
                )
                if success:
                    print(f"[AlphaBot Upload] ✅ Sessão persistida no banco para user_id={user_id}, session_id={session_id}")
                    # Criar conversa inicial vinculada à sessão, para facilitar o chat
                    created_conversation_id = str(uuid.uuid4())
                    conv_title = f"Análise AlphaBot - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}"
                    conv_ok = database.create_alphabot_conversation(
                        conversation_id=created_conversation_id,
                        session_id=session_id,
                        user_id=int(user_id),
                        title=conv_title
                    )
                    print(f"[AlphaBot Upload] {'✅' if conv_ok else '⚠️'} Conversa inicial criada: {created_conversation_id}")
                else:
                    print(f"[AlphaBot Upload] ⚠️ Falha ao criar sessão no banco (retornou False)")
            except Exception as e:
                print(f"[AlphaBot Upload] ❌ Erro ao persistir sessão: {e}")
                import traceback
                traceback.print_exc()
        
        # Calcular período se houver colunas de data (após unificação)
        date_range = None
        date_cols = [c for c, info in processing_metadata.get('columns_processed', {}).items() if info.get('type') == 'temporal']
        if date_cols:
            try:
                min_date = None
                max_date = None
                for dc in date_cols:
                    valid = consolidated_df[dc].dropna()
                    if not valid.empty:
                        dmin = valid.min()
                        dmax = valid.max()
                        min_date = dmin if min_date is None or dmin < min_date else min_date
                        max_date = dmax if max_date is None or dmax > max_date else max_date
                if min_date or max_date:
                    date_range = {
                        "min": analyzer.format_date(min_date),
                        "max": analyzer.format_date(max_date)
                    }
            except Exception as _:
                pass
        
        # Retornar resposta de sucesso
        response_payload = {
            "status": "success",
            "message": f"{len(result['files_ok'])} arquivo(s) processado(s) com sucesso.",
            "session_id": session_id,
            "metadata": {
                "total_records": len(consolidated_df),
                "total_columns": len(consolidated_df.columns),
                "columns": list(consolidated_df.columns),
                "date_columns": date_cols,
                "files_success": result['files_ok'],
                "files_failed": result['files_failed'],
                "date_range": date_range,
                "duplicates_detected": duplicates_count
            }
        }
        if created_conversation_id:
            response_payload["conversation_id"] = created_conversation_id
        return jsonify(response_payload), 200
        
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
        conversation_id = data.get('conversation_id')
        user_id = data.get('user_id')
        
        if not session_id or not message:
            return jsonify({"error": "session_id e message são obrigatórios"}), 400

        # Construir chave de sessão isolada
        session_key = f"{user_id}_{session_id}" if user_id else session_id

        # Recuperar dados da sessão: preferir persistência no banco quando user_id disponível
        df = None
        metadata = None
        if user_id:
            session_row = database.get_alphabot_session(int(user_id), session_id)
            if session_row:
                try:
                    df = pd.read_json(io.StringIO(session_row["dataframe"]), orient='split')
                    metadata = session_row["metadata"]
                except Exception:
                    df = None
                    metadata = None

        if df is None:
            # Fallback: sessão em memória
            if session_key not in ALPHABOT_SESSIONS:
                return jsonify({
                    "error": "Sessão não encontrada. Por favor, faça upload dos arquivos primeiro.",
                    "session_id": session_id
                }), 404
            session_data = ALPHABOT_SESSIONS[session_key]
            df = pd.read_json(io.StringIO(session_data["dataframe"]), orient='split')
            metadata = session_data["metadata"]
        
        # Preparar contexto dos dados para o LLM (robusto a metadados ausentes)
        total_records = metadata.get('total_records') if isinstance(metadata, dict) else None
        total_columns = metadata.get('total_columns') if isinstance(metadata, dict) else None
        columns_list = metadata.get('columns', []) if isinstance(metadata, dict) else []

        # Obter lista de arquivos com fallback: metadata.files_success (memória) OU session_row.files_info (banco)
        files_success = []
        if isinstance(metadata, dict) and 'files_success' in metadata:
            files_success = metadata.get('files_success') or []
        elif user_id and 'session_row' in locals():
            try:
                files_success = session_row.get('files_info') or []
            except Exception:
                files_success = []

        data_context = "\n**Dados Disponíveis:**\n"
        if total_records is not None:
            data_context += f"- Total de Registros: {total_records}\n"
        if total_columns is not None:
            data_context += f"- Total de Colunas: {total_columns}\n"
        if columns_list:
            data_context += f"- Colunas: {', '.join(columns_list)}\n"
        if files_success:
            data_context += f"- Arquivos: {', '.join(files_success)}\n"

        date_cols = metadata.get('date_columns', []) if isinstance(metadata, dict) else []
        if date_cols:
            data_context += f"- Colunas Temporais: {', '.join(date_cols)}\n"
        
        # Análise estatística básica para contexto
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            data_context += f"\n- Colunas Numéricas: {', '.join(numeric_cols[:5])}..."
        
        # Preparar preview dos dados (primeiras 5 linhas)
        data_preview = df.head(5).to_markdown(index=False)
        
        # Garantir conversation_id quando user_id foi informado (auto-criar se necessário)
        if user_id and not conversation_id:
            try:
                auto_title = f"Chat AlphaBot - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}"
                conversation_id = database.find_or_create_alphabot_conversation_for_session(int(user_id), session_id, auto_title)
                if conversation_id:
                    print(f"[AlphaBot Chat] ✅ Conversa pronta: {conversation_id}")
                else:
                    print(f"[AlphaBot Chat] ⚠️ Não foi possível criar/obter conversa para user_id={user_id} session_id={session_id}")
            except Exception as e:
                print(f"[AlphaBot Chat] ❌ Erro ao preparar conversa: {e}")
        
        # Garantir que a conversação existe em memória
        conversation = ensure_alphabot_conversation(conversation_id, session_id, user_id)
        
        # Adicionar mensagem do usuário ao histórico em memória
        append_alphabot_message(conversation, "user", message)

        # Persistir mensagem do usuário no histórico, garantindo conversa
        if conversation_id and user_id:
            try:
                existing = database.get_alphabot_conversation(conversation_id)
                if not existing:
                    conv_created = database.create_alphabot_conversation(
                        conversation_id=conversation_id,
                        session_id=session_id,
                        user_id=int(user_id),
                        title=f"Chat AlphaBot - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}"
                    )
                    if conv_created:
                        print(f"[AlphaBot Chat] ✅ Nova conversa criada: {conversation_id}")
                    else:
                        print(f"[AlphaBot Chat] ⚠️ Falha ao criar conversa: {conversation_id}")
                
                msg_saved = database.add_alphabot_message(
                    conversation_id=conversation_id,
                    author='user',
                    text=message,
                    time=int(pd.Timestamp.now().timestamp() * 1000)
                )
                if msg_saved:
                    print(f"[AlphaBot Chat] ✅ Mensagem do usuário salva: {conversation_id}")
                else:
                    print(f"[AlphaBot Chat] ⚠️ Falha ao salvar mensagem de usuário: {conversation_id}")
            except Exception as e:
                print(f"[AlphaBot Chat] ❌ Erro ao salvar mensagem de usuário: {e}")
                import traceback
                traceback.print_exc()
        elif conversation_id:
            # conversation_id fornecido mas sem user_id
            print(f"[AlphaBot Chat] ⚠️ conversation_id fornecido sem user_id - mensagem NÃO será persistida")
        else:
            # Sem conversation_id
            print(f"[AlphaBot Chat] ⚠️ conversation_id não fornecido - mensagem NÃO será persistida")

        # Cálculo determinístico para perguntas de faturamento (evita alucinações)
        computed_answer = None
        try:
            import re
            # Detectar ano solicitado na pergunta (fallback: maior ano disponível)
            years_in_msg = re.findall(r"(19\d{2}|20\d{2})", message)
            requested_year = int(years_in_msg[0]) if years_in_msg else None

            # Detectar possíveis colunas base de data e seus derivados
            date_cols = metadata.get('date_columns', []) if isinstance(metadata, dict) else []
            base_date_col = date_cols[0] if date_cols else None
            ano_col = f"{base_date_col}_Ano" if base_date_col and f"{base_date_col}_Ano" in df.columns else None
            mes_col = f"{base_date_col}_Mes" if base_date_col and f"{base_date_col}_Mes" in df.columns else None
            mes_nome_col = f"{base_date_col}_Mes_Nome" if base_date_col and f"{base_date_col}_Mes_Nome" in df.columns else None

            # Identificar coluna de receita
            receita_candidates = [c for c in df.columns if any(k in c.lower() for k in ['receita', 'faturamento'])]
            if not receita_candidates:
                receita_candidates = [c for c in df.columns if 'valor' in c.lower() or 'total' in c.lower()]
            receita_col = None
            for c in receita_candidates:
                if pd.api.types.is_numeric_dtype(df[c]):
                    receita_col = c
                    break
            # Fallback para receita derivada criada pelo processor
            if not receita_col and 'Receita_Total_Derivada' in df.columns and pd.api.types.is_numeric_dtype(df['Receita_Total_Derivada']):
                receita_col = 'Receita_Total_Derivada'

            # Se necessário, tentar derivar receita a partir de quantidade x preço
            if not receita_col:
                qtd_col = next((c for c in df.columns if 'quantidade' in c.lower() and pd.api.types.is_numeric_dtype(df[c])), None)
                preco_col = next((c for c in df.columns if any(k in c.lower() for k in ['preco', 'preço']) and pd.api.types.is_numeric_dtype(df[c])), None)
                if qtd_col and preco_col:
                    receita_col = '__tmp_receita__'
                    df[receita_col] = df[qtd_col].fillna(0) * df[preco_col].fillna(0)

            # Prosseguir apenas se houver receita numérica e algum indicador temporal
            if receita_col and (ano_col or base_date_col in df.columns):
                # Filtrar ano
                if not requested_year and ano_col:
                    # Escolher maior ano disponível
                    try:
                        requested_year = int(df[ano_col].dropna().max()) if not df[ano_col].dropna().empty else None
                    except Exception:
                        requested_year = None
                if ano_col and requested_year:
                    df_year = df[df[ano_col] == requested_year]
                elif base_date_col in df.columns and pd.api.types.is_datetime64_any_dtype(df[base_date_col]):
                    df_year = df[df[base_date_col].dt.year == requested_year] if requested_year else df
                else:
                    df_year = df

                total_receita = float(df_year[receita_col].sum()) if not df_year.empty else 0.0

                # Mensal
                if mes_col and requested_year:
                    grp = df_year.groupby([mes_col], dropna=True)[receita_col].sum().reset_index()
                    grp = grp.sort_values(mes_col)
                    mes_map = df[[mes_col, mes_nome_col]].dropna().drop_duplicates().set_index(mes_col)[mes_nome_col].to_dict() if mes_nome_col in df.columns else {}
                    monthly = [(int(r[mes_col]), float(r[receita_col]), mes_map.get(int(r[mes_col]))) for _, r in grp.iterrows()]
                else:
                    monthly = []

                # Formatar
                def brl(v: float) -> str:
                    return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

                lines = []
                lines.append(f"## 🎯 OBJETIVO")
                if requested_year:
                    lines.append(f"Informar a fatura total do ano de {requested_year} e comparar a fatura total dos 12 meses.")
                else:
                    lines.append(f"Informar a fatura total e comparação mensal.")
                
                lines.append("")
                lines.append(f"## 📊 EXECUÇÃO E RESULTADO")
                if requested_year:
                    lines.append(f"A fatura total para o ano de {requested_year} foi calculada como **{brl(total_receita)}**.")
                else:
                    lines.append(f"A fatura total encontrada é de **{brl(total_receita)}**.")

                if monthly:
                    lines.append("")
                    lines.append("A seguir, a comparação da fatura total para cada um dos 12 meses:")
                    lines.append("")
                    lines.append("| Mês | Fatura Mensal (R$) |")
                    lines.append("|-----|-------------------:|")
                    for m, val, nome in monthly:
                        label = nome.capitalize() if isinstance(nome, str) else str(m)
                        lines.append(f"| {label} | {brl(val).replace('R$ ', '')} |")
                    lines.append(f"| **TOTAL** | **{brl(total_receita).replace('R$ ', '')}** |")
                    
                    # Adicionar insight
                    if len(monthly) >= 2:
                        max_month = max(monthly, key=lambda x: x[1])
                        min_month = min(monthly, key=lambda x: x[1])
                        max_label = max_month[2].capitalize() if isinstance(max_month[2], str) else str(max_month[0])
                        min_label = min_month[2].capitalize() if isinstance(min_month[2], str) else str(min_month[0])
                        
                        lines.append("")
                        lines.append("## 💡 INSIGHT")
                        lines.append(f"A análise da fatura mensal de {requested_year if requested_year else 'período analisado'} revela uma variação significativa ao longo do ano. ")
                        lines.append(f"Observa-se que o mês de **{max_label}** ({brl(max_month[1])}) apresentou a maior fatura, ")
                        lines.append(f"enquanto **{min_label}** ({brl(min_month[1])}) registrou a menor fatura. ")
                        lines.append("Esta sazonalidade pode ser um fator importante para planejamento e projeções futuras.")

                computed_answer = "\n".join(lines)
        except Exception as e:
            print(f"[AlphaBot Chat] ⚠️ Falha no cálculo determinístico: {e}")

        if computed_answer:
            answer = computed_answer
        else:
            # Criar serviço de IA e usar fallback com contexto/preview
            ai_service = get_ai_service('alphabot')
            validation_prompt = f"""
{data_context}

**Preview dos Dados (5 primeiras linhas):**
```
{data_preview}
```

**Pergunta do Usuário:** {message}

Responda apenas com base nos dados; se a pergunta exigir somas/contagens fora do preview, explique a limitação e peça para rodar "calcular faturamento {pd.Timestamp.now().year}".
"""
            answer = ai_service.generate_response(validation_prompt)
        
        # Adicionar resposta do bot ao histórico em memória
        append_alphabot_message(conversation, "assistant", answer)

        # Persistir resposta do bot
        if conversation_id and user_id:
            try:
                msg_saved = database.add_alphabot_message(
                    conversation_id=conversation_id,
                    author='bot',
                    text=answer,
                    time=int(pd.Timestamp.now().timestamp() * 1000)
                )
                if msg_saved:
                    print(f"[AlphaBot Chat] ✅ Resposta do bot salva: {conversation_id}")
                else:
                    print(f"[AlphaBot Chat] ⚠️ Falha ao salvar resposta do bot: {conversation_id}")
            except Exception as e:
                print(f"[AlphaBot Chat] ❌ Erro ao salvar resposta do bot: {e}")
                import traceback
                traceback.print_exc()
        elif conversation_id:
            print(f"[AlphaBot Chat] ⚠️ conversation_id fornecido sem user_id - resposta NÃO será persistida")
        else:
            print(f"[AlphaBot Chat] ⚠️ conversation_id não fornecido - resposta NÃO será persistida")
        
        resp_meta = {
            "records_analyzed": len(df),
            "columns_available": len(df.columns)
        }
        payload = {
            "answer": answer,
            "session_id": session_id,
            "metadata": resp_meta
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id
        return jsonify(payload), 200
        
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


# ===============================
# Endpoints de Histórico AlphaBot
# ===============================

@alphabot_bp.route('/conversations', methods=['GET'])
def list_alphabot_conversations():
    """
    Lista conversas do AlphaBot para um usuário.
    Query params: user_id (obrigatório)
    """
    try:
        user_id_param = request.args.get('user_id')
        if not user_id_param or not user_id_param.isdigit():
            return jsonify({"error": "user_id é obrigatório e deve ser numérico"}), 400
        user_id = int(user_id_param)

        convs = database.get_user_alphabot_conversations(user_id)
        return jsonify({
            "user_id": user_id,
            "conversations": convs
        }), 200
    except Exception as e:
        return jsonify({"error": f"Erro ao listar conversas: {str(e)}"}), 500


@alphabot_bp.route('/conversation/<conversation_id>', methods=['GET'])
def get_alphabot_conversation_meta(conversation_id: str):
    """
    Retorna metadados básicos de uma conversa específica do AlphaBot.
    Primeiro tenta buscar do banco, depois da memória.
    """
    try:
        # Tentar buscar do banco primeiro
        conv = database.get_alphabot_conversation(conversation_id)
        if conv:
            # Se encontrou no banco, enriquecer com dados da memória se disponível
            if conversation_id in ALPHABOT_CONVERSATIONS:
                conv['history_length'] = len(ALPHABOT_CONVERSATIONS[conversation_id]['history'])
            return jsonify(conv), 200
        
        # Fallback: buscar da memória
        if conversation_id in ALPHABOT_CONVERSATIONS:
            mem_conv = ALPHABOT_CONVERSATIONS[conversation_id]
            return jsonify({
                "id": conversation_id,
                "session_id": mem_conv.get("session_id"),
                "user_id": mem_conv.get("user_id"),
                "bot_id": "alphabot",
                "history_length": len(mem_conv.get("history", []))
            }), 200
        
        return jsonify({"error": "Conversa não encontrada", "conversation_id": conversation_id}), 404
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar conversa: {str(e)}"}), 500


@alphabot_bp.route('/conversation/<conversation_id>/messages', methods=['GET'])
def get_alphabot_conversation_msgs(conversation_id: str):
    """
    Retorna todas as mensagens de uma conversa do AlphaBot.
    Prioriza memória para mensagens recentes, com fallback para banco.
    """
    try:
        messages = []
        
        # Primeiro tentar buscar da memória (mais rápido e tem histórico completo da sessão atual)
        if conversation_id in ALPHABOT_CONVERSATIONS:
            mem_conv = ALPHABOT_CONVERSATIONS[conversation_id]
            history = mem_conv.get("history", [])
            
            # Converter formato do histórico para formato de mensagens
            import time
            for idx, entry in enumerate(history):
                messages.append({
                    "id": f"msg-mem-{idx}",
                    "author": entry["role"] if entry["role"] == "user" else "bot",
                    "text": entry["content"],
                    "time": int(time.time() * 1000) - ((len(history) - idx) * 1000)  # Timestamps aproximados
                })
            
            return jsonify({
                "conversation_id": conversation_id,
                "messages": messages,
                "source": "memory"
            }), 200
        
        # Fallback: buscar do banco
        conv = database.get_alphabot_conversation(conversation_id)
        if not conv:
            return jsonify({
                "conversation_id": conversation_id,
                "messages": [],
                "source": "not_found"
            }), 200
        
        db_messages = database.get_alphabot_conversation_messages(conversation_id)
        return jsonify({
            "conversation_id": conversation_id,
            "messages": db_messages,
            "source": "database"
        }), 200
        
    except Exception as e:
        print(f"❌ Erro ao buscar mensagens: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro ao buscar mensagens: {str(e)}"}), 500
