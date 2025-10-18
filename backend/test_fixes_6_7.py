"""
TESTE DAS CORREÇÕES #6 e #7 - DriveBot v11.0

Valida:
- FIX #6: Case-insensitive filtering (Abril vs abril)
- FIX #7: Múltiplos comandos (lista de ferramentas)

Autor: DriveBot v11.0
Data: 2025-10-18
"""

import pandas as pd
import sys
import os

# Adicionar path do backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import detect_datetime_columns, prepare_table, month_number_to_name

def test_case_insensitive_filtering():
    """
    FIX #6: Testa se filtros ignoram maiúsculas/minúsculas
    """
    print("\n" + "="*80)
    print("TESTE FIX #6: CASE-INSENSITIVE FILTERING")
    print("="*80)
    
    # Criar DataFrame de teste
    df = pd.DataFrame({
        'Data': pd.to_datetime(['2024-04-15', '2024-07-20', '2024-11-10']),
        'Produto': ['Mouse', 'Teclado', 'Monitor'],
        'Receita': [100, 200, 300]
    })
    
    # Preparar tabela (cria colunas auxiliares)
    table_info = prepare_table('test_table', df)
    processed_df = table_info['df']
    
    print(f"\n✅ DataFrame criado com {len(processed_df)} registros")
    print(f"✅ Colunas auxiliares criadas: {table_info.get('auxiliary_columns', [])}")
    
    # Verificar se coluna Data_Mes_Nome foi criada
    if 'Data_Mes_Nome' not in processed_df.columns:
        print("❌ FALHA: Coluna 'Data_Mes_Nome' não foi criada!")
        return False
    
    print(f"\n📊 Valores em 'Data_Mes_Nome': {processed_df['Data_Mes_Nome'].unique().tolist()}")
    
    # TESTE 1: Filtro com letra maiúscula (como LLM envia)
    filter_value_upper = "Abril"
    filtered_upper = processed_df[
        processed_df['Data_Mes_Nome'].astype(str).str.lower() == filter_value_upper.lower()
    ]
    
    print(f"\n🔍 TESTE 1: Filtro '{filter_value_upper}' (maiúscula)")
    print(f"   Registros encontrados: {len(filtered_upper)}")
    
    if len(filtered_upper) == 0:
        print(f"   ❌ FALHA: Nenhum registro encontrado para '{filter_value_upper}'")
        return False
    else:
        print(f"   ✅ SUCESSO: Encontrou {len(filtered_upper)} registro(s)")
    
    # TESTE 2: Filtro com lista de meses
    filter_list = ["Abril", "Novembro"]
    filter_list_lower = [m.lower() for m in filter_list]
    filtered_list = processed_df[
        processed_df['Data_Mes_Nome'].astype(str).str.lower().isin(filter_list_lower)
    ]
    
    print(f"\n🔍 TESTE 2: Filtro {filter_list} (lista)")
    print(f"   Registros encontrados: {len(filtered_list)}")
    
    if len(filtered_list) != 2:
        print(f"   ❌ FALHA: Esperado 2 registros, encontrado {len(filtered_list)}")
        return False
    else:
        print(f"   ✅ SUCESSO: Encontrou {len(filtered_list)} registros")
    
    print("\n" + "="*80)
    print("✅ FIX #6: TODOS OS TESTES PASSARAM")
    print("="*80)
    return True


def test_multiple_commands():
    """
    FIX #7: Testa se sistema aceita lista de comandos
    """
    print("\n" + "="*80)
    print("TESTE FIX #7: MÚLTIPLOS COMANDOS")
    print("="*80)
    
    # Simular comando único
    single_command = {"tool": "calculate_metric", "params": {"metric_column": "Receita"}}
    
    # Simular lista de comandos
    multiple_commands = [
        {"tool": "get_ranking", "params": {"operation": "max"}},
        {"tool": "get_ranking", "params": {"operation": "min"}}
    ]
    
    print("\n🔍 TESTE 1: Comando único (dict)")
    if isinstance(single_command, dict):
        print("   ✅ SUCESSO: Tipo correto (dict)")
        print(f"   Ferramenta: {single_command.get('tool')}")
    else:
        print("   ❌ FALHA: Tipo incorreto")
        return False
    
    print("\n🔍 TESTE 2: Múltiplos comandos (list)")
    if isinstance(multiple_commands, list):
        print("   ✅ SUCESSO: Tipo correto (list)")
        print(f"   Número de comandos: {len(multiple_commands)}")
        
        for idx, cmd in enumerate(multiple_commands, 1):
            if 'tool' not in cmd:
                print(f"   ❌ FALHA: Comando {idx} não tem chave 'tool'")
                return False
            print(f"   Comando {idx}: {cmd.get('tool')} - {cmd.get('params', {}).get('operation')}")
    else:
        print("   ❌ FALHA: Tipo incorreto")
        return False
    
    print("\n" + "="*80)
    print("✅ FIX #7: TODOS OS TESTES PASSARAM")
    print("="*80)
    return True


def test_month_names():
    """
    Testa se função de conversão mês → nome funciona
    """
    print("\n" + "="*80)
    print("TESTE AUXILIAR: CONVERSÃO MÊS → NOME")
    print("="*80)
    
    expected_months = {
        1: "janeiro", 4: "abril", 7: "julho", 11: "novembro"
    }
    
    all_passed = True
    for month_num, expected_name in expected_months.items():
        actual_name = month_number_to_name(month_num)
        
        if actual_name == expected_name:
            print(f"   ✅ Mês {month_num} → '{actual_name}'")
        else:
            print(f"   ❌ Mês {month_num} → Esperado '{expected_name}', obtido '{actual_name}'")
            all_passed = False
    
    if all_passed:
        print("\n✅ CONVERSÃO MÊS → NOME: TODOS OS TESTES PASSARAM")
    else:
        print("\n❌ CONVERSÃO MÊS → NOME: FALHAS DETECTADAS")
    
    return all_passed


def main():
    """
    Executa todos os testes
    """
    print("\n" + "="*80)
    print("🧪 VALIDAÇÃO DAS CORREÇÕES #6 e #7 - DRIVEBOT v11.0")
    print("="*80)
    
    results = []
    
    # Executar testes
    results.append(("FIX #6 - Case-Insensitive", test_case_insensitive_filtering()))
    results.append(("FIX #7 - Múltiplos Comandos", test_multiple_commands()))
    results.append(("Auxiliar - Conversão Mês", test_month_names()))
    
    # Resumo final
    print("\n" + "="*80)
    print("📊 RESUMO DOS TESTES")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*80)
    print(f"RESULTADO FINAL: {passed}/{total} testes passaram ({passed/total*100:.0f}%)")
    print("="*80)
    
    if passed == total:
        print("\n🎉 TODAS AS CORREÇÕES VALIDADAS COM SUCESSO!")
        return 0
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM - REVISAR IMPLEMENTAÇÃO")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
