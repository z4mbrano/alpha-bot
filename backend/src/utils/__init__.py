"""
Utils Module
Funções utilitárias para processamento de dados, arquivos e validações
"""

from .data_processors import (
    normalize_decimal_string,
    coerce_numeric_series,
    detect_numeric_columns,
    normalize_month_text,
    month_number_to_name,
    detect_datetime_columns,
    detect_text_columns,
    build_temporal_mask,
    prepare_table,
)

from .file_handlers import (
    download_file_bytes,
    load_csv_tables,
    load_excel_tables,
    load_local_csv,
    load_local_excel,
    load_from_bytes,
)

from .validators import (
    ALLOWED_EXTENSIONS,
    allowed_file,
    is_valid_google_drive_folder_id,
    extract_folder_id_from_url,
    validate_session_id,
    validate_conversation_id,
    sanitize_filename,
    validate_file_size,
)

__all__ = [
    # Data Processors
    'normalize_decimal_string',
    'coerce_numeric_series',
    'detect_numeric_columns',
    'normalize_month_text',
    'month_number_to_name',
    'detect_datetime_columns',
    'detect_text_columns',
    'build_temporal_mask',
    'prepare_table',
    
    # File Handlers
    'download_file_bytes',
    'load_csv_tables',
    'load_excel_tables',
    'load_local_csv',
    'load_local_excel',
    'load_from_bytes',
    
    # Validators
    'ALLOWED_EXTENSIONS',
    'allowed_file',
    'is_valid_google_drive_folder_id',
    'extract_folder_id_from_url',
    'validate_session_id',
    'validate_conversation_id',
    'sanitize_filename',
    'validate_file_size',
]
