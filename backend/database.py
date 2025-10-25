"""
Sistema de banco de dados SQLite para multi-usuário com histórico de conversas.
Autor: ALPHABOT
Data: 2025-10-19
"""

import os
import sqlite3
import hashlib
import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any
import json

# Detectar ambiente e usar caminho apropriado
if os.environ.get('RAILWAY_ENVIRONMENT'):
    # Railway: usar diretório de dados (persistente com volume)
    data_dir = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH', '/data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    DATABASE_PATH = os.path.join(data_dir, 'alphabot.db')
    print(f"🚂 Railway: Usando database em {DATABASE_PATH}")
elif os.environ.get('VERCEL'):
    # Vercel: usar /tmp (efêmero - apenas para testes)
    DATABASE_PATH = '/tmp/alphabot.db'
    print("⚠️ Vercel: Usando database efêmero em /tmp")
else:
    # Local: usar diretório do backend
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'alphabot.db')
    print(f"🔧 Local: Usando database em {DATABASE_PATH}")


def get_connection():
    """Cria conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn


def init_database():
    """Inicializa o banco de dados criando as tabelas necessárias."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            alphabot_data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de conversas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            bot_type TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela de mensagens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            author TEXT NOT NULL,
            text TEXT NOT NULL,
            time INTEGER NOT NULL,
            chart_data TEXT,
            suggestions TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabelas exclusivas do AlphaBot (persistência completa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alphabot_sessions (
            id TEXT PRIMARY KEY,
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
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES alphabot_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alphabot_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            author TEXT NOT NULL CHECK (author IN ('user', 'bot')),
            text TEXT NOT NULL,
            time INTEGER NOT NULL,
            chart_data TEXT,
            suggestions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES alphabot_conversations(id) ON DELETE CASCADE
        )
    ''')

    # Índices para otimizar buscas (sistema original)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)')
    
    # Índices para tabelas AlphaBot
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_sessions_user_id ON alphabot_sessions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_conversations_session_id ON alphabot_conversations(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_conversations_user_id ON alphabot_conversations(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_messages_conversation_id ON alphabot_messages(conversation_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_alphabot_messages_time ON alphabot_messages(time)')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso (incluindo tabelas AlphaBot exclusivas)!")


# ========================================
# FUNÇÕES DE AUTENTICAÇÃO
# ========================================

def hash_password(password: str) -> str:
    """Gera hash SHA-256 da senha."""
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Cria um novo usuário.
    Retorna: dict com user_id e username, ou None se username já existe.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(password)
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        
        return {
            'id': user_id,
            'username': username,
            'created_at': datetime.now().isoformat()
        }
    except sqlite3.IntegrityError:
        # Username já existe
        return None
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Autentica usuário verificando senha.
    Retorna: dict com dados do usuário, ou None se credenciais inválidas.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    password_hash = hash_password(password)
    cursor.execute(
        'SELECT id, username, created_at FROM users WHERE username = ? AND password_hash = ?',
        (username, password_hash)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row['id'],
            'username': row['username'],
            'created_at': row['created_at']
        }
    return None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retorna dados do usuário pelo ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT id, username, created_at FROM users WHERE id = ?',
        (user_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            'id': row['id'],
            'username': row['username'],
            'created_at': row['created_at']
        }
    return None


# ========================================
# FUNÇÕES DE CONVERSAS
# ========================================

def create_conversation(user_id: int, bot_type: str, title: str = "Nova Conversa") -> str:
    """
    Cria uma nova conversa.
    Retorna: conversation_id (UUID)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    conversation_id = secrets.token_urlsafe(16)
    cursor.execute(
        '''INSERT INTO conversations (id, user_id, bot_type, title) 
           VALUES (?, ?, ?, ?)''',
        (conversation_id, user_id, bot_type, title)
    )
    
    conn.commit()
    conn.close()
    
    return conversation_id


def get_user_conversations(user_id: int, bot_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lista todas as conversas do usuário.
    Pode filtrar por bot_type (alphabot/drivebot).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if bot_type:
        cursor.execute(
            '''SELECT id, bot_type, title, created_at, updated_at 
               FROM conversations 
               WHERE user_id = ? AND bot_type = ?
               ORDER BY updated_at DESC''',
            (user_id, bot_type)
        )
    else:
        cursor.execute(
            '''SELECT id, bot_type, title, created_at, updated_at 
               FROM conversations 
               WHERE user_id = ?
               ORDER BY updated_at DESC''',
            (user_id,)
        )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_conversation(conversation_id: str, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retorna dados de uma conversa específica.
    Valida que a conversa pertence ao usuário.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''SELECT id, user_id, bot_type, title, created_at, updated_at 
           FROM conversations 
           WHERE id = ? AND user_id = ?''',
        (conversation_id, user_id)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_conversation_title(conversation_id: str, user_id: int, title: str) -> bool:
    """Atualiza o título de uma conversa."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''UPDATE conversations 
           SET title = ?, updated_at = CURRENT_TIMESTAMP 
           WHERE id = ? AND user_id = ?''',
        (title, conversation_id, user_id)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success


def delete_conversation(conversation_id: str, user_id: int) -> bool:
    """
    Delete uma conversa e todas as mensagens associadas.
    Retorna True se deletado com sucesso.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # SQLite deleta mensagens automaticamente (CASCADE)
    cursor.execute(
        'DELETE FROM conversations WHERE id = ? AND user_id = ?',
        (conversation_id, user_id)
    )
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success


def touch_conversation(conversation_id: str):
    """Atualiza o timestamp updated_at de uma conversa."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?',
        (conversation_id,)
    )
    
    conn.commit()
    conn.close()


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
    """
    Adiciona uma mensagem à conversa.
    Retorna: message_id
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    chart_json = json.dumps(chart_data) if chart_data else None
    suggestions_json = json.dumps(suggestions) if suggestions else None
    
    cursor.execute(
        '''INSERT INTO messages (conversation_id, author, text, time, chart_data, suggestions)
           VALUES (?, ?, ?, ?, ?, ?)''',
        (conversation_id, author, text, time, chart_json, suggestions_json)
    )
    
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Atualizar timestamp da conversa
    touch_conversation(conversation_id)
    
    return message_id


def get_conversation_messages(conversation_id: str, user_id: int) -> List[Dict[str, Any]]:
    """
    Retorna todas as mensagens de uma conversa.
    Valida que a conversa pertence ao usuário.
    """
    # Primeiro verificar se conversa existe e pertence ao usuário
    conversation = get_conversation(conversation_id, user_id)
    if not conversation:
        return []
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''SELECT id, author, text, time, chart_data, suggestions
           FROM messages
           WHERE conversation_id = ?
           ORDER BY time ASC''',
        (conversation_id,)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        message = {
            'id': f"msg-{row['id']}",
            'author': row['author'],
            'text': row['text'],
            'time': row['time']
        }
        
        if row['chart_data']:
            message['chart'] = json.loads(row['chart_data'])
        
        if row['suggestions']:
            message['suggestions'] = json.loads(row['suggestions'])
        
        messages.append(message)
    
    return messages


def search_conversations(user_id: int, query: str) -> List[Dict[str, Any]]:
    """
    Busca conversas por título ou conteúdo das mensagens.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    search_pattern = f'%{query}%'
    
    cursor.execute(
        '''SELECT DISTINCT c.id, c.bot_type, c.title, c.created_at, c.updated_at
           FROM conversations c
           LEFT JOIN messages m ON c.id = m.conversation_id
           WHERE c.user_id = ? AND (
               c.title LIKE ? OR m.text LIKE ?
           )
           ORDER BY c.updated_at DESC''',
        (user_id, search_pattern, search_pattern)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


# ========================================
# ALPHABOT DATA PERSISTENCE (SISTEMA EXCLUSIVO)
# ========================================

def save_alphabot_data(user_id: int, dataframe_json: str, metadata: Dict[str, Any]) -> bool:
    """
    Salva dados do AlphaBot (DataFrame + metadata) para um usuário.
    Retorna: True se salvou com sucesso, False caso contrário.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Criar estrutura de dados completa
        alphabot_data = {
            'dataframe': dataframe_json,
            'metadata': metadata,
            'updated_at': datetime.now().isoformat()
        }
        
        cursor.execute(
            'UPDATE users SET alphabot_data_json = ? WHERE id = ?',
            (json.dumps(alphabot_data), user_id)
        )
        conn.commit()
        
        # Verificar se atualizou alguma linha
        if cursor.rowcount > 0:
            print(f"✅ Dados do AlphaBot salvos para usuário {user_id}")
            return True
        else:
            print(f"⚠️ Usuário {user_id} não encontrado para salvar dados")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao salvar dados do AlphaBot: {e}")
        return False
    finally:
        conn.close()


def load_alphabot_data(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Carrega dados do AlphaBot para um usuário.
    Retorna: dict com 'dataframe' (JSON) e 'metadata', ou None se não houver dados.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'SELECT alphabot_data_json FROM users WHERE id = ?',
            (user_id,)
        )
        
        row = cursor.fetchone()
        if row and row['alphabot_data_json']:
            alphabot_data = json.loads(row['alphabot_data_json'])
            print(f"✅ Dados do AlphaBot carregados para usuário {user_id}")
            return alphabot_data
        else:
            print(f"ℹ️ Nenhum dado do AlphaBot encontrado para usuário {user_id}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao carregar dados do AlphaBot: {e}")
        return None
    finally:
        conn.close()


def clear_alphabot_data(user_id: int) -> bool:
    """
    Remove dados do AlphaBot para um usuário.
    Retorna: True se removeu com sucesso, False caso contrário.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'UPDATE users SET alphabot_data_json = NULL WHERE id = ?',
            (user_id,)
        )
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ Dados do AlphaBot removidos para usuário {user_id}")
            return True
        else:
            print(f"⚠️ Usuário {user_id} não encontrado para remover dados")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao remover dados do AlphaBot: {e}")
        return False
    finally:
        conn.close()


# ========================================
# ALPHABOT SESSIONS E CONVERSATIONS (SISTEMA EXCLUSIVO)
# ========================================

def create_alphabot_session(user_id: int, session_id: str, dataframe_json: str, metadata: Dict[str, Any], files_info: List[str]) -> bool:
    """
    Cria uma nova sessão do AlphaBot com dados persistentes.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO alphabot_sessions (id, user_id, dataframe_json, metadata_json, files_info, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            user_id,
            dataframe_json,
            json.dumps(metadata),
            json.dumps(files_info),
            datetime.now().isoformat()
        ))
        conn.commit()
        print(f"✅ Sessão AlphaBot criada: {session_id} para usuário {user_id}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar sessão AlphaBot: {e}")
        return False
    finally:
        conn.close()


def get_alphabot_session(user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Recupera dados de uma sessão específica do AlphaBot.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT dataframe_json, metadata_json, files_info, created_at, updated_at
            FROM alphabot_sessions 
            WHERE id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        row = cursor.fetchone()
        if row:
            return {
                'dataframe': row['dataframe_json'],
                'metadata': json.loads(row['metadata_json']),
                'files_info': json.loads(row['files_info']),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
        
    except Exception as e:
        print(f"❌ Erro ao recuperar sessão AlphaBot: {e}")
        return None
    finally:
        conn.close()


def get_user_alphabot_sessions(user_id: int) -> List[Dict[str, Any]]:
    """
    Lista todas as sessões do AlphaBot de um usuário.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, metadata_json, files_info, created_at, updated_at
            FROM alphabot_sessions 
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        sessions = []
        for row in rows:
            metadata = json.loads(row['metadata_json'])
            sessions.append({
                'session_id': row['id'],
                'files_info': json.loads(row['files_info']),
                'total_records': metadata.get('total_records', 0),
                'total_columns': metadata.get('total_columns', 0),
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        return sessions
        
    except Exception as e:
        print(f"❌ Erro ao listar sessões AlphaBot: {e}")
        return []
    finally:
        conn.close()


def create_alphabot_conversation(conversation_id: str, session_id: str, user_id: int, title: str) -> bool:
    """
    Cria uma nova conversa do AlphaBot associada a uma sessão.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO alphabot_conversations (id, session_id, user_id, title, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (conversation_id, session_id, user_id, title, datetime.now().isoformat()))
        conn.commit()
        print(f"✅ Conversa AlphaBot criada: {conversation_id}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar conversa AlphaBot: {e}")
        return False
    finally:
        conn.close()


def get_alphabot_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Busca uma conversa específica do AlphaBot por ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, session_id, user_id, title, created_at, updated_at
            FROM alphabot_conversations
            WHERE id = ?
        ''', (conversation_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0],
                "session_id": row[1],
                "user_id": row[2],
                "title": row[3],
                "created_at": row[4],
                "updated_at": row[5]
            }
        return None
        
    except Exception as e:
        print(f"❌ Erro ao buscar conversa AlphaBot: {e}")
        return None
    finally:
        conn.close()


def find_or_create_alphabot_conversation_for_session(user_id: int, session_id: str, title: Optional[str] = None) -> Optional[str]:
    """
    Retorna o ID de uma conversa existente para a sessão do AlphaBot (user_id + session_id)
    ou cria uma nova se não existir.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT id FROM alphabot_conversations
            WHERE user_id = ? AND session_id = ?
            ORDER BY updated_at DESC LIMIT 1
        ''', (user_id, session_id))
        row = cursor.fetchone()
        if row:
            return row['id']

        # Criar nova conversa
        from datetime import datetime as _dt
        import secrets as _secrets
        conversation_id = _secrets.token_urlsafe(16)
        conv_title = title or f"Chat AlphaBot - {_dt.now().strftime('%d/%m/%Y %H:%M')}"
        cursor.execute('''
            INSERT INTO alphabot_conversations (id, session_id, user_id, title, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (conversation_id, session_id, user_id, conv_title, _dt.now().isoformat()))
        conn.commit()
        return conversation_id

    except Exception as e:
        print(f"❌ Erro em find_or_create_alphabot_conversation_for_session: {e}")
        return None
    finally:
        conn.close()


def add_alphabot_message(conversation_id: str, author: str, text: str, time: int, chart_data: Optional[str] = None, suggestions: Optional[List[str]] = None) -> bool:
    """
    Adiciona uma mensagem à conversa do AlphaBot.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO alphabot_messages (conversation_id, author, text, time, chart_data, suggestions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            conversation_id,
            author,
            text,
            time,
            chart_data,
            json.dumps(suggestions) if suggestions else None
        ))
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar mensagem AlphaBot: {e}")
        return False
    finally:
        conn.close()


def get_alphabot_conversation_messages(conversation_id: str) -> List[Dict[str, Any]]:
    """
    Recupera todas as mensagens de uma conversa do AlphaBot.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT author, text, time, chart_data, suggestions
            FROM alphabot_messages 
            WHERE conversation_id = ?
            ORDER BY time ASC
        ''', (conversation_id,))
        
        rows = cursor.fetchall()
        messages = []
        for row in rows:
            message = {
                'author': row['author'],
                'text': row['text'],
                'time': row['time'],
                'chart_data': row['chart_data'],
                'suggestions': json.loads(row['suggestions']) if row['suggestions'] else None
            }
            messages.append(message)
        return messages
        
    except Exception as e:
        print(f"❌ Erro ao recuperar mensagens AlphaBot: {e}")
        return []
    finally:
        conn.close()


def get_user_alphabot_conversations(user_id: int) -> List[Dict[str, Any]]:
    """
    Lista todas as conversas do AlphaBot de um usuário.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT ac.id, ac.session_id, ac.title, ac.created_at, ac.updated_at,
                   COUNT(am.id) as message_count
            FROM alphabot_conversations ac
            LEFT JOIN alphabot_messages am ON ac.id = am.conversation_id
            WHERE ac.user_id = ?
            GROUP BY ac.id, ac.session_id, ac.title, ac.created_at, ac.updated_at
            ORDER BY ac.updated_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conversations = []
        for row in rows:
            conversations.append({
                'conversation_id': row['id'],
                'session_id': row['session_id'],
                'title': row['title'],
                'message_count': row['message_count'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        return conversations
        
    except Exception as e:
        print(f"❌ Erro ao listar conversas AlphaBot: {e}")
        return []
    finally:
        conn.close()


def delete_alphabot_session(user_id: int, session_id: str) -> bool:
    """
    Remove uma sessão do AlphaBot e todas as conversas/mensagens associadas.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM alphabot_sessions 
            WHERE id = ? AND user_id = ?
        ''', (session_id, user_id))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ Sessão AlphaBot removida: {session_id}")
            return True
        else:
            print(f"⚠️ Sessão não encontrada: {session_id}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao remover sessão AlphaBot: {e}")
        return False
    finally:
        conn.close()


# ========================================
# INICIALIZAÇÃO
# ========================================

if __name__ == '__main__':
    print("🔧 Inicializando banco de dados...")
    init_database()
    
    # Criar usuário de teste
    test_user = create_user('admin', 'admin123')
    if test_user:
        print(f"✅ Usuário de teste criado: {test_user['username']}")
    else:
        print("⚠️ Usuário 'admin' já existe")
