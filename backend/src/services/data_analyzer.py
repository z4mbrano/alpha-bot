"""
Data Analyzer Service
Gerencia análise e sumarização de dados
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from ..utils.data_processors import prepare_table
from ..utils.file_handlers import load_csv_tables, load_excel_tables, load_from_bytes


class DataAnalyzer:
    """Serviço para análise e consolidação de dados de múltiplas fontes."""
    
    def __init__(self):
        """Inicializa o analisador de dados."""
        self.tables: List[Dict[str, Any]] = []
        self.consolidated_df: Optional[pd.DataFrame] = None
        self.summary: Optional[Dict[str, Any]] = None
    
    def load_files_from_drive(
        self,
        drive_service: Any,
        file_metas: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Carrega e processa arquivos do Google Drive.
        
        Args:
            drive_service: Instância do serviço do Google Drive
            file_metas: Lista de metadados dos arquivos
        
        Returns:
            Dict com resumo do carregamento (files_ok, files_failed, tables)
        """
        files_ok: List[str] = []
        files_failed: List[Dict[str, str]] = []
        
        for file_meta in file_metas:
            try:
                mime_type = file_meta.get('mimeType', '')
                
                if 'spreadsheet' in mime_type or mime_type == 'text/csv':
                    if mime_type == 'text/csv':
                        tables = load_csv_tables(drive_service, file_meta)
                    else:
                        tables = load_excel_tables(drive_service, file_meta)
                    
                    self.tables.extend(tables)
                    files_ok.append(file_meta['name'])
                else:
                    files_failed.append({
                        'name': file_meta['name'],
                        'reason': f"Formato não suportado: {mime_type}"
                    })
            
            except Exception as error:
                files_failed.append({
                    'name': file_meta['name'],
                    'reason': str(error)
                })
        
        return {
            'files_ok': files_ok,
            'files_failed': files_failed,
            'tables': self.tables
        }
    
    def load_files_from_bytes(
        self,
        files_data: List[Tuple[bytes, str]]
    ) -> Dict[str, Any]:
        """
        Carrega arquivos a partir de bytes (para upload direto).
        
        Args:
            files_data: Lista de tuplas (file_bytes, filename)
        
        Returns:
            Dict com resumo do carregamento
        """
        files_ok: List[str] = []
        files_failed: List[Dict[str, str]] = []
        
        for file_bytes, filename in files_data:
            try:
                tables = load_from_bytes(file_bytes, filename)
                self.tables.extend(tables)
                files_ok.append(filename)
            
            except Exception as error:
                files_failed.append({
                    'name': filename,
                    'reason': str(error)
                })
        
        return {
            'files_ok': files_ok,
            'files_failed': files_failed,
            'tables': self.tables
        }
    
    def consolidate_tables(self) -> pd.DataFrame:
        """
        Consolida todas as tabelas carregadas em um único DataFrame.
        
        Returns:
            DataFrame consolidado
        
        Raises:
            ValueError: Se não houver tabelas carregadas
        """
        if not self.tables:
            raise ValueError("Nenhuma tabela carregada para consolidar")
        
        dfs = [table['df'] for table in self.tables]
        self.consolidated_df = pd.concat(dfs, ignore_index=True)
        
        return self.consolidated_df
    
    def build_summary(
        self,
        files_ok: List[str],
        files_failed: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Constrói sumário dos dados carregados.
        
        Args:
            files_ok: Lista de arquivos carregados com sucesso
            files_failed: Lista de arquivos que falharam
        
        Returns:
            Dict com sumário completo
        """
        total_records = sum(table['row_count'] for table in self.tables)
        all_columns = set()
        numeric_columns = set()
        text_columns = set()
        datetime_columns_names = set()
        start_dates: List[pd.Timestamp] = []
        end_dates: List[pd.Timestamp] = []

        for table in self.tables:
            all_columns.update(table['columns'])
            numeric_columns.update(table['numeric_columns'])
            text_columns.update(table['text_columns'])
            datetime_columns_names.update(table['datetime_columns'].keys())

            for parsed in table['datetime_columns'].values():
                valid = parsed.dropna()
                if not valid.empty:
                    start_dates.append(valid.min())
                    end_dates.append(valid.max())

        if start_dates and end_dates:
            date_range: Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]] = (
                min(start_dates),
                max(end_dates),
            )
        else:
            date_range = (None, None)

        domains: List[str] = []
        if numeric_columns:
            domains.append('numérico')
        if text_columns:
            domains.append('categórico')
        if datetime_columns_names:
            domains.append('temporal')

        self.summary = {
            'files_ok': files_ok,
            'files_failed': files_failed,
            'total_records': int(total_records),
            'columns': sorted(filter(None, all_columns)),
            'numeric_columns': sorted(numeric_columns),
            'text_columns': sorted(text_columns),
            'datetime_columns': sorted(datetime_columns_names),
            'date_range': date_range,
            'domains': domains,
        }
        
        return self.summary
    
    @staticmethod
    def format_date(date_value: Optional[pd.Timestamp]) -> Optional[str]:
        """
        Formata um timestamp para string DD/MM/YYYY.
        
        Args:
            date_value: Timestamp do pandas
        
        Returns:
            String formatada ou None
        """
        if date_value is None or (isinstance(date_value, float) and np.isnan(date_value)):
            return None
        try:
            timestamp = pd.to_datetime(date_value)
        except Exception:
            return None
        if pd.isna(timestamp):
            return None
        return timestamp.strftime('%d/%m/%Y')
    
    def build_discovery_report(self, summary: Optional[Dict[str, Any]] = None) -> str:
        """
        Constrói relatório markdown de descoberta dos dados.
        
        Args:
            summary: Sumário dos dados (usa self.summary se não fornecido)
        
        Returns:
            String markdown com o relatório formatado
        """
        if summary is None:
            summary = self.summary
        
        if not summary:
            raise ValueError("Sumário não disponível. Execute build_summary() primeiro.")
        
        files_ok = summary['files_ok']
        files_failed = summary['files_failed']
        date_range = summary['date_range']

        files_ok_md = '\n'.join(f"- {name}" for name in files_ok) or '- Nenhum arquivo processado.'
        files_failed_md = '\n'.join(
            f"- {entry['name']} (Motivo: {entry['reason']})" for entry in files_failed
        ) or '- Nenhum arquivo com falha.'

        start_text = self.format_date(date_range[0])
        end_text = self.format_date(date_range[1])
        if start_text and end_text:
            period_text = f"{start_text} até {end_text}"
        elif start_text or end_text:
            period_text = start_text or end_text
        else:
            period_text = 'Não identificado'

        numeric_cols_md = ', '.join(f"`{col}`" for col in summary['numeric_columns']) or 'Nenhum'
        text_cols_md = ', '.join(f"`{col}`" for col in summary['text_columns']) or 'Nenhum'
        
        # Diagnóstico de colunas temporais
        datetime_cols = summary.get('datetime_columns', [])
        if datetime_cols:
            datetime_cols_md = ', '.join(f"`{col}`" for col in datetime_cols)
            datetime_status = f"""#### 📅 Campos Temporais (Análises de Evolução)
**Status da Conversão de Datas:**
- **✅ Conversão Bem-Sucedida:** {datetime_cols_md}
  - **Capacidades:** Filtros por ano, mês, trimestre, período, evolução temporal
"""
        else:
            datetime_status = """#### 📅 Campos Temporais
**Status:** Nenhuma coluna temporal detectada
- Análises de evolução temporal não estão disponíveis neste dataset
"""

        can_temporal = "✅" if datetime_cols else "❌"

        return f"""## 🔍 Descoberta e Diagnóstico Completo

**Status:** Leitura, processamento e diagnóstico finalizados ✅

### 📁 Arquivos Processados com Sucesso
{files_ok_md}

### ⚠️ Arquivos Ignorados/Com Falha
{files_failed_md}

---

### 🗺️ MAPA DO ECOSSISTEMA DE DADOS

**Registros Totais Consolidados:** {summary['total_records']}

**Período Identificado:** {period_text}

---

### 🔬 DIAGNÓSTICO DE QUALIDADE POR TIPO

#### 💰 Campos Numéricos (Análises Quantitativas)
**Prontos para:** soma, média, mínimo, máximo, contagem

{numeric_cols_md}

#### 📝 Campos Categóricos (Agrupamentos e Filtros)
**Prontos para:** agrupamento, ranking, filtros

{text_cols_md}

{datetime_status}

---

### 🎯 CAPACIDADES ANALÍTICAS DISPONÍVEIS

Com base no diagnóstico acima, **posso responder perguntas sobre:**

✅ **Totalizações:** Soma, média, contagem nos campos numéricos
✅ **Rankings:** Top N por qualquer campo categórico
✅ **Filtros:** Por categorias disponíveis
{can_temporal} **Análises Temporais:** Evolução, comparação de períodos
✅ **Comparações:** Entre categorias
✅ **Detalhamento:** Drill-down em registros específicos

---

**Status:** Ecossistema mapeado. Pronto para análises investigativas. 🚀
"""
    
    def get_column_info(self, column_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações sobre uma coluna específica.
        
        Args:
            column_name: Nome da coluna
        
        Returns:
            Dict com info da coluna ou None se não encontrada
        """
        if not self.consolidated_df is not None:
            return None
        
        if column_name not in self.consolidated_df.columns:
            return None
        
        series = self.consolidated_df[column_name]
        
        info = {
            'name': column_name,
            'dtype': str(series.dtype),
            'count': int(series.count()),
            'null_count': int(series.isnull().sum()),
            'unique_count': int(series.nunique()),
        }
        
        if pd.api.types.is_numeric_dtype(series):
            info.update({
                'min': float(series.min()) if not series.empty else None,
                'max': float(series.max()) if not series.empty else None,
                'mean': float(series.mean()) if not series.empty else None,
                'median': float(series.median()) if not series.empty else None,
            })
        
        return info


def get_data_analyzer() -> DataAnalyzer:
    """
    Factory function para obter instância do DataAnalyzer.
    
    Returns:
        Instância do DataAnalyzer
    """
    return DataAnalyzer()
