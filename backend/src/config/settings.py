"""
Configurações centralizadas da aplicação Alpha Insights
"""
import os
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# API Keys
DRIVEBOT_API_KEY = os.getenv('DRIVEBOT_API_KEY')
ALPHABOT_API_KEY = os.getenv('ALPHABOT_API_KEY')

# Google Drive Configuration
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
]
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
GOOGLE_SERVICE_ACCOUNT_INFO = os.getenv('GOOGLE_SERVICE_ACCOUNT_INFO')

# Excel MIME Types
EXCEL_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
}

# Conversation Settings
MAX_HISTORY_MESSAGES = 12

# Month Aliases (PT-BR)
MONTH_ALIASES = {
    'janeiro': 1, 'jan': 1,
    'fevereiro': 2, 'fev': 2,
    'março': 3, 'marco': 3, 'mar': 3,
    'abril': 4, 'abr': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9, 'set': 9,
    'outubro': 10, 'out': 10,
    'novembro': 11, 'nov': 11,
    'dezembro': 12, 'dez': 12,
}

MONTH_NAMES_PT = {
    1: 'janeiro', 2: 'fevereiro', 3: 'março',
    4: 'abril', 5: 'maio', 6: 'junho',
    7: 'julho', 8: 'agosto', 9: 'setembro',
    10: 'outubro', 11: 'novembro', 12: 'dezembro',
}

# Month Translation (PT-BR to English)
MONTH_TRANSLATION = {name: datetime(2000, number, 1).strftime('%B') for name, number in MONTH_ALIASES.items()}
