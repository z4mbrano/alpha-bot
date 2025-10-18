#!/usr/bin/env python3
"""Script para corrigir bytes nulos no app.py"""

from pathlib import Path

app_file = Path(__file__).parent / 'app.py'

# Ler o arquivo
print(f"Lendo {app_file}...")
with open(app_file, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Substituir a função problemática
old_func = """def normalize_decimal_string(value: Any) -> Optional[str]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None

    if isinstance(value, (int, float, np.number)):
        return str(value)

    text = str(value).strip()
    if not text or text.lower() in {'nan', 'none', 'null'}:
        return None

', '').replace('
', '').replace(' a', '')
    replacements = [
        ('R$', ''),
        ('%', ''),
        ('\\u00a0', ''),
        ('\\t', ''),
        ('\\n', ''),
        ('\\r', ''),
        (' ', ''),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    if text.count(',') == 1 and text.count('.') >= 1:
        text = text.replace('.', '').replace(',', '.')
    elif text.count(',') > 0:
        text = text.replace('.', '').replace(',', '.')

    return text"""

new_func = """def normalize_decimal_string(value: Any) -> Optional[str]:
    \"\"\"Normaliza strings com valores decimais para formato padrão.\"\"\"
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None

    if isinstance(value, (int, float, np.number)):
        return str(value)

    text = str(value).strip()
    if not text or text.lower() in {'nan', 'none', 'null'}:
        return None

    # Remove símbolos comuns
    text = text.replace('R$', '').replace('%', '').replace(' ', '')
    text = text.replace('\\t', '').replace('\\n', '').replace('\\r', '')
    text = text.replace('\\u00a0', '')  # Non-breaking space

    # Normaliza separadores decimais
    if text.count(',') == 1 and text.count('.') >= 1:
        # Formato: 1.234,56 -> 1234.56
        text = text.replace('.', '').replace(',', '.')
    elif text.count(',') > 0:
        # Formato: 1234,56 -> 1234.56
        text = text.replace(',', '.')

    return text"""

# Tentar remover bytes nulos
content_clean = content.replace('\x00', '')

# Verificar se conseguimos encontrar a função
if "def normalize_decimal_string" in content_clean:
    print("Função normalize_decimal_string encontrada")
    
    # Procurar e substituir a parte problemática
    lines = content_clean.split('\n')
    new_lines = []
    skip_until_def = False
    in_normalize = False
    
    for i, line in enumerate(lines):
        if 'def normalize_decimal_string' in line:
            in_normalize = True
            new_lines.extend(new_func.split('\n'))
            skip_until_def = True
            continue
        
        if skip_until_def:
            if line.strip().startswith('def ') and 'normalize_decimal_string' not in line:
                skip_until_def = False
                in_normalize = False
                new_lines.append(line)
            continue
        
        new_lines.append(line)
    
    content_clean = '\n'.join(new_lines)
    
    # Salvar o arquivo corrigido
    print(f"Salvando {app_file}...")
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content_clean)
    
    print("✅ Arquivo corrigido com sucesso!")
else:
    print("❌ Função normalize_decimal_string não encontrada")
