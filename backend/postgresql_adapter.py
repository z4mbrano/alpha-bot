"""
PostgreSQL Adapter para migração do SQLite
Autor: ALPHABOT - Render Migration
Data: 2025-11-19
"""

import os
import json
import hashlib
import secrets
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager

# Configuração de conexão PostgreSQL
def get_database_url() -> str:
    """Retorna URL de conexão do PostgreSQL baseada no ambiente"""
    if os.environ.get('DATABASE_URL'):
        # Render: URL fornecida automaticamente
        return os.environ['DATABASE_URL']
    elif os.environ.get('POSTGRES_URL'):
        # Alternativa Render/Railway
        return os.environ['POSTGRES_URL']
    else:
        # Construir URL manualmente para desenvolvimento local
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5432')
        database = os.environ.get('POSTGRES_DB', 'alphabot')
        user = os.environ.get('POSTGRES_USER', 'postgres')
        password = os.environ.get('POSTGRES_PASSWORD', 'password')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

@contextmanager
def get_connection():
    """Context manager para conexão PostgreSQL"""
    database_url = get_database_url()
    conn = None
    try:
        conn = psycopg2.connect(
            database_url,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def init_database():
    """Inicializa o banco PostgreSQL com todas as tabelas"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                alphabot_data_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de conversas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id VARCHAR(255) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                bot_type VARCHAR(100) NOT NULL,
                title VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela de mensagens
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id VARCHAR(255) NOT NULL,
                author VARCHAR(100) NOT NULL,
                text TEXT NOT NULL,
                time BIGINT NOT NULL,
                chart_data TEXT,
                suggestions TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabelas exclusivas do AlphaBot
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alphabot_sessions (
                id VARCHAR(255) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                dataframe_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                files_info TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alphabot_conversations (
                id VARCHAR(255) PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                user_id INTEGER NOT NULL,
                title VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES alphabot_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alphabot_messages (
                id SERIAL PRIMARY KEY,
                conversation_id VARCHAR(255) NOT NULL,
                author VARCHAR(20) NOT NULL CHECK (author IN ('user', 'bot')),
                text TEXT NOT NULL,
                time BIGINT NOT NULL,
                chart_data TEXT,
                suggestions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES alphabot_conversations(id) ON DELETE CASCADE
            )
        ''')

        # Índices para otimizar buscas
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_sessions_user_id ON alphabot_sessions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_conversations_session_id ON alphabot_conversations(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_conversations_user_id ON alphabot_conversations(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_messages_conversation_id ON alphabot_messages(conversation_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_messages_time ON alphabot_messages(time)')
        
        conn.commit()
        print("✅ Database PostgreSQL inicializado com sucesso!")

# ========================================
# FUNÇÕES DE AUTENTICAÇÃO
# ========================================

def hash_password(password: str) -> str:
    """Gera hash SHA-256 da senha."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Cria um novo usuário."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            password_hash = hash_password(password)
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id, username, created_at',
                (username, password_hash)
            )
            row = cursor.fetchone()
            conn.commit()
            
            return {
                'user_id': row['id'],
                'username': row['username'],
                'created_at': row['created_at']
            }
        except psycopg2.IntegrityError:
            return None  # Username já existe

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Autentica usuário verificando senha."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            'SELECT id, username, created_at FROM users WHERE username = %s AND password_hash = %s',
            (username, password_hash)
        )
        
        row = cursor.fetchone()
        
        if row:
            return {
                'user_id': row['id'],
                'username': row['username'],
                'created_at': row['created_at']
            }
        return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retorna dados do usuário pelo ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, username, created_at FROM users WHERE id = %s',
            (user_id,)
        )
        
        row = cursor.fetchone()
        
        if row:
            return {
                'user_id': row['id'],
                'username': row['username'],
                'created_at': row['created_at']
            }
        return None

# ========================================
# FUNÇÕES DE CONVERSAS
# ========================================

def create_conversation(user_id: int, bot_type: str, title: str = "Nova Conversa") -> str:
    """Cria uma nova conversa."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        conversation_id = secrets.token_urlsafe(16)
        cursor.execute(
            'INSERT INTO conversations (id, user_id, bot_type, title) VALUES (%s, %s, %s, %s)',
            (conversation_id, user_id, bot_type, title)
        )
        
        conn.commit()
        return conversation_id

def get_user_conversations(user_id: int, bot_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista todas as conversas do usuário."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if bot_type:
            cursor.execute(
                '''SELECT id, user_id, bot_type, title, created_at, updated_at 
                   FROM conversations 
                   WHERE user_id = %s AND bot_type = %s 
                   ORDER BY updated_at DESC''',
                (user_id, bot_type)
            )
        else:
            cursor.execute(
                '''SELECT id, user_id, bot_type, title, created_at, updated_at 
                   FROM conversations 
                   WHERE user_id = %s 
                   ORDER BY updated_at DESC''',
                (user_id,)
            )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_conversation(conversation_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """Retorna dados de uma conversa específica."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT id, user_id, bot_type, title, created_at, updated_at 
               FROM conversations 
               WHERE id = %s AND user_id = %s''',
            (conversation_id, user_id)
        )
        
        row = cursor.fetchone()
        return dict(row) if row else None

def update_conversation_title(conversation_id: str, user_id: int, title: str) -> bool:
    """Atualiza o título de uma conversa."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            '''UPDATE conversations 
               SET title = %s, updated_at = CURRENT_TIMESTAMP 
               WHERE id = %s AND user_id = %s''',
            (title, conversation_id, user_id)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        return success

def delete_conversation(conversation_id: str, user_id: int) -> bool:
    """Delete uma conversa e todas as mensagens associadas."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM conversations WHERE id = %s AND user_id = %s',
            (conversation_id, user_id)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        return success

def touch_conversation(conversation_id: str):
    """Atualiza o timestamp updated_at de uma conversa."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s',
            (conversation_id,)
        )
        
        conn.commit()

# ========================================
# FUNÇÕES DE MENSAGENS
# ========================================

def add_message(
    conversation_id: str,
    author: str,
    text: str,
    time: int,
    chart_data: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None
) -> int:
    """Adiciona uma mensagem à conversa."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        chart_json = json.dumps(chart_data) if chart_data else None
        suggestions_json = json.dumps(suggestions) if suggestions else None
        
        cursor.execute(
            '''INSERT INTO messages (conversation_id, author, text, time, chart_data, suggestions)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id''',
            (conversation_id, author, text, time, chart_json, suggestions_json)
        )
        
        message_id = cursor.fetchone()['id']
        conn.commit()
        
        # Atualizar timestamp da conversa
        touch_conversation(conversation_id)
        
        return message_id

def get_conversation_messages(conversation_id: str, user_id: int) -> List[Dict[str, Any]]:
    """Retorna todas as mensagens de uma conversa."""
    # Verificar se conversa existe e pertence ao usuário
    conversation = get_conversation(conversation_id, user_id)
    if not conversation:
        return []
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT id, author, text, time, chart_data, suggestions
               FROM messages
               WHERE conversation_id = %s
               ORDER BY time ASC''',
            (conversation_id,)
        )
        
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            message = {
                'id': row['id'],
                'author': row['author'],
                'text': row['text'],
                'time': row['time']
            }
            
            if row['chart_data']:
                try:
                    message['chart_data'] = json.loads(row['chart_data'])
                except:
                    message['chart_data'] = None
            
            if row['suggestions']:
                try:
                    message['suggestions'] = json.loads(row['suggestions'])
                except:
                    message['suggestions'] = None
                    
            messages.append(message)
        
        return messages

def search_conversations(user_id: int, query: str) -> List[Dict[str, Any]]:
    """Busca conversas por título ou conteúdo das mensagens."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        search_pattern = f'%{query}%'
        
        cursor.execute(
            '''SELECT DISTINCT c.id, c.bot_type, c.title, c.created_at, c.updated_at
               FROM conversations c
               LEFT JOIN messages m ON c.id = m.conversation_id
               WHERE c.user_id = %s AND (
                   c.title ILIKE %s OR m.text ILIKE %s
               )
               ORDER BY c.updated_at DESC''',
            (user_id, search_pattern, search_pattern)
        )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

# ========================================
# ALPHABOT DATA PERSISTENCE (SISTEMA EXCLUSIVO)
# ========================================

def save_alphabot_data(user_id: int, dataframe_json: str, metadata: Dict[str, Any]) -> bool:
    """Salva dados do AlphaBot para um usuário."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            metadata_json = json.dumps(metadata)
            cursor.execute(
                '''UPDATE users SET alphabot_data_json = %s 
                   WHERE id = %s''',
                (json.dumps({'dataframe': dataframe_json, 'metadata': metadata_json}), user_id)
            )
            
            conn.commit()
            return True
        except Exception:
            return False

def load_alphabot_data(user_id: int) -> Optional[Dict[str, Any]]:
    """Carrega dados do AlphaBot para um usuário."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'SELECT alphabot_data_json FROM users WHERE id = %s',
                (user_id,)
            )
            
            row = cursor.fetchone()
            if row and row['alphabot_data_json']:
                data = json.loads(row['alphabot_data_json'])
                return {
                    'dataframe': data.get('dataframe'),
                    'metadata': json.loads(data.get('metadata', '{}'))
                }
            return None
        except Exception:
            return None

def clear_alphabot_data(user_id: int) -> bool:
    """Remove dados do AlphaBot para um usuário."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'UPDATE users SET alphabot_data_json = NULL WHERE id = %s',
                (user_id,)
            )
            conn.commit()
            return True
        except Exception:
            return False

# ========================================
# ALPHABOT SESSIONS E CONVERSATIONS
# ========================================

def create_alphabot_session(user_id: int, session_id: str, dataframe_json: str, metadata: Dict[str, Any], files_info: List[str]) -> bool:
    """Cria uma sessão do AlphaBot."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            metadata_json = json.dumps(metadata)
            files_info_json = json.dumps(files_info)
            
            cursor.execute(
                '''INSERT INTO alphabot_sessions 
                   (id, user_id, dataframe_json, metadata_json, files_info, created_at, updated_at) 
                   VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                   ON CONFLICT (id) DO UPDATE SET
                   dataframe_json = EXCLUDED.dataframe_json,
                   metadata_json = EXCLUDED.metadata_json,
                   files_info = EXCLUDED.files_info,
                   updated_at = CURRENT_TIMESTAMP''',
                (session_id, user_id, dataframe_json, metadata_json, files_info_json)
            )
            
            conn.commit()
            return True
        except Exception:
            return False

def get_alphabot_session(user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
    """Retorna uma sessão do AlphaBot."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT id, user_id, dataframe_json, metadata_json, files_info, created_at, updated_at 
               FROM alphabot_sessions 
               WHERE id = %s AND user_id = %s''',
            (session_id, user_id)
        )
        
        row = cursor.fetchone()
        if row:
            return {
                'session_id': row['id'],
                'user_id': row['user_id'],
                'dataframe_json': row['dataframe_json'],
                'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {},
                'files_info': json.loads(row['files_info']) if row['files_info'] else [],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None

def get_user_alphabot_sessions(user_id: int) -> List[Dict[str, Any]]:
    """Lista todas as sessões do AlphaBot do usuário."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT id, user_id, metadata_json, files_info, created_at, updated_at 
               FROM alphabot_sessions 
               WHERE user_id = %s 
               ORDER BY updated_at DESC''',
            (user_id,)
        )
        
        rows = cursor.fetchall()
        sessions = []
        for row in rows:
            sessions.append({
                'session_id': row['id'],
                'user_id': row['user_id'],
                'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {},
                'files_info': json.loads(row['files_info']) if row['files_info'] else [],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return sessions

def create_alphabot_conversation(conversation_id: str, session_id: str, user_id: int, title: str) -> bool:
    """Cria uma conversa do AlphaBot."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                '''INSERT INTO alphabot_conversations 
                   (id, session_id, user_id, title) 
                   VALUES (%s, %s, %s, %s)''',
                (conversation_id, session_id, user_id, title)
            )
            conn.commit()
            return True
        except Exception:
            return False

def get_alphabot_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Retorna uma conversa do AlphaBot."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT ac.id, ac.session_id, ac.user_id, ac.title, ac.created_at, ac.updated_at,
                      ase.dataframe_json, ase.metadata_json, ase.files_info
               FROM alphabot_conversations ac
               JOIN alphabot_sessions ase ON ac.session_id = ase.id
               WHERE ac.id = %s''',
            (conversation_id,)
        )
        
        row = cursor.fetchone()
        if row:
            return {
                'conversation_id': row['id'],
                'session_id': row['session_id'],
                'user_id': row['user_id'],
                'title': row['title'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'dataframe_json': row['dataframe_json'],
                'metadata': json.loads(row['metadata_json']) if row['metadata_json'] else {},
                'files_info': json.loads(row['files_info']) if row['files_info'] else []
            }
        return None

def add_alphabot_message(conversation_id: str, author: str, text: str, time: int, chart_data: Optional[str] = None, suggestions: Optional[List[str]] = None) -> bool:
    """Adiciona uma mensagem do AlphaBot."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            suggestions_json = json.dumps(suggestions) if suggestions else None
            
            cursor.execute(
                '''INSERT INTO alphabot_messages 
                   (conversation_id, author, text, time, chart_data, suggestions) 
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (conversation_id, author, text, time, chart_data, suggestions_json)
            )
            
            conn.commit()
            return True
        except Exception:
            return False

def get_alphabot_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
    """Retorna mensagens de uma conversa do AlphaBot."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT id, conversation_id, author, text, time, chart_data, suggestions, created_at
               FROM alphabot_messages
               WHERE conversation_id = %s
               ORDER BY time ASC''',
            (conversation_id,)
        )
        
        rows = cursor.fetchall()
        messages = []
        for row in rows:
            message = {
                'id': row['id'],
                'conversation_id': row['conversation_id'],
                'author': row['author'],
                'text': row['text'],
                'time': row['time'],
                'chart_data': row['chart_data'],
                'created_at': row['created_at']
            }
            
            if row['suggestions']:
                try:
                    message['suggestions'] = json.loads(row['suggestions'])
                except:
                    message['suggestions'] = None
                    
            messages.append(message)
        
        return messages

def get_user_alphabot_conversations(user_id: int) -> List[Dict[str, Any]]:
    """Lista conversas do AlphaBot do usuário."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT id, session_id, user_id, title, created_at, updated_at
               FROM alphabot_conversations
               WHERE user_id = %s
               ORDER BY updated_at DESC''',
            (user_id,)
        )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def delete_alphabot_session(user_id: int, session_id: str) -> bool:
    """Delete uma sessão do AlphaBot."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'DELETE FROM alphabot_sessions WHERE id = %s AND user_id = %s',
                (session_id, user_id)
            )
            success = cursor.rowcount > 0
            conn.commit()
            return success
        except Exception:
            return False