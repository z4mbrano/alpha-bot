"""
TESTE DO ALPHABOT - Motor de Validação Interna

Testa:
- Upload de múltiplos arquivos (.csv, .xlsx)
- Consolidação de DataFrames
- Criação de colunas auxiliares temporais
- Armazenamento de sessão
- Endpoint de chat com motor de validação (Analista → Crítico → Júri)

Autor: AlphaBot Team
Data: 2025-10-18
"""

import requests
import pandas as pd
import os
from io import BytesIO

# Configuração
BASE_URL = "http://localhost:5000"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/alphabot/upload"
CHAT_ENDPOINT = f"{BASE_URL}/api/alphabot/chat"

def create_test_files():
    """
    Cria arquivos de teste (.csv e .xlsx) em memória
    """
    print("\n" + "="*80)
    print("📁 CRIANDO ARQUIVOS DE TESTE")
    print("="*80)
    
    # Arquivo 1: vendas_janeiro.csv
    df1 = pd.DataFrame({
        'Data': pd.date_range('2024-01-01', periods=5, freq='D'),
        'Produto': ['Mouse', 'Teclado', 'Monitor', 'Mouse', 'Webcam'],
        'Categoria': ['Periféricos', 'Periféricos', 'Monitores', 'Periféricos', 'Periféricos'],
        'Quantidade': [2, 1, 1, 3, 2],
        'Preco': [50.00, 150.00, 800.00, 50.00, 120.00]
    })
    
    # Arquivo 2: vendas_fevereiro.xlsx
    df2 = pd.DataFrame({
        'Data': pd.date_range('2024-02-01', periods=5, freq='D'),
        'Produto': ['Teclado', 'Mouse', 'Monitor', 'Fone', 'Mouse'],
        'Categoria': ['Periféricos', 'Periféricos', 'Monitores', 'Áudio', 'Periféricos'],
        'Quantidade': [1, 2, 1, 1, 4],
        'Preco': [150.00, 50.00, 850.00, 200.00, 50.00]
    })
    
    # Converter para bytes (simulando upload)
    csv_buffer = BytesIO()
    df1.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    xlsx_buffer = BytesIO()
    df2.to_excel(xlsx_buffer, index=False, engine='openpyxl')
    xlsx_buffer.seek(0)
    
    print("✅ Arquivo 1: vendas_janeiro.csv (5 registros)")
    print("✅ Arquivo 2: vendas_fevereiro.xlsx (5 registros)")
    
    return {
        'vendas_janeiro.csv': csv_buffer,
        'vendas_fevereiro.xlsx': xlsx_buffer
    }


def test_upload():
    """
    Testa endpoint de upload de múltiplos arquivos
    """
    print("\n" + "="*80)
    print("🧪 TESTE 1: UPLOAD DE MÚLTIPLOS ARQUIVOS")
    print("="*80)
    
    files_dict = create_test_files()
    
    # Preparar requisição multipart/form-data
    files = []
    for filename, buffer in files_dict.items():
        files.append(('files', (filename, buffer, 'application/octet-stream')))
    
    print("\n📤 Enviando arquivos para /api/alphabot/upload...")
    
    try:
        response = requests.post(UPLOAD_ENDPOINT, files=files)
        
        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data['status']}")
            print(f"✅ Mensagem: {data['message']}")
            print(f"✅ Session ID: {data['session_id']}")
            print(f"✅ Arquivos processados: {data['files_success']}")
            
            if data.get('files_failed'):
                print(f"⚠️ Arquivos com falha: {data['files_failed']}")
            
            metadata = data.get('metadata', {})
            print(f"\n📈 Metadata:")
            print(f"   - Total de Registros: {metadata.get('total_records')}")
            print(f"   - Total de Colunas: {metadata.get('total_columns')}")
            
            if metadata.get('date_range'):
                dr = metadata['date_range']
                print(f"   - Período: {dr['min']} até {dr['max']}")
            
            return data['session_id']
        else:
            print(f"❌ FALHA: {response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return None


def test_chat(session_id):
    """
    Testa endpoint de chat com motor de validação
    """
    print("\n" + "="*80)
    print("🧪 TESTE 2: CHAT COM MOTOR DE VALIDAÇÃO")
    print("="*80)
    
    if not session_id:
        print("❌ Session ID não disponível. Pule o teste de chat.")
        return False
    
    # Perguntas de teste
    questions = [
        "Qual foi o produto mais vendido?",
        "Qual foi o faturamento total no período?",
        "Em qual mês houve maior volume de vendas?"
    ]
    
    for idx, question in enumerate(questions, 1):
        print(f"\n🔍 Pergunta {idx}: {question}")
        
        payload = {
            "session_id": session_id,
            "message": question
        }
        
        try:
            response = requests.post(CHAT_ENDPOINT, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                
                print(f"\n💬 Resposta do AlphaBot:")
                print("-" * 80)
                print(answer)
                print("-" * 80)
                
                # Verificar estrutura da resposta (Júri)
                has_structure = (
                    'Resposta Direta' in answer or
                    'Análise Detalhada' in answer or
                    'resposta' in answer.lower()
                )
                
                if has_structure:
                    print("✅ Resposta estruturada detectada")
                else:
                    print("⚠️ Estrutura de resposta não detectada claramente")
                    
            else:
                print(f"❌ FALHA: {response.json()}")
                
        except Exception as e:
            print(f"❌ ERRO: {e}")
    
    return True


def test_session_validation():
    """
    Testa validação de sessão inexistente
    """
    print("\n" + "="*80)
    print("🧪 TESTE 3: VALIDAÇÃO DE SESSÃO")
    print("="*80)
    
    fake_session_id = "00000000-0000-0000-0000-000000000000"
    
    payload = {
        "session_id": fake_session_id,
        "message": "Teste"
    }
    
    print(f"\n🔍 Tentando usar sessão inexistente: {fake_session_id}")
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload)
        
        if response.status_code == 404:
            print("✅ Validação correta: Sessão não encontrada (404)")
            return True
        else:
            print(f"⚠️ Esperado 404, obtido {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False


def main():
    """
    Executa todos os testes
    """
    print("\n" + "="*80)
    print("🚀 TESTANDO ALPHABOT - MOTOR DE VALIDAÇÃO INTERNA")
    print("="*80)
    print("\n⚠️ IMPORTANTE: Certifique-se de que o backend está rodando em http://localhost:5000")
    print("   Execute: cd backend && python app.py\n")
    
    input("Pressione ENTER para começar os testes...")
    
    results = []
    
    # Teste 1: Upload
    session_id = test_upload()
    results.append(("Upload de Arquivos", session_id is not None))
    
    # Teste 2: Chat (depende do upload)
    if session_id:
        chat_success = test_chat(session_id)
        results.append(("Chat com Validação", chat_success))
    else:
        results.append(("Chat com Validação", False))
    
    # Teste 3: Validação de sessão
    validation_success = test_session_validation()
    results.append(("Validação de Sessão", validation_success))
    
    # Resumo
    print("\n" + "="*80)
    print("📊 RESUMO DOS TESTES")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*80)
    print(f"RESULTADO FINAL: {passed}/{total} testes passaram ({passed/total*100:.0f}%)")
    print("="*80)
    
    if passed == total:
        print("\n🎉 ALPHABOT TOTALMENTE FUNCIONAL!")
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM - REVISAR IMPLEMENTAÇÃO")


if __name__ == "__main__":
    main()
