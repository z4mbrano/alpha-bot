"""
Data Processors Module
Funções para processamento e normalização de dados em DataFrames
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from ..config.settings import MONTH_TRANSLATION, MONTH_NAMES_PT


def normalize_decimal_string(value: Any) -> Optional[str]:
    """Normaliza strings com valores decimais para formato padrão."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None

    if isinstance(value, (int, float, np.number)):
        return str(value)

    text = str(value).strip()
    if not text or text.lower() in {'nan', 'none', 'null'}:
        return None

    # Remove símbolos comuns
    text = text.replace('R$', '').replace('%', '').replace(' ', '')
    text = text.replace('\t', '').replace('\n', '').replace('\r', '')
    text = text.replace('\u00a0', '')  # Non-breaking space

    # Normaliza separadores decimais
    if text.count(',') == 1 and text.count('.') >= 1:
        # Formato: 1.234,56 -> 1234.56
        text = text.replace('.', '').replace(',', '.')
    elif text.count(',') > 0:
        # Formato: 1234,56 -> 1234.56
        text = text.replace(',', '.')

    return text


def coerce_numeric_series(series: pd.Series) -> pd.Series:
    """Converte uma série para numérico com tratamento robusto."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors='coerce')

    normalized = series.astype(str).map(normalize_decimal_string)
    return pd.to_numeric(normalized, errors='coerce')


def detect_numeric_columns(df: pd.DataFrame) -> Tuple[List[str], Dict[str, pd.Series]]:
    """
    Detecta colunas numéricas em um DataFrame.
    
    Returns:
        Tuple contendo:
        - Lista de nomes das colunas numéricas
        - Dict mapeando nome da coluna para série convertida
    """
    numeric_columns: List[str] = []
    numeric_data: Dict[str, pd.Series] = {}

    for column in df.columns:
        coerced = coerce_numeric_series(df[column])
        # Considerar numérica se >= 30% dos valores forem convertidos
        if coerced.notna().sum() >= max(1, int(len(coerced) * 0.3)):
            numeric_columns.append(column)
            numeric_data[column] = coerced

    return numeric_columns, numeric_data


def normalize_month_text(value: Any) -> Any:
    """Normaliza texto de mês em português para inglês."""
    if not isinstance(value, str):
        return value

    text = value.strip()
    lower = text.lower()
    for pt_name, eng_name in MONTH_TRANSLATION.items():
        if pt_name in lower:
            lower = lower.replace(pt_name, eng_name.lower())
    return lower


def month_number_to_name(month_num: int) -> str:
    """
    Converte número do mês (1-12) para nome em português.
    Usado para criar coluna auxiliar 'Data_Mes_Nome'.
    
    Retorna em minúsculas para consistência com filtros case-insensitive.
    """
    return MONTH_NAMES_PT.get(month_num, str(month_num))


def detect_datetime_columns(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Detecta e converte colunas de data/hora com tratamento robusto.
    
    Tenta múltiplos formatos:
    - ISO (YYYY-MM-DD)
    - Brasileiro (DD/MM/YYYY)
    - Americano (MM/DD/YYYY)
    - Texto de mês (ex: "Janeiro 2024")
    
    Returns:
        Dict mapeando nome da coluna para série de datetime convertida
    """
    datetime_columns: Dict[str, pd.Series] = {}

    for column in df.columns:
        series = df[column]
        parsed = None
        
        if pd.api.types.is_datetime64_any_dtype(series):
            # Já é datetime, apenas garantir
            parsed = pd.to_datetime(series, errors='coerce')
        else:
            # Tentar múltiplos formatos comuns
            # Formato ISO (YYYY-MM-DD) - mais comum e inequívoco
            parsed = pd.to_datetime(series, format='%Y-%m-%d', errors='coerce')
            
            if parsed.isna().all():
                # Formato brasileiro (DD/MM/YYYY)
                parsed = pd.to_datetime(series, format='%d/%m/%Y', errors='coerce', dayfirst=True)
            
            if parsed.isna().all():
                # Formato americano (MM/DD/YYYY)
                parsed = pd.to_datetime(series, format='%m/%d/%Y', errors='coerce')
            
            if parsed.isna().all():
                # Formato com texto de mês (ex: "Janeiro 2024")
                normalized = series.astype(str).map(normalize_month_text)
                parsed = pd.to_datetime(normalized, errors='coerce', dayfirst=True)
            
            if parsed.isna().all():
                # Último recurso: deixar pandas inferir (SEM dayfirst para evitar ambiguidade)
                parsed = pd.to_datetime(series, errors='coerce', dayfirst=False)

        # Considerar válida se >= 30% dos valores foram convertidos com sucesso
        if parsed is not None and parsed.notna().sum() >= max(1, int(len(parsed) * 0.3)):
            parsed.name = column
            datetime_columns[column] = parsed

    return datetime_columns


def detect_text_columns(df: pd.DataFrame, numeric_columns: List[str]) -> List[str]:
    """
    Detecta colunas de texto em um DataFrame.
    
    Args:
        df: DataFrame a ser analisado
        numeric_columns: Lista de colunas já identificadas como numéricas
    
    Returns:
        Lista de nomes de colunas identificadas como texto
    """
    text_columns: List[str] = []
    numeric_set = set(numeric_columns)

    for column in df.columns:
        if column in numeric_set:
            continue
        series = df[column]
        if pd.api.types.is_string_dtype(series) or series.dtype == object:
            if series.astype(str).str.strip().replace('', np.nan).notna().sum() > 0:
                text_columns.append(column)

    return text_columns


def build_temporal_mask(
    table: Dict[str, Any],
    year: Optional[int] = None,
    month: Optional[int] = None
) -> Optional[pd.Series]:
    """
    Constrói máscara booleana para filtrar dados por ano/mês.
    
    Args:
        table: Dict contendo 'datetime_columns' com séries de datetime
        year: Filtro de ano (opcional)
        month: Filtro de mês (opcional)
    
    Returns:
        Série booleana com a máscara ou None se não houver colunas de data
    """
    datetime_columns: Dict[str, pd.Series] = table.get('datetime_columns', {})
    if not datetime_columns:
        return None

    combined_mask: Optional[pd.Series] = None
    for parsed in datetime_columns.values():
        mask = parsed.notna()
        if year is not None:
            mask &= parsed.dt.year == year
        if month is not None:
            mask &= parsed.dt.month == month
        if combined_mask is None:
            combined_mask = mask
        else:
            combined_mask |= mask

    return combined_mask


def prepare_table(table_name: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Processa um DataFrame completo, detectando tipos e criando colunas auxiliares.
    
    Cria colunas auxiliares para análise temporal:
    - {coluna}_Mes: Número do mês (1-12)
    - {coluna}_Ano: Ano (ex: 2024)
    - {coluna}_Trimestre: Trimestre (1-4)
    - {coluna}_Mes_Nome: Nome do mês em português
    
    Args:
        table_name: Nome identificador da tabela
        df: DataFrame a ser processado
    
    Returns:
        Dict com metadados da tabela processada
    """
    processed = df.copy()
    processed.columns = [str(col).strip() for col in processed.columns]
    processed = processed.replace('', np.nan)

    numeric_columns, numeric_data = detect_numeric_columns(processed)
    datetime_columns = detect_datetime_columns(processed)
    text_columns = detect_text_columns(processed, numeric_columns)
    
    # Criar colunas auxiliares para CADA coluna de data detectada
    auxiliary_columns_created = []
    for col_name, datetime_series in datetime_columns.items():
        # Adicionar coluna "Mes" (numérico: 1-12)
        mes_col = f"{col_name}_Mes"
        processed[mes_col] = datetime_series.dt.month
        numeric_columns.append(mes_col)
        auxiliary_columns_created.append(mes_col)
        
        # Adicionar coluna "Ano" (numérico: ex: 2024)
        ano_col = f"{col_name}_Ano"
        processed[ano_col] = datetime_series.dt.year
        numeric_columns.append(ano_col)
        auxiliary_columns_created.append(ano_col)
        
        # Adicionar coluna "Trimestre" (numérico: 1-4)
        trimestre_col = f"{col_name}_Trimestre"
        processed[trimestre_col] = datetime_series.dt.quarter
        numeric_columns.append(trimestre_col)
        auxiliary_columns_created.append(trimestre_col)
        
        # Adicionar coluna "Mes_Nome" (texto: "janeiro", "fevereiro", etc.)
        mes_nome_col = f"{col_name}_Mes_Nome"
        processed[mes_nome_col] = datetime_series.dt.month.map(month_number_to_name)
        text_columns.append(mes_nome_col)
        auxiliary_columns_created.append(mes_nome_col)

    return {
        'name': table_name,
        'df': processed,
        'row_count': int(len(processed)),
        'columns': list(processed.columns),
        'numeric_columns': numeric_columns,
        'numeric_data': numeric_data,
        'datetime_columns': datetime_columns,
        'text_columns': text_columns,
        'auxiliary_columns': auxiliary_columns_created,
    }
