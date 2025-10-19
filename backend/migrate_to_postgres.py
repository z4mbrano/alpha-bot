"""
Script de Migração de SQLite para PostgreSQL
============================================

Use este script para migrar dados existentes do SQLite local
para PostgreSQL em produção (Supabase/Railway/Vercel).

ATENÇÃO: Execute APENAS se você já tem dados no SQLite local
que deseja migrar para produção.
"""

import os
import sqlite3
import sys

# Verificar se psycopg2 está instalado
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ ERRO: psycopg2 não está instalado!")
    print("Execute: pip install psycopg2-binary")
    sys.exit(1)

# Configuração
SQLITE_DB = 'alphabot.db'  # Seu database SQLite local
POSTGRES_URL = os.environ.get('DATABASE_URL')  # Connection string do PostgreSQL

if not POSTGRES_URL:
    print("❌ ERRO: DATABASE_URL não configurada!")
    print("Configure a variável de ambiente DATABASE_URL com a connection string do PostgreSQL")
    print("Exemplo: export DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
    sys.exit(1)

if not os.path.exists(SQLITE_DB):
    print(f"❌ ERRO: Arquivo {SQLITE_DB} não encontrado!")
    sys.exit(1)

print("🚀 Iniciando migração de SQLite para PostgreSQL...")
print(f"📂 SQLite: {SQLITE_DB}")
print(f"🗄️  PostgreSQL: {POSTGRES_URL[:30]}...")

# Conectar aos databases
sqlite_conn = sqlite3.connect(SQLITE_DB)
sqlite_conn.row_factory = sqlite3.Row
postgres_conn = psycopg2.connect(POSTGRES_URL)

print("\n✅ Conexões estabelecidas!")

try:
    # Criar tabelas no PostgreSQL (se ainda não existem)
    print("\n📋 Criando tabelas no PostgreSQL...")
    with postgres_conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                bot_type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER NOT NULL,
                author VARCHAR(50) NOT NULL,
                text TEXT NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chart_data TEXT,
                suggestions TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
            ON conversations(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
            ON messages(conversation_id)
        """)
        
        postgres_conn.commit()
        print("✅ Tabelas criadas/verificadas!")
    
    # Migrar usuários
    print("\n👥 Migrando usuários...")
    sqlite_cursor = sqlite_conn.execute("SELECT * FROM users")
    users = sqlite_cursor.fetchall()
    
    user_id_map = {}  # Mapear IDs antigos para novos
    
    with postgres_conn.cursor() as cursor:
        for user in users:
            cursor.execute("""
                INSERT INTO users (username, password_hash, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO NOTHING
                RETURNING id
            """, (user['username'], user['password_hash'], user['created_at']))
            
            result = cursor.fetchone()
            if result:
                user_id_map[user['id']] = result[0]
            else:
                # Usuário já existe, buscar ID
                cursor.execute("SELECT id FROM users WHERE username = %s", (user['username'],))
                user_id_map[user['id']] = cursor.fetchone()[0]
    
    postgres_conn.commit()
    print(f"✅ {len(users)} usuários migrados!")
    
    # Migrar conversas
    print("\n💬 Migrando conversas...")
    sqlite_cursor = sqlite_conn.execute("SELECT * FROM conversations")
    conversations = sqlite_cursor.fetchall()
    
    conversation_id_map = {}
    
    with postgres_conn.cursor() as cursor:
        for conv in conversations:
            new_user_id = user_id_map.get(conv['user_id'])
            if not new_user_id:
                print(f"⚠️  Pulando conversa {conv['id']} - usuário não encontrado")
                continue
            
            cursor.execute("""
                INSERT INTO conversations (user_id, bot_type, title, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (new_user_id, conv['bot_type'], conv['title'], 
                  conv['created_at'], conv['updated_at']))
            
            new_id = cursor.fetchone()[0]
            conversation_id_map[conv['id']] = new_id
    
    postgres_conn.commit()
    print(f"✅ {len(conversations)} conversas migradas!")
    
    # Migrar mensagens
    print("\n📨 Migrando mensagens...")
    sqlite_cursor = sqlite_conn.execute("SELECT * FROM messages")
    messages = sqlite_cursor.fetchall()
    
    message_count = 0
    with postgres_conn.cursor() as cursor:
        for msg in messages:
            new_conv_id = conversation_id_map.get(msg['conversation_id'])
            if not new_conv_id:
                continue
            
            cursor.execute("""
                INSERT INTO messages 
                (conversation_id, author, text, time, chart_data, suggestions)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (new_conv_id, msg['author'], msg['text'], 
                  msg['time'], msg.get('chart_data'), msg.get('suggestions')))
            
            message_count += 1
    
    postgres_conn.commit()
    print(f"✅ {message_count} mensagens migradas!")
    
    print("\n" + "="*60)
    print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*60)
    print(f"\n📊 Resumo:")
    print(f"  • Usuários: {len(users)}")
    print(f"  • Conversas: {len(conversations)}")
    print(f"  • Mensagens: {message_count}")
    print("\n✅ Seus dados foram migrados para PostgreSQL!")
    print("🚀 Agora você pode fazer deploy no Vercel com segurança.")
    
except Exception as e:
    print(f"\n❌ ERRO durante migração: {e}")
    postgres_conn.rollback()
    import traceback
    traceback.print_exc()
    sys.exit(1)

finally:
    sqlite_conn.close()
    postgres_conn.close()
    print("\n🔌 Conexões fechadas.")
