"""
🔧 DATA PROCESSOR UNIFICADO - DriveBot + AlphaBot
Função única para garantir processamento idêntico de dados entre os bots

Correção dos problemas:
1. Coluna 'Quantidade' sendo tratada como temporal (1970) no AlphaBot
2. Inconsistência de cálculos financeiros entre bots
3. Tipagem de dados não determinística

Data: 19/12/2024
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import unicodedata
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_dataframe_unified(df: pd.DataFrame, source_info: str = "unknown") -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    🔧 FUNÇÃO UNIFICADA DE PROCESSAMENTO DE DATAFRAME
    
    Garante que DriveBot e AlphaBot processem dados de forma idêntica.
    Corrige especificamente o bug da coluna 'Quantidade' sendo tratada como temporal.
    
    Args:
        df: DataFrame para processar
        source_info: Informação sobre origem dos dados (para logging)
    
    Returns:
        Tuple[DataFrame processado, Metadata do processamento]
    """
    logger.info(f"[UNIFIED PROCESSOR] Iniciando processamento para {source_info}")
    logger.info(f"[UNIFIED PROCESSOR] DataFrame original: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Criar cópia para não modificar original
    processed_df = df.copy()
    metadata = {
        "source": source_info,
        "original_rows": len(df),
        "original_columns": len(df.columns),
        "columns_processed": {},
        "data_quality": {},
        "financial_summary": {}
    }
    
    # 🔧 CORREÇÃO CRÍTICA 1: Palavras-chave para identificar colunas financeiras
    financial_keywords = [
        'quantidade', 'receita', 'receita_total', 'valor', 'preco', 'preço', 'preco_unitario', 'preço_unitário', 'faturamento', 
        'total', 'vendas', 'custo', 'lucro', 'margem', 'desconto'
    ]
    
    # Palavras-chave para EXCLUIR (colunas textuais que nunca devem ser convertidas)
    # NOTA: 'quantidade' foi REMOVIDA desta lista - ela é financeira!
    text_keywords = [
        'nome', 'produto', 'categoria', 'cliente', 'regiao', 'região',
        'cidade', 'estado', 'uf', 'loja', 'filial', 'grupo', 'setor', 
        'descricao', 'descrição', 'id', 'codigo', 'código', 'transacao'
    ]
    
    # Meses em português que indicam coluna textual
    months_pt = [
        'janeiro', 'fevereiro', 'março', 'marco', 'abril', 'maio', 'junho',
        'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
    ]
    
    logger.info("[UNIFIED PROCESSOR] 🔧 Aplicando tipagem seletiva para colunas financeiras...")
    
    # Helper para normalização
    def normalize_name(s: str) -> str:
        s = s.lower()
        s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
        return s

    # 🚨 CRÍTICO: Também excluir colunas auxiliares geradas anteriormente
    skip_column_suffixes = ['_mes_nome', '_nome', '_ano', '_mes', '_trimestre']

    # Processar apenas colunas que parecem financeiras
    for col in processed_df.columns:
        col_norm = normalize_name(col)
        
        # Pular colunas auxiliares geradas (terminam com sufixos conhecidos)
        if any(col_norm.endswith(suffix) for suffix in skip_column_suffixes):
            logger.info(f"[UNIFIED PROCESSOR] ⏭️ Pulando coluna auxiliar: '{col}'")
            continue
        
        # VERIFICAR SE A COLUNA CONTÉM MESES (NUNCA CONVERTER)
        if processed_df[col].dtype == 'object':
            sample_values = processed_df[col].dropna().astype(str).str.lower().head(10).tolist()
            contains_months = any(any(month in str(val) for month in months_pt) for val in sample_values)
            if contains_months:
                logger.info(f"[UNIFIED PROCESSOR] ⏭️ Pulando coluna de meses: '{col}' (contém: {sample_values[:3]})")
                continue
        
        # DETECTAR COLUNAS FINANCEIRAS POR PALAVRAS-CHAVE (com prioridade sobre exclusões)
        is_financial = any(fin_kw in col_norm for fin_kw in financial_keywords)
        
        # VERIFICAR SE A COLUNA É TEXTUAL (NUNCA CONVERTER) - MAS APENAS SE NÃO FOR FINANCEIRA
        if not is_financial:
            is_text_column = any(text_kw in col_norm for text_kw in text_keywords)
            if is_text_column:
                logger.info(f"[UNIFIED PROCESSOR] ⏭️ Pulando coluna textual: '{col}'")
                continue
        
        # SE FOR FINANCEIRA E DO TIPO OBJECT, TENTAR CONVERTER
        if is_financial and processed_df[col].dtype == 'object':
            logger.info(f"[UNIFIED PROCESSOR] 💰 Processando coluna financeira detectada: '{col}'")
            
            try:
                # Converter para string primeiro para limpar formatação
                processed_df[col] = processed_df[col].astype(str)
                
                # Limpar formatação brasileira/internacional
                processed_df[col] = processed_df[col].str.replace('R$', '', regex=False)
                processed_df[col] = processed_df[col].str.replace('$', '', regex=False)
                processed_df[col] = processed_df[col].str.replace('.', '', regex=False)  # Separador milhares
                processed_df[col] = processed_df[col].str.replace(',', '.', regex=False)  # Decimal brasileiro
                processed_df[col] = processed_df[col].str.strip()
                
                # Converter para numérico (CRÍTICO: errors='coerce' para limpar dados ruins)
                # Primeiro, testar a conversão em uma cópia para validar
                test_conversion = pd.to_numeric(processed_df[col], errors='coerce')
                
                # Verificar se a conversão foi bem-sucedida (pelo menos 80% dos valores convertidos)
                valid_count = test_conversion.notna().sum()
                total_count = len(processed_df)
                success_rate = (valid_count / total_count) * 100 if total_count > 0 else 0
                
                # Para colunas claramente financeiras (receita/valor/preço/faturamento), forçar conversão mesmo com taxa menor
                force_financial = any(key in col_norm for key in ['receita', 'valor', 'preco', 'preço', 'faturamento'])
                threshold_ok = success_rate >= 80 or force_financial and success_rate >= 30
                if not threshold_ok:
                    logger.warning(f"[UNIFIED PROCESSOR] ⚠️ '{col}': Conversão com baixa taxa de sucesso ({success_rate:.1f}% válidos). Mantendo como texto.")
                    # Reverter para tipo original
                    continue
                
                # Aplicar a conversão validada
                original_dtype = processed_df[col].dtype
                processed_df[col] = test_conversion
                
                # Preencher NaN com 0 para cálculos financeiros
                nan_count = processed_df[col].isna().sum()
                processed_df[col] = processed_df[col].fillna(0)
                
                metadata["columns_processed"][col] = {
                    "type": "financial_numeric",
                    "original_dtype": str(original_dtype),
                    "final_dtype": str(processed_df[col].dtype),
                    "nan_values_filled": int(nan_count),
                    "conversion_success_rate": float(success_rate),
                    "sample_values": processed_df[col].head(3).tolist()
                }
                
                logger.info(f"[UNIFIED PROCESSOR] ✅ '{col}': Convertida com sucesso ({success_rate:.1f}% válidos, {nan_count} NaN preenchidos)")
                
            except Exception as e:
                logger.error(f"[UNIFIED PROCESSOR] ❌ Erro ao processar '{col}': {e}")
                # Reverter para tipo original em caso de erro
                processed_df[col] = df[col].copy()
    
    # 🔧 CORREÇÃO CRÍTICA 2: Forçar tipagem explícita de colunas temporais
    date_columns = ['Data', 'Date', 'data', 'date']
    
    logger.info("[UNIFIED PROCESSOR] 🔧 Aplicando tipagem forçada para colunas temporais...")
    
    for col in processed_df.columns:
        col_norm = normalize_name(col)
        
        # Evitar processar colunas derivadas como datas novamente
        if any(col_norm.endswith(suffix) for suffix in ['_ano', '_mes', '_trimestre', '_mes_nome']):
            continue
        
        # Detectar colunas de data
        is_date = any(date_term in col_norm for date_term in ['data', 'date', 'tempo', 'time'])
        
        if is_date:
            logger.info(f"[UNIFIED PROCESSOR] Processando coluna temporal: '{col}'")
            
            original_dtype = processed_df[col].dtype
            
            # Múltiplos formatos de data para máxima compatibilidade
            date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']
            parsed_successfully = False
            
            for date_format in date_formats:
                try:
                    processed_df[col] = pd.to_datetime(processed_df[col], format=date_format, errors='coerce')
                    valid_dates = processed_df[col].notna().sum()
                    if valid_dates > len(processed_df) * 0.5:  # Pelo menos 50% válidas
                        parsed_successfully = True
                        logger.info(f"[UNIFIED PROCESSOR] ✅ '{col}': Formato '{date_format}' funcionou ({valid_dates} válidas)")
                        break
                except:
                    continue
            
            # Fallback: pandas automático
            if not parsed_successfully:
                processed_df[col] = pd.to_datetime(processed_df[col], errors='coerce')
                valid_dates = processed_df[col].notna().sum()
                logger.info(f"[UNIFIED PROCESSOR] ⚠️ '{col}': Usando parser automático ({valid_dates} válidas)")
            
            # 🚨 VALIDAÇÃO CRÍTICA: Remover datas epoch (1970) que causam bugs
            epoch_filter = (processed_df[col] >= '1990-01-01') & (processed_df[col] <= '2030-12-31')
            invalid_dates = (~epoch_filter & processed_df[col].notna()).sum()
            if invalid_dates > 0:
                processed_df.loc[~epoch_filter, col] = pd.NaT
                logger.warning(f"[UNIFIED PROCESSOR] ⚠️ '{col}': Removidas {invalid_dates} datas inválidas (epoch/futuro)")
            
            # 🔧 EXTRAIR COMPONENTES DE DATA (Ano, Mês, Trimestre, Nome do Mês)
            if processed_df[col].notna().any():
                try:
                    # Criar colunas derivadas
                    processed_df[f'{col}_Ano'] = processed_df[col].dt.year
                    processed_df[f'{col}_Mes'] = processed_df[col].dt.month
                    processed_df[f'{col}_Trimestre'] = processed_df[col].dt.to_period('Q').astype(str)
                    
                    # Nome do mês em português
                    try:
                        import locale
                        # Tentar configurar locale para português
                        for loc in ['pt_BR.UTF-8', 'pt_BR', 'Portuguese_Brazil.1252', 'Portuguese']:
                            try:
                                locale.setlocale(locale.LC_TIME, loc)
                                logger.info(f"[UNIFIED PROCESSOR] ✅ Locale configurado: {loc}")
                                break
                            except:
                                continue
                    except Exception as e:
                        logger.warning(f"[UNIFIED PROCESSOR] ⚠️ Não foi possível configurar locale pt_BR: {e}")
                    
                    # Mapear nomes de meses em português (fallback se locale falhar)
                    month_names_pt = {
                        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
                    }
                    processed_df[f'{col}_Mes_Nome'] = processed_df[f'{col}_Mes'].map(month_names_pt)
                    
                    logger.info(f"[UNIFIED PROCESSOR] ✅ Componentes de data extraídos: {col}_Ano, {col}_Mes, {col}_Trimestre, {col}_Mes_Nome")
                    
                except Exception as e:
                    logger.warning(f"[UNIFIED PROCESSOR] ⚠️ Erro ao extrair componentes de data de '{col}': {e}")
            
            metadata["columns_processed"][col] = {
                "type": "temporal",
                "original_dtype": str(original_dtype),
                "final_dtype": str(processed_df[col].dtype),
                "valid_dates": int(processed_df[col].notna().sum()),
                "invalid_dates_removed": int(invalid_dates),
                "date_range": {
                    "min": str(processed_df[col].min()) if processed_df[col].notna().any() else None,
                    "max": str(processed_df[col].max()) if processed_df[col].notna().any() else None
                }
            }
    
    # 🔧 CORREÇÃO CRÍTICA 3: Calcular métricas financeiras unificadas
    logger.info("[UNIFIED PROCESSOR] 📊 Calculando métricas financeiras...")
    
    # Identificar colunas financeiras processadas
    quantidade_col = None
    receita_col = None
    
    for col in processed_df.columns:
        if 'quantidade' in col.lower():
            quantidade_col = col
        elif any(term in col.lower() for term in ['receita', 'valor', 'total', 'faturamento']):
            if receita_col is None:  # Pegar a primeira encontrada
                receita_col = col
    
    # Se não existir 'receita' numérica mas existir quantidade e preço unitário, calcular receita total derivada
    if receita_col is None or not pd.api.types.is_numeric_dtype(processed_df.get(receita_col, pd.Series(dtype=float))):
        preco_cols = [c for c in processed_df.columns if any(term in c.lower() for term in ['preco', 'preço'])]
        preco_col = None
        for c in preco_cols:
            if pd.api.types.is_numeric_dtype(processed_df[c]):
                preco_col = c
                break
        if quantidade_col and preco_col:
            derived_col = 'Receita_Total_Derivada'
            try:
                processed_df[derived_col] = processed_df[quantidade_col].fillna(0) * processed_df[preco_col].fillna(0)
                receita_col = derived_col
                logger.info(f"[UNIFIED PROCESSOR] ✅ Receita derivada criada a partir de '{quantidade_col}' x '{preco_col}'")
            except Exception as e:
                logger.warning(f"[UNIFIED PROCESSOR] ⚠️ Falha ao criar receita derivada: {e}")

    if quantidade_col and receita_col:
        # Garantir que as colunas são numéricas antes de somar
        if pd.api.types.is_numeric_dtype(processed_df[quantidade_col]):
            total_quantidade = processed_df[quantidade_col].sum()
        else:
            total_quantidade = 0
            logger.warning(f"[UNIFIED PROCESSOR] ⚠️ Coluna '{quantidade_col}' não é numérica, usando 0")
        
        if pd.api.types.is_numeric_dtype(processed_df[receita_col]):
            total_receita = processed_df[receita_col].sum()
        else:
            total_receita = 0
            logger.warning(f"[UNIFIED PROCESSOR] ⚠️ Coluna '{receita_col}' não é numérica, usando 0")
        
        metadata["financial_summary"] = {
            "quantidade_column": quantidade_col,
            "receita_column": receita_col,
            "total_quantidade": float(total_quantidade),
            "total_receita": float(total_receita),
            "total_receita_formatted": f"R$ {total_receita:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        }
        
        logger.info(f"[UNIFIED PROCESSOR] 💰 Total Quantidade: {total_quantidade:,.0f}")
        logger.info(f"[UNIFIED PROCESSOR] 💰 Total Receita: R$ {total_receita:,.2f}")
    
    # 🔧 CORREÇÃO CRÍTICA 4: Validação de qualidade de dados
    metadata["data_quality"] = {
        "total_rows_final": len(processed_df),
        "total_columns_final": len(processed_df.columns),
        "missing_values_by_column": processed_df.isnull().sum().to_dict(),
        "duplicated_rows": int(processed_df.duplicated().sum())
    }
    
    logger.info(f"[UNIFIED PROCESSOR] ✅ Processamento concluído para {source_info}")
    logger.info(f"[UNIFIED PROCESSOR] Resultado: {len(processed_df)} linhas, {len(processed_df.columns)} colunas")
    
    return processed_df, metadata


def validate_financial_consistency(df1: pd.DataFrame, df2: pd.DataFrame, label1: str = "DataFrame1", label2: str = "DataFrame2") -> Dict[str, Any]:
    """
    Valida consistência financeira entre dois DataFrames processados
    
    Args:
        df1, df2: DataFrames para comparar
        label1, label2: Labels para identificação
    
    Returns:
        Dict com resultados da validação
    """
    validation_results = {
        "consistent": True,
        "differences": [],
        "summary": {}
    }
    
    # Identificar colunas financeiras em ambos
    financial_cols = []
    for col in df1.columns:
        if any(term in col.lower() for term in ['quantidade', 'receita', 'valor', 'total', 'faturamento']):
            if col in df2.columns:
                financial_cols.append(col)
    
    for col in financial_cols:
        sum1 = df1[col].sum()
        sum2 = df2[col].sum()
        
        diff_abs = abs(sum1 - sum2)
        diff_pct = (diff_abs / max(sum1, sum2)) * 100 if max(sum1, sum2) > 0 else 0
        
        validation_results["summary"][col] = {
            f"{label1}_total": float(sum1),
            f"{label2}_total": float(sum2),
            "difference_absolute": float(diff_abs),
            "difference_percentage": float(diff_pct)
        }
        
        if diff_pct > 1:  # Mais de 1% de diferença é significativo
            validation_results["consistent"] = False
            validation_results["differences"].append({
                "column": col,
                "difference_pct": diff_pct,
                "values": {label1: sum1, label2: sum2}
            })
    
    return validation_results