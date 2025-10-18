"""
File Handlers Module
Funções para leitura e processamento de arquivos (CSV, Excel, Google Drive)
"""

from typing import Any, Dict, List
import io
import pandas as pd
from googleapiclient.http import MediaIoBaseDownload

from .data_processors import prepare_table


def download_file_bytes(drive_service: Any, file_id: str) -> bytes:
    """
    Baixa o conteúdo de um arquivo do Google Drive como bytes.
    
    Args:
        drive_service: Cliente autenticado da API do Google Drive
        file_id: ID do arquivo no Google Drive
    
    Returns:
        Bytes do conteúdo do arquivo
    """
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _status, done = downloader.next_chunk()

    return fh.getvalue()


def load_csv_tables(drive_service: Any, file_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Carrega tabelas de um arquivo CSV do Google Drive.
    
    Args:
        drive_service: Cliente autenticado da API do Google Drive
        file_meta: Metadados do arquivo contendo 'id' e 'name'
    
    Returns:
        Lista contendo um único dict com a tabela processada
    """
    content = download_file_bytes(drive_service, file_meta['id'])
    df = pd.read_csv(io.BytesIO(content))
    return [prepare_table(file_meta['name'], df)]


def load_excel_tables(drive_service: Any, file_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Carrega todas as abas de um arquivo Excel do Google Drive.
    
    Args:
        drive_service: Cliente autenticado da API do Google Drive
        file_meta: Metadados do arquivo contendo 'id' e 'name'
    
    Returns:
        Lista de dicts, cada um contendo uma aba processada do Excel
    """
    content = download_file_bytes(drive_service, file_meta['id'])
    workbook = pd.read_excel(io.BytesIO(content), sheet_name=None)
    tables: List[Dict[str, Any]] = []
    
    for sheet_name, df in workbook.items():
        table_name = f"{file_meta['name']} - {sheet_name}"
        tables.append(prepare_table(table_name, df))
    
    return tables


def load_local_csv(file_path: str, table_name: str = None) -> Dict[str, Any]:
    """
    Carrega um arquivo CSV local.
    
    Args:
        file_path: Caminho para o arquivo CSV
        table_name: Nome da tabela (opcional, usa o nome do arquivo se não fornecido)
    
    Returns:
        Dict com a tabela processada
    """
    if table_name is None:
        table_name = file_path.split('/')[-1].replace('.csv', '')
    
    df = pd.read_csv(file_path)
    return prepare_table(table_name, df)


def load_local_excel(file_path: str, sheet_name: str = None) -> List[Dict[str, Any]]:
    """
    Carrega um arquivo Excel local.
    
    Args:
        file_path: Caminho para o arquivo Excel
        sheet_name: Nome da aba específica (opcional, carrega todas se None)
    
    Returns:
        Lista de dicts contendo as abas processadas
    """
    base_name = file_path.split('/')[-1].replace('.xlsx', '').replace('.xls', '')
    
    if sheet_name:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return [prepare_table(f"{base_name} - {sheet_name}", df)]
    
    workbook = pd.read_excel(file_path, sheet_name=None)
    tables: List[Dict[str, Any]] = []
    
    for sheet, df in workbook.items():
        table_name = f"{base_name} - {sheet}"
        tables.append(prepare_table(table_name, df))
    
    return tables


def load_from_bytes(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Carrega tabelas a partir de bytes de um arquivo.
    
    Detecta automaticamente o tipo (CSV ou Excel) pela extensão do filename.
    
    Args:
        file_bytes: Conteúdo do arquivo em bytes
        filename: Nome do arquivo (usado para detectar extensão)
    
    Returns:
        Lista de dicts contendo as tabelas processadas
    
    Raises:
        ValueError: Se o formato do arquivo não for suportado
    """
    ext = filename.lower().split('.')[-1]
    
    if ext == 'csv':
        df = pd.read_csv(io.BytesIO(file_bytes))
        return [prepare_table(filename, df)]
    
    elif ext in ('xlsx', 'xls'):
        workbook = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
        tables: List[Dict[str, Any]] = []
        
        for sheet_name, df in workbook.items():
            table_name = f"{filename} - {sheet_name}"
            tables.append(prepare_table(table_name, df))
        
        return tables
    
    else:
        raise ValueError(f"Formato de arquivo não suportado: .{ext}")
