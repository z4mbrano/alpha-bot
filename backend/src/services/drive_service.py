"""
Google Drive Service
Gerencia autenticação e operações com Google Drive API
"""

import os
import json
from typing import Any, Dict, List, Optional, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build

from ..config.settings import (
    GOOGLE_SERVICE_ACCOUNT_FILE,
    GOOGLE_SERVICE_ACCOUNT_INFO,
    GOOGLE_SCOPES
)


# Cache global para credenciais (evita reautenticações)
_GOOGLE_CREDENTIALS: Optional[service_account.Credentials] = None


class DriveService:
    """Serviço para interações com Google Drive e Sheets."""
    
    def __init__(self):
        """Inicializa o serviço com credenciais do Google."""
        self.credentials = self._get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials, cache_discovery=False)
        self.sheets_service = build('sheets', 'v4', credentials=self.credentials, cache_discovery=False)
    
    @staticmethod
    def _get_credentials() -> service_account.Credentials:
        """
        Obtém credenciais de serviço para acessar Google Drive e Sheets.
        
        Usa cache global para evitar múltiplas autenticações.
        
        Returns:
            Credenciais autenticadas da service account
        
        Raises:
            RuntimeError: Se as credenciais não estiverem configuradas ou falharem
        """
        global _GOOGLE_CREDENTIALS

        if _GOOGLE_CREDENTIALS is not None:
            return _GOOGLE_CREDENTIALS

        try:
            if GOOGLE_SERVICE_ACCOUNT_INFO:
                # Credenciais via variável de ambiente (JSON string)
                print("[DriveService] 📝 GOOGLE_SERVICE_ACCOUNT_INFO encontrada")
                try:
                    info = json.loads(GOOGLE_SERVICE_ACCOUNT_INFO)
                    print(f"[DriveService] ✅ JSON parseado com sucesso. Project: {info.get('project_id', 'N/A')}")
                except json.JSONDecodeError as json_err:
                    print(f"[DriveService] ❌ Erro ao parsear JSON: {json_err}")
                    print(f"[DriveService] JSON (primeiros 200 chars): {GOOGLE_SERVICE_ACCOUNT_INFO[:200]}")
                    raise
                
                credentials = service_account.Credentials.from_service_account_info(
                    info,
                    scopes=GOOGLE_SCOPES
                )
                print(f"[DriveService] ✅ Credenciais criadas para: {info.get('client_email', 'N/A')}")
            elif GOOGLE_SERVICE_ACCOUNT_FILE:
                # Credenciais via arquivo JSON
                print(f"[DriveService] 📁 Usando arquivo: {GOOGLE_SERVICE_ACCOUNT_FILE}")
                if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
                    raise RuntimeError(
                        f"Arquivo de credenciais não encontrado: {GOOGLE_SERVICE_ACCOUNT_FILE}"
                    )
                credentials = service_account.Credentials.from_service_account_file(
                    GOOGLE_SERVICE_ACCOUNT_FILE,
                    scopes=GOOGLE_SCOPES,
                )
                print("[DriveService] ✅ Credenciais carregadas do arquivo")
            else:
                print("[DriveService] ❌ Nenhuma fonte de credenciais encontrada")
                print(f"[DriveService] GOOGLE_SERVICE_ACCOUNT_INFO: {bool(GOOGLE_SERVICE_ACCOUNT_INFO)}")
                print(f"[DriveService] GOOGLE_SERVICE_ACCOUNT_FILE: {bool(GOOGLE_SERVICE_ACCOUNT_FILE)}")
                raise RuntimeError(
                    "Credenciais não configuradas. Defina GOOGLE_SERVICE_ACCOUNT_FILE com o caminho "
                    "do JSON da service account ou GOOGLE_SERVICE_ACCOUNT_INFO com o conteúdo JSON."
                )
        except json.JSONDecodeError as error:
            raise RuntimeError(f"JSON de credenciais inválido: {error}") from error
        except Exception as error:
            raise RuntimeError(f"Erro ao carregar credenciais do Google: {error}") from error

        _GOOGLE_CREDENTIALS = credentials
        return credentials
    
    def list_folder_files(
        self,
        folder_id: str,
        mime_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista arquivos em uma pasta do Google Drive.
        
        Args:
            folder_id: ID da pasta no Google Drive
            mime_types: Lista de MIME types para filtrar (opcional)
        
        Returns:
            Lista de dicts com metadados dos arquivos (id, name, mimeType)
        
        Raises:
            Exception: Se a pasta não for encontrada ou não houver permissão
        """
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            
            if mime_types:
                mime_query = " or ".join([f"mimeType='{mt}'" for mt in mime_types])
                query += f" and ({mime_query})"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                pageSize=100
            ).execute()
            
            return results.get('files', [])
        
        except Exception as error:
            raise Exception(f"Erro ao listar arquivos da pasta {folder_id}: {error}") from error
    
    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Obtém metadados de um arquivo.
        
        Args:
            file_id: ID do arquivo no Google Drive
        
        Returns:
            Dict com metadados do arquivo
        """
        try:
            return self.drive_service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, createdTime, modifiedTime"
            ).execute()
        except Exception as error:
            raise Exception(f"Erro ao obter metadados do arquivo {file_id}: {error}") from error
    
    def file_exists(self, file_id: str) -> bool:
        """
        Verifica se um arquivo existe e está acessível.
        
        Args:
            file_id: ID do arquivo no Google Drive
        
        Returns:
            True se o arquivo existe e está acessível, False caso contrário
        """
        try:
            self.drive_service.files().get(fileId=file_id, fields="id").execute()
            return True
        except Exception:
            return False
    
    def folder_exists(self, folder_id: str) -> bool:
        """
        Verifica se uma pasta existe e está acessível.
        
        Args:
            folder_id: ID da pasta no Google Drive
        
        Returns:
            True se a pasta existe e está acessível, False caso contrário
        """
        try:
            file = self.drive_service.files().get(
                fileId=folder_id,
                fields="id, mimeType"
            ).execute()
            return file.get('mimeType') == 'application/vnd.google-apps.folder'
        except Exception:
            return False
    
    def get_spreadsheet_data(
        self,
        spreadsheet_id: str,
        range_name: str = 'A1:Z1000'
    ) -> List[List[Any]]:
        """
        Obtém dados de uma planilha do Google Sheets.
        
        Args:
            spreadsheet_id: ID da planilha no Google Sheets
            range_name: Range de células (ex: 'A1:Z1000', 'Sheet1!A1:B10')
        
        Returns:
            Lista de listas contendo os valores das células
        """
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            return result.get('values', [])
        
        except Exception as error:
            raise Exception(
                f"Erro ao obter dados da planilha {spreadsheet_id}: {error}"
            ) from error


def get_drive_service() -> DriveService:
    """
    Factory function para obter instância do DriveService.
    
    Returns:
        Instância configurada do DriveService
    """
    return DriveService()


def get_google_services() -> Tuple[Any, Any]:
    """
    Inicializa clientes do Google Drive e Sheets.
    
    DEPRECATED: Use DriveService() diretamente para melhor encapsulamento.
    
    Returns:
        Tupla (drive_service, sheets_service)
    """
    service = DriveService()
    return service.drive_service, service.sheets_service
