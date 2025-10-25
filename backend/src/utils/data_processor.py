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
    
    # 🔧 CORREÇÃO CRÍTICA 1: Forçar tipagem explícita de colunas financeiras
    financial_columns = {
        'Quantidade': 'numeric',
        'Receita_Total': 'numeric', 
        'Valor': 'numeric',
        'Preco': 'numeric',
        'Preço': 'numeric',
        'Total': 'numeric',
        'Faturamento': 'numeric',
        'Vendas': 'numeric'
    }
    
    logger.info("[UNIFIED PROCESSOR] 🔧 Aplicando tipagem forçada para colunas financeiras...")
    
    for col in processed_df.columns:
        col_lower = col.lower()
        
        # Detectar colunas financeiras por nome
        is_financial = any(fin_term in col_lower for fin_term in financial_columns.keys())
        
        if is_financial or col in financial_columns:
            logger.info(f"[UNIFIED PROCESSOR] Processando coluna financeira: '{col}'")
            
            # Converter para string primeiro para limpar formatação
            processed_df[col] = processed_df[col].astype(str)
            
            # Limpar formatação brasileira/internacional
            processed_df[col] = processed_df[col].str.replace('R$', '', regex=False)
            processed_df[col] = processed_df[col].str.replace('$', '', regex=False)
            processed_df[col] = processed_df[col].str.replace('.', '', regex=False)  # Separador milhares
            processed_df[col] = processed_df[col].str.replace(',', '.', regex=False)  # Decimal brasileiro
            processed_df[col] = processed_df[col].str.strip()
            
            # Converter para numérico (CRÍTICO: errors='coerce' para limpar dados ruins)
            original_dtype = processed_df[col].dtype
            processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
            
            # Preencher NaN com 0 para cálculos financeiros
            nan_count = processed_df[col].isna().sum()
            processed_df[col] = processed_df[col].fillna(0)
            
            metadata["columns_processed"][col] = {
                "type": "financial_numeric",
                "original_dtype": str(original_dtype),
                "final_dtype": str(processed_df[col].dtype),
                "nan_values_filled": int(nan_count),
                "sample_values": processed_df[col].head(3).tolist()
            }
            
            logger.info(f"[UNIFIED PROCESSOR] ✅ '{col}': {original_dtype} → {processed_df[col].dtype} ({nan_count} NaN preenchidos)")
    
    # 🔧 CORREÇÃO CRÍTICA 2: Forçar tipagem explícita de colunas temporais
    date_columns = ['Data', 'Date', 'data', 'date']
    
    logger.info("[UNIFIED PROCESSOR] 🔧 Aplicando tipagem forçada para colunas temporais...")
    
    for col in processed_df.columns:
        col_lower = col.lower()
        
        # Detectar colunas de data
        is_date = any(date_term in col_lower for date_term in ['data', 'date', 'tempo', 'time'])
        
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
    
    if quantidade_col and receita_col:
        total_quantidade = processed_df[quantidade_col].sum()
        total_receita = processed_df[receita_col].sum()
        
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