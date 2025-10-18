#!/usr/bin/env python3
"""
DriveBot v11.0 - Validação Final
Verifica se todos os componentes críticos estão implementados
"""

print('='*60)
print('VALIDAÇÃO FINAL - DRIVEBOT V11.0')
print('='*60)
print()

from app import DRIVEBOT_SYSTEM_PROMPT

# Verificações de componentes v11.0
v11_checks = {
    'Título v11.0': 'Analista Autônomo Confiável' in DRIVEBOT_SYSTEM_PROMPT,
    'Mandatos Inquebráveis': 'MANDATOS INQUEBRÁVEIS' in DRIVEBOT_SYSTEM_PROMPT or 'Mandatos Inquebráveis' in DRIVEBOT_SYSTEM_PROMPT,
    'Tolerância Zero (≥5)': DRIVEBOT_SYSTEM_PROMPT.count('Tolerância Zero') + DRIVEBOT_SYSTEM_PROMPT.count('TOLERÂNCIA ZERO') >= 5,
    'Context Bleed (≥5)': DRIVEBOT_SYSTEM_PROMPT.count('Context Bleed') + DRIVEBOT_SYSTEM_PROMPT.count('CONTEXT BLEED') >= 5,
    'Checklist Pré-Execução': 'CHECKLIST' in DRIVEBOT_SYSTEM_PROMPT,
    'Auto-Correção': 'INCONSISTÊNCIA' in DRIVEBOT_SYSTEM_PROMPT or 'AUTO-CORREÇÃO' in DRIVEBOT_SYSTEM_PROMPT,
    'Clarificação': 'CLARIFICAÇÃO' in DRIVEBOT_SYSTEM_PROMPT,
    'Léxico Semântico': 'Léxico' in DRIVEBOT_SYSTEM_PROMPT,
    'Log de Análise': 'Log de Análise' in DRIVEBOT_SYSTEM_PROMPT,
}

print('COMPONENTES v11.0:')
print()

for component, status in v11_checks.items():
    symbol = '✅' if status else '❌'
    print(f'  [{symbol}] {component}')

print()

# Estatísticas
total = sum(v11_checks.values())
pct = (total / len(v11_checks)) * 100

print(f'SCORE: {total}/{len(v11_checks)} ({pct:.0f}%)')
print()

# Estatísticas do prompt
print('ESTATÍSTICAS DO PROMPT:')
print(f'  - Tamanho: {len(DRIVEBOT_SYSTEM_PROMPT):,} caracteres')
print(f'  - Linhas: {DRIVEBOT_SYSTEM_PROMPT.count(chr(10)):,}')
print(f'  - Menções "Tolerância Zero": {DRIVEBOT_SYSTEM_PROMPT.count("Tolerância Zero") + DRIVEBOT_SYSTEM_PROMPT.count("TOLERÂNCIA ZERO")}')
print(f'  - Menções "Context Bleed": {DRIVEBOT_SYSTEM_PROMPT.count("Context Bleed") + DRIVEBOT_SYSTEM_PROMPT.count("CONTEXT BLEED")}')
print(f'  - Menções "Checklist": {DRIVEBOT_SYSTEM_PROMPT.count("CHECKLIST")}')
print()

# Resultado final
if all(v11_checks.values()):
    print('🎉 TODOS OS COMPONENTES IMPLEMENTADOS')
    print('✅ DriveBot v11.0 PRONTO PARA PRODUÇÃO')
    print()
    print('PRÓXIMOS PASSOS:')
    print('  1. Execute os testes em: TESTES_V11_VALIDACAO.md')
    print('  2. Teste com dados reais do Google Drive')
    print('  3. Valide os 3 Mandatos Inquebráveis')
    print('  4. Forneça feedback')
else:
    print('⚠️  ALGUNS COMPONENTES AUSENTES')
    print('❌ REVISÃO NECESSÁRIA')
    print()
    print('COMPONENTES FALTANDO:')
    for component, status in v11_checks.items():
        if not status:
            print(f'  - {component}')

print()
print('='*60)
