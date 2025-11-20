"""
Script de Migração SQLite para PostgreSQL no Render
Autor: ALPHABOT
Data: 2025-11-19

Este script transfere todos os dados de um banco SQLite local para PostgreSQL no Render.
"""

import os
import sqlite3
import sys
import json
from datetime import datetime

# Adicionar o diretório do backend ao path
sys.path.append(os.path.dirname(__file__))

def migrate_sqlite_to_postgresql():
    """
    Migra dados do SQLite local para PostgreSQL no Render
    """
    print("🔄 Iniciando migração SQLite → PostgreSQL...")
    
    # Verificar se existe banco SQLite local
    sqlite_path = os.path.join(os.path.dirname(__file__), 'alphabot.db')
    
    if not os.path.exists(sqlite_path):
        print(f"⚠️ Arquivo SQLite não encontrado em: {sqlite_path}")
        print("💡 Nada para migrar. O PostgreSQL será inicializado vazio.")
        return True
    
    # Verificar se temos credentials do PostgreSQL
    if not (os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')):
        print("❌ Variáveis de ambiente PostgreSQL não encontradas!")
        print("💡 Defina DATABASE_URL ou POSTGRES_URL antes da migração.")
        return False
    
    try:
        # Forçar uso do PostgreSQL para este script
        os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
        
        # Importar módulos após definir environment
        from postgresql_adapter import (
            init_database as init_pg,
            create_user as create_pg_user,
            create_conversation as create_pg_conversation,
            add_message as add_pg_message,
            create_alphabot_session as create_pg_session,
            create_alphabot_conversation as create_pg_alpha_conversation,
            add_alphabot_message as add_pg_alpha_message
        )
        
        # Conectar ao SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        print("✅ Conexões estabelecidas (SQLite + PostgreSQL)")
        
        # 1. Inicializar PostgreSQL
        print("📁 Inicializando estrutura PostgreSQL...")
        init_pg()
        
        # 2. Migrar usuários
        print("👥 Migrando usuários...")
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        user_map = {}  # Mapeamento SQLite ID → PostgreSQL ID
        migrated_users = 0
        
        for user in users:
            # No PostgreSQL adapter, create_user gera novo ID
            # Vamos usar o username + password hash direto
            pg_user = create_pg_user(user['username'], 'migrated_password_hash_' + user['password_hash'][:10])
            if pg_user:
                user_map[user['id']] = pg_user['user_id']
                migrated_users += 1
                print(f"  ✅ {user['username']} → ID {pg_user['user_id']}")
        
        print(f"📊 Usuários migrados: {migrated_users}/{len(users)}")
        
        # 3. Migrar conversas
        print("💬 Migrando conversas...")
        sqlite_cursor.execute("SELECT * FROM conversations")
        conversations = sqlite_cursor.fetchall()
        
        conversation_map = {}
        migrated_conversations = 0
        
        for conv in conversations:
            if conv['user_id'] in user_map:
                pg_user_id = user_map[conv['user_id']]
                pg_conv_id = create_pg_conversation(pg_user_id, conv['bot_type'], conv['title'])
                conversation_map[conv['id']] = pg_conv_id
                migrated_conversations += 1
        
        print(f"📊 Conversas migradas: {migrated_conversations}/{len(conversations)}")
        
        # 4. Migrar mensagens
        print("📝 Migrando mensagens...")
        sqlite_cursor.execute("SELECT * FROM messages")
        messages = sqlite_cursor.fetchall()
        
        migrated_messages = 0
        
        for msg in messages:
            if msg['conversation_id'] in conversation_map:
                pg_conv_id = conversation_map[msg['conversation_id']]
                
                # Parse JSON fields
                chart_data = None
                suggestions = None
                
                if msg['chart_data']:
                    try:
                        chart_data = json.loads(msg['chart_data'])
                    except:
                        pass
                
                if msg['suggestions']:
                    try:
                        suggestions = json.loads(msg['suggestions'])
                    except:
                        pass
                
                add_pg_message(
                    pg_conv_id,
                    msg['author'],
                    msg['text'],
                    msg['time'],
                    chart_data,
                    suggestions
                )
                migrated_messages += 1
        
        print(f"📊 Mensagens migradas: {migrated_messages}/{len(messages)}")
        
        # 5. Migrar sessões AlphaBot (se existirem)
        try:
            sqlite_cursor.execute("SELECT * FROM alphabot_sessions")
            alpha_sessions = sqlite_cursor.fetchall()
            
            print("🤖 Migrando sessões AlphaBot...")
            migrated_alpha_sessions = 0
            
            for session in alpha_sessions:
                if session['user_id'] in user_map:
                    pg_user_id = user_map[session['user_id']]
                    
                    # Parse metadata e files_info
                    metadata = {}
                    files_info = []
                    
                    try:
                        metadata = json.loads(session['metadata_json']) if session['metadata_json'] else {}
                    except:
                        pass
                    
                    try:
                        files_info = json.loads(session['files_info']) if session['files_info'] else []
                    except:
                        pass
                    
                    success = create_pg_session(
                        pg_user_id,
                        session['id'],
                        session['dataframe_json'],
                        metadata,
                        files_info
                    )
                    
                    if success:
                        migrated_alpha_sessions += 1
            
            print(f"📊 Sessões AlphaBot migradas: {migrated_alpha_sessions}/{len(alpha_sessions)}")
            
        except sqlite3.OperationalError:
            print("⚠️ Tabelas AlphaBot não encontradas no SQLite (versão mais antiga)")
        
        # Fechar conexão SQLite
        sqlite_conn.close()
        
        print("✅ Migração concluída com sucesso!")
        print(f"""
📋 RESUMO DA MIGRAÇÃO:
   👥 Usuários: {migrated_users}
   💬 Conversas: {migrated_conversations} 
   📝 Mensagens: {migrated_messages}
   🤖 Sessões AlphaBot: {migrated_alpha_sessions if 'migrated_alpha_sessions' in locals() else 'N/A'}
   
🎯 O banco PostgreSQL no Render está pronto para uso!
        """)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_postgresql_connection():
    """Testa se a conexão PostgreSQL está funcionando"""
    try:
        from postgresql_adapter import get_connection
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        print("✅ Conexão PostgreSQL funcionando!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão PostgreSQL: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Script de Migração AlphaBot - SQLite → PostgreSQL")
    print("=" * 60)
    
    # Verificar argumentos
    import argparse
    parser = argparse.ArgumentParser(description='Migrar dados SQLite para PostgreSQL')
    parser.add_argument('--test', action='store_true', help='Apenas testar conexão PostgreSQL')
    parser.add_argument('--force', action='store_true', help='Forçar migração mesmo sem confirmação')
    args = parser.parse_args()
    
    if args.test:
        test_postgresql_connection()
        sys.exit(0)
    
    # Verificar environment variables
    if not (os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')):
        print("❌ Erro: Variáveis de ambiente PostgreSQL não definidas!")
        print("💡 Configure DATABASE_URL ou POSTGRES_URL no Render antes de executar.")
        print("💡 Exemplo: DATABASE_URL=postgresql://user:pass@host:port/db")
        sys.exit(1)
    
    # Confirmar migração
    if not args.force:
        confirm = input("\n⚠️  Esta migração irá transferir dados do SQLite local para PostgreSQL.\n"
                       "   Tem certeza que deseja continuar? (s/N): ")
        if confirm.lower() not in ['s', 'sim', 'y', 'yes']:
            print("❌ Migração cancelada pelo usuário.")
            sys.exit(0)
    
    # Executar migração
    success = migrate_sqlite_to_postgresql()
    sys.exit(0 if success else 1)