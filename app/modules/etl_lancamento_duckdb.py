"""
Módulo ETL base para processar lançamentos no DuckDB
"""
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import logging
from app.modules.database_duckdb import db_duckdb

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETLLancamentoDuckDB:
    """Classe base para processar lançamentos no DuckDB"""
    
    def __init__(self, tipo_lancamento='receita', chunk_size=10000):
        self.tipo_lancamento = tipo_lancamento
        self.chunk_size = chunk_size
        self.table_name = f"{tipo_lancamento}_lancamento"
        
    def validar_periodo_existente(self, periodo):
        """Verifica se um período já foi carregado"""
        conn = db_duckdb.get_connection()
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE periodo = ?"
            result = conn.execute(query, [periodo]).fetchone()
            return result[0] > 0 if result else False
        finally:
            conn.close()
    
    def deletar_periodo(self, periodo):
        """Remove dados de um período específico"""
        conn = db_duckdb.get_connection()
        try:
            # Contar registros antes
            count_query = f"SELECT COUNT(*) FROM {self.table_name} WHERE periodo = ?"
            count = conn.execute(count_query, [periodo]).fetchone()[0]
            
            # Deletar
            delete_query = f"DELETE FROM {self.table_name} WHERE periodo = ?"
            conn.execute(delete_query, [periodo])
            
            logger.info(f"✅ Removidos {count:,} registros do período {periodo}")
            return count
        finally:
            conn.close()
    
    def analisar_arquivo(self, file_path):
        """Analisa o arquivo Excel e retorna informações"""
        logger.info(f"📖 Analisando arquivo: {file_path}")
        
        try:
            # Ler amostra
            df_sample = pd.read_excel(file_path, nrows=1000)
            
            # Criar período
            df_sample['periodo'] = (
                df_sample['COEXERCICIO'].astype(str) + '-' + 
                df_sample['INMES'].astype(str).str.zfill(2)
            )
            
            # Períodos únicos
            periodos = df_sample['periodo'].unique()
            
            # Estimar total (baseado no tamanho do arquivo)
            file_size = Path(file_path).stat().st_size
            # ~200 bytes por linha em Excel
            total_estimado = file_size // 200
            
            return sorted(periodos), total_estimado
            
        except Exception as e:
            logger.error(f"Erro ao analisar arquivo: {e}")
            return [], 0
    
    def validar_colunas_obrigatorias(self, df):
        """Valida se o DataFrame tem todas as colunas obrigatórias"""
        colunas_obrigatorias = [
            'COEXERCICIO', 'COUG', 'NUDOCUMENTO', 'NULANCAMENTO',
            'COCONTACORRENTE', 'INMES', 'DALANCAMENTO', 'VALANCAMENTO',
            'INDEBITOCREDITO'
        ]
        
        colunas_faltando = [col for col in colunas_obrigatorias if col not in df.columns]
        
        if colunas_faltando:
            raise ValueError(f"Colunas obrigatórias faltando: {colunas_faltando}")
        
        return True
    
    def get_colunas_insert(self):
        """Retorna lista de colunas para INSERT (sem data_carga)"""
        if self.tipo_lancamento == 'receita':
            return [
                'coexercicio', 'coug', 'cogestao', 'nudocumento', 'nulancamento',
                'coevento', 'cocontacontabil', 'cocontacorrente', 'inmes',
                'dalancamento', 'valancamento', 'indebitocredito', 'inabreencerra',
                'cougdestino', 'cogestaodestino', 'datransacao', 'hotransacao',
                'cougcontab', 'cogestaocontab', 'coclasseorc', 'cofonte',
                'cocategoriareceita', 'cofontereceita', 'cosubfontereceita',
                'corubrica', 'coalinea', 'inesfera', 'couo', 'cofuncao',
                'cosubfuncao', 'coprograma', 'coprojeto', 'cosubtitulo',
                'conatureza', 'incategoria', 'cogrupo', 'comodalidade',
                'coelemento', 'cosubelemento', 'periodo', 'tipo_lancamento'
            ]
        else:  # despesa
            return [
                'coexercicio', 'coug', 'cogestao', 'nudocumento', 'nulancamento',
                'coevento', 'cocontacontabil', 'cocontacorrente', 'inmes',
                'dalancamento', 'valancamento', 'indebitocredito', 'inabreencerra',
                'cougdestino', 'cogestaodestino', 'datransacao', 'hotransacao',
                'cougcontab', 'cogestaocontab', 'inesfera', 'couo', 'cofuncao',
                'cosubfuncao', 'coprograma', 'coprojeto', 'cosubtitulo', 'cofonte',
                'conatureza', 'incategoria', 'cogrupo', 'comodalidade', 'coelemento',
                'cosubelemento', 'periodo', 'tipo_lancamento'
            ]
    
    def processar_arquivo(self, file_path, sobrescrever=False):
        """Processa um arquivo Excel e carrega no DuckDB"""
        raise NotImplementedError("Deve ser implementado nas classes filhas")