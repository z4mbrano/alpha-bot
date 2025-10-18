"""
Validators Module
Funções de validação para arquivos, dados e requisições
"""

from typing import Optional, Set
import re


# Extensões de arquivo permitidas para upload
ALLOWED_EXTENSIONS: Set[str] = {'csv', 'xlsx', 'xls'}


def allowed_file(filename: str, allowed_extensions: Optional[Set[str]] = None) -> bool:
    """
    Valida se um arquivo tem extensão permitida.
    
    Args:
        filename: Nome do arquivo a ser validado
        allowed_extensions: Set de extensões permitidas (usa ALLOWED_EXTENSIONS se None)
    
    Returns:
        True se o arquivo é permitido, False caso contrário
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def is_valid_google_drive_folder_id(folder_id: str) -> bool:
    """
    Valida se uma string é um ID válido de pasta do Google Drive.
    
    IDs do Google Drive geralmente têm ~33 caracteres alfanuméricos.
    
    Args:
        folder_id: String a ser validada
    
    Returns:
        True se parece um ID válido, False caso contrário
    """
    if not folder_id or not isinstance(folder_id, str):
        return False
    
    # IDs do Google Drive são alfanuméricos, hifens e underscores
    pattern = r'^[a-zA-Z0-9_-]{20,50}$'
    return bool(re.match(pattern, folder_id.strip()))


def extract_folder_id_from_url(url: str) -> Optional[str]:
    """
    Extrai o ID da pasta de uma URL do Google Drive.
    
    Formatos suportados:
    - https://drive.google.com/drive/folders/ABC123
    - https://drive.google.com/drive/u/0/folders/ABC123
    
    Args:
        url: URL do Google Drive
    
    Returns:
        ID da pasta ou None se não encontrado
    """
    if not url or not isinstance(url, str):
        return None
    
    # Padrão para URLs do Google Drive
    patterns = [
        r'/folders/([a-zA-Z0-9_-]+)',  # Formato padrão
        r'id=([a-zA-Z0-9_-]+)',         # Formato alternativo
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            folder_id = match.group(1)
            if is_valid_google_drive_folder_id(folder_id):
                return folder_id
    
    return None


def validate_session_id(session_id: str) -> bool:
    """
    Valida se um session_id é válido (formato esperado).
    
    Args:
        session_id: String do session_id
    
    Returns:
        True se válido, False caso contrário
    """
    if not session_id or not isinstance(session_id, str):
        return False
    
    # Session IDs são geralmente UUIDs ou strings alfanuméricas
    pattern = r'^[a-zA-Z0-9_-]{8,64}$'
    return bool(re.match(pattern, session_id.strip()))


def validate_conversation_id(conversation_id: str) -> bool:
    """
    Valida se um conversation_id é válido (formato esperado).
    
    Args:
        conversation_id: String do conversation_id
    
    Returns:
        True se válido, False caso contrário
    """
    if not conversation_id or not isinstance(conversation_id, str):
        return False
    
    # Conversation IDs são geralmente UUIDs
    pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    return bool(re.match(pattern, conversation_id.strip().lower()))


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitiza um nome de arquivo removendo caracteres perigosos.
    
    Args:
        filename: Nome do arquivo original
        max_length: Tamanho máximo do nome (padrão: 255)
    
    Returns:
        Nome do arquivo sanitizado
    """
    if not filename:
        return "unnamed_file"
    
    # Remove caracteres perigosos
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove espaços múltiplos e underscores múltiplos
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    
    # Remove pontos no início/fim
    sanitized = sanitized.strip('.')
    
    # Limita tamanho
    if len(sanitized) > max_length:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        name = name[:max_length - len(ext) - 1]
        sanitized = f"{name}.{ext}" if ext else name
    
    return sanitized or "unnamed_file"


def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """
    Valida se o tamanho de um arquivo está dentro do limite.
    
    Args:
        file_size: Tamanho do arquivo em bytes
        max_size_mb: Tamanho máximo permitido em MB
    
    Returns:
        True se o arquivo está dentro do limite, False caso contrário
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return 0 < file_size <= max_size_bytes
