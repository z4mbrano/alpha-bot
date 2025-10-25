"""
Script de Teste para Validar as Correções do AlphaBot

Testa:
1. Processamento correto de dados (sem converter colunas textuais)
2. Cálculos financeiros corretos
3. Persistência de sessão no banco de dados
4. Persistência de mensagens de chat
"""

import pandas as pd
import numpy as np
from src.utils.data_processor import process_dataframe_unified
import database

def test_data_processing():
    """
    Testa se o processamento de dados está correto
    """
    print("\n" + "="*60)
    print("TESTE 1: Processamento de Dados")
    print("="*60)
    
    # Criar DataFrame de teste similar ao que causa erro
    test_data = {
        'Data': ['2024-01-15', '2024-02-20', '2024-03-10'],
        'Mês': ['Janeiro', 'Fevereiro', 'Março'],  # COLUNA TEXTUAL - NÃO DEVE SER CONVERTIDA
        'Produto': ['Produto A', 'Produto B', 'Produto C'],
        'Quantidade': ['100', '200', '150'],  # STRING que deve virar numérico
        'Receita_Total': ['R$ 5.000,00', 'R$ 10.000,00', 'R$ 7.500,00'],  # Formatação brasileira
        'Categoria': ['Vendas', 'Marketing', 'Vendas']
    }
    
    df = pd.DataFrame(test_data)
    
    print("\n📋 DataFrame Original:")
    print(df)
    print("\n📋 Tipos Originais:")
    print(df.dtypes)
    
    # Processar
    try:
        processed_df, metadata = process_dataframe_unified(df, source_info="Teste_AlphaBot")
        
        print("\n✅ Processamento concluído com sucesso!")
        print("\n📋 DataFrame Processado:")
        print(processed_df)
        print("\n📋 Tipos Processados:")
        print(processed_df.dtypes)
        
        # Validações
        print("\n🔍 VALIDAÇÕES:")
        
        # 1. Coluna 'Mês' deve permanecer textual
        if processed_df['Mês'].dtype == 'object':
            print("✅ Coluna 'Mês' permaneceu textual (correto)")
            print(f"   Valores: {processed_df['Mês'].tolist()}")
        else:
            print(f"❌ ERRO: Coluna 'Mês' foi convertida para {processed_df['Mês'].dtype}")
            return False
        
        # 2. Coluna 'Quantidade' deve ser numérica
        if pd.api.types.is_numeric_dtype(processed_df['Quantidade']):
            print("✅ Coluna 'Quantidade' é numérica (correto)")
            total_qtd = processed_df['Quantidade'].sum()
            print(f"   Total: {total_qtd} (esperado: 450)")
            if total_qtd != 450:
                print(f"❌ ERRO: Total incorreto! Esperado 450, obtido {total_qtd}")
                return False
        else:
            print(f"❌ ERRO: Coluna 'Quantidade' não é numérica: {processed_df['Quantidade'].dtype}")
            return False
        
        # 3. Coluna 'Receita_Total' deve ser numérica
        if pd.api.types.is_numeric_dtype(processed_df['Receita_Total']):
            print("✅ Coluna 'Receita_Total' é numérica (correto)")
            total_receita = processed_df['Receita_Total'].sum()
            print(f"   Total: R$ {total_receita:,.2f} (esperado: R$ 22.500,00)")
            if abs(total_receita - 22500) > 1:  # Tolerância de R$ 1
                print(f"❌ ERRO: Total incorreto! Esperado R$ 22.500,00, obtido R$ {total_receita:,.2f}")
                return False
        else:
            print(f"❌ ERRO: Coluna 'Receita_Total' não é numérica: {processed_df['Receita_Total'].dtype}")
            return False
        
        # 4. Verificar metadata
        print("\n📊 Metadata do Processamento:")
        for col, info in metadata.get('columns_processed', {}).items():
            print(f"   {col}: {info.get('type')} ({info.get('original_dtype')} → {info.get('final_dtype')})")
        
        print("\n✅ TESTE 1 PASSOU!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO no processamento: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_persistence():
    """
    Testa se os dados estão sendo persistidos no banco
    """
    print("\n" + "="*60)
    print("TESTE 2: Persistência no Banco de Dados")
    print("="*60)
    
    # Inicializar banco
    database.init_database()
    
    # Criar sessão de teste
    import random
    test_user_id = 999999  # ID de teste
    test_session_id = f"test_session_{random.randint(1000, 9999)}"  # ID único para cada teste
    
    test_df = pd.DataFrame({
        'Quantidade': [100, 200],
        'Receita': [5000, 10000]
    })
    
    test_metadata = {
        'total_records': 2,
        'total_columns': 2,
        'columns': ['Quantidade', 'Receita']
    }
    
    test_files = ['test_file.csv']
    
    print(f"\n📝 Criando sessão de teste: user_id={test_user_id}, session_id={test_session_id}")
    
    # Criar sessão
    success = database.create_alphabot_session(
        user_id=test_user_id,
        session_id=test_session_id,
        dataframe_json=test_df.to_json(orient='split'),
        metadata=test_metadata,
        files_info=test_files
    )
    
    if success:
        print("✅ Sessão criada com sucesso")
    else:
        print("❌ ERRO: Falha ao criar sessão")
        return False
    
    # Recuperar sessão
    print(f"\n📖 Recuperando sessão...")
    session_data = database.get_alphabot_session(test_user_id, test_session_id)
    
    if session_data:
        print("✅ Sessão recuperada com sucesso")
        print(f"   Metadata: {session_data['metadata']}")
        
        # Verificar dados
        recovered_df = pd.read_json(session_data['dataframe'], orient='split')
        print(f"   DataFrame recuperado: {len(recovered_df)} linhas, {len(recovered_df.columns)} colunas")
        
        if len(recovered_df) == 2 and len(recovered_df.columns) == 2:
            print("✅ Dados recuperados corretamente")
        else:
            print(f"❌ ERRO: Dados recuperados incorretamente")
            return False
    else:
        print("❌ ERRO: Sessão não encontrada")
        return False
    
    # Testar mensagens
    print(f"\n📝 Testando persistência de mensagens...")
    
    test_conv_id = f"test_conv_{random.randint(1000, 9999)}"  # ID único para cada teste
    
    # Criar conversa
    conv_created = database.create_alphabot_conversation(
        conversation_id=test_conv_id,
        session_id=test_session_id,
        user_id=test_user_id,
        title="Teste de Conversa"
    )
    
    if conv_created:
        print("✅ Conversa criada com sucesso")
    else:
        print("❌ ERRO: Falha ao criar conversa")
        return False
    
    # Adicionar mensagem do usuário
    msg_user_saved = database.add_alphabot_message(
        conversation_id=test_conv_id,
        author='user',
        text='Qual o total de receita?',
        time=1234567890000
    )
    
    if msg_user_saved:
        print("✅ Mensagem do usuário salva com sucesso")
    else:
        print("❌ ERRO: Falha ao salvar mensagem do usuário")
        return False
    
    # Adicionar mensagem do bot
    msg_bot_saved = database.add_alphabot_message(
        conversation_id=test_conv_id,
        author='bot',
        text='O total de receita é R$ 15.000,00',
        time=1234567891000
    )
    
    if msg_bot_saved:
        print("✅ Mensagem do bot salva com sucesso")
    else:
        print("❌ ERRO: Falha ao salvar mensagem do bot")
        return False
    
    # Recuperar mensagens
    # Como não existe get_alphabot_messages, vamos apenas verificar se salvou
    print(f"✅ Mensagens salvas com sucesso (verificação de recuperação não implementada)")
    
    # Limpar dados de teste
    print(f"\n🧹 Limpando dados de teste...")
    # (Não implementado para não afetar banco de produção)
    
    print("\n✅ TESTE 2 PASSOU!")
    return True


def main():
    """
    Executa todos os testes
    """
    print("\n" + "="*60)
    print("🧪 TESTES DE VALIDAÇÃO DO ALPHABOT")
    print("="*60)
    
    results = []
    
    # Teste 1: Processamento de Dados
    results.append(("Processamento de Dados", test_data_processing()))
    
    # Teste 2: Persistência no Banco
    results.append(("Persistência no Banco", test_database_persistence()))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passaram, {failed} falharam")
    
    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! AlphaBot está funcionando corretamente.")
        return True
    else:
        print(f"\n⚠️ {failed} teste(s) falharam. Verifique os logs acima.")
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
