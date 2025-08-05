"""
Módulo ETL para processar DespesaSaldo no DuckDB
"""
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import logging
from app.modules.database_duckdb import db_duckdb

logger = logging.getLogger(__name__)

class ETLDespesaSaldoDuckDB:
    """Classe para processar DespesaSaldo no DuckDB"""
    
    def __init__(self, chunk_size=10000):
        self.chunk_size = chunk_size
        self.table_name = 'despesa_saldo'
        self.db_duckdb = db_duckdb
        
    def validar_periodo_existente(self, periodo):
        """Verifica se um período já foi carregado"""
        conn = self.db_duckdb.get_connection()
        try:
            query = f"SELECT COUNT(*) FROM {self.table_name} WHERE periodo = ?"
            result = conn.execute(query, [periodo]).fetchone()
            return result[0] > 0 if result else False
        finally:
            conn.close()
    
    def deletar_periodo(self, periodo):
        """Remove dados de um período específico"""
        conn = self.db_duckdb.get_connection()
        try:
            count_query = f"SELECT COUNT(*) FROM {self.table_name} WHERE periodo = ?"
            count = conn.execute(count_query, [periodo]).fetchone()[0]
            
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
            df_sample = pd.read_excel(file_path, nrows=1000)
            
            df_sample['periodo'] = (
                df_sample['COEXERCICIO'].astype(str) + '-' + 
                df_sample['INMES'].astype(str).str.zfill(2)
            )
            
            periodos = df_sample['periodo'].unique()
            
            file_size = Path(file_path).stat().st_size
            total_estimado = file_size // 200
            
            return sorted(periodos), total_estimado
            
        except Exception as e:
            logger.error(f"Erro ao analisar arquivo: {e}")
            return [], 0
    
    def transform_data(self, df):
        """Aplica as transformações necessárias"""
        df = df.copy()
        
        # Converter tipos e limpar dados
        df['coexercicio'] = df['COEXERCICIO'].astype(int)
        df['coug'] = df['COUG'].astype(int)
        df['cogestao'] = df['COGESTAO'].astype(int)
        df['cocontacontabil'] = df['COCONTACONTABIL'].astype(str).str.strip()
        df['cocontacorrente'] = df['COCONTACORRENTE'].astype(str).str.strip()
        df['inmes'] = df['INMES'].astype(int)
        df['inesfera'] = df['INESFERA'].astype(int)
        df['couo'] = df['COUO'].astype(int)
        df['cofuncao'] = df['COFUNCAO'].astype(int)
        df['cosubfuncao'] = df['COSUBFUNCAO'].astype(int)
        df['coprograma'] = df['COPROGRAMA'].astype(int)
        df['coprojeto'] = df['COPROJETO'].astype(int)
        df['cosubtitulo'] = df['COSUBTITULO'].astype(int)
        df['cofonte'] = df['COFONTE'].astype(int)
        df['conatureza'] = df['CONATUREZA'].astype(int)
        df['incategoria'] = df['INCATEGORIA'].astype(int)
        df['vacredito'] = pd.to_numeric(df['VACREDITO'], errors='coerce').fillna(0)
        df['vadebito'] = pd.to_numeric(df['VADEBITO'], errors='coerce').fillna(0)
        df['noug'] = df['NOUG'].astype(str) if 'NOUG' in df.columns else ''
        df['cogestao_1'] = df['COGESTAO_1'].astype(int)
        df['nogestao'] = df['NOGESTAO'].astype(str) if 'NOGESTAO' in df.columns else ''
        df['intipoadm'] = df['INTIPOADM'].astype(int)
        df['instatus'] = df['INSTATUS'].astype(int)
        df['ultalteracao'] = df['ULTALTERACAO'].astype(str) if 'ULTALTERACAO' in df.columns else ''
        
        # Criar coluna periodo
        df['periodo'] = df['coexercicio'].astype(str) + '-' + df['inmes'].astype(str).str.zfill(2)
        
        # Calcular saldo_contabil_despesa
        df['primeiro_digito'] = df['cocontacontabil'].str[0]
        df['saldo_contabil_despesa'] = np.where(
            df['primeiro_digito'] == '5',
            df['vadebito'] - df['vacredito'],
            df['vacredito'] - df['vadebito']
        )
        
        # Parse de CONATUREZA
        df['conatureza_str'] = df['conatureza'].astype(str).str.zfill(6)
        df['cogrupo'] = df['conatureza_str'].str[1:2]
        df['comodalidade'] = df['conatureza_str'].str[2:4]
        df['coelemento'] = df['conatureza_str'].str[4:6]
        
        # Cosubelemento para contas de 40 chars
        df['tamanho_conta'] = df['cocontacorrente'].str.len()
        df['cosubelemento'] = None
        mask_40 = df['tamanho_conta'] == 40
        if mask_40.any():
            df.loc[mask_40, 'cosubelemento'] = df.loc[mask_40, 'cocontacorrente'].str[38:40]
        
        # Selecionar colunas finais
        colunas_finais = [
            'coexercicio', 'coug', 'cogestao', 'cocontacontabil', 'cocontacorrente',
            'inmes', 'inesfera', 'couo', 'cofuncao', 'cosubfuncao', 
            'coprograma', 'coprojeto', 'cosubtitulo', 'cofonte', 'conatureza',
            'incategoria', 'vacredito', 'vadebito', 'noug', 'cogestao_1',
            'nogestao', 'intipoadm', 'instatus', 'ultalteracao',
            'saldo_contabil_despesa', 'cogrupo', 'comodalidade', 'coelemento',
            'cosubelemento', 'periodo'
        ]
        
        return df[colunas_finais]
    
    def processar_arquivo(self, file_path, sobrescrever=False):
        """Processa um arquivo Excel e carrega no DuckDB"""
        logger.info(f"Iniciando processamento: {file_path}")
        inicio = datetime.now()
        
        if not Path(file_path).exists():
            logger.error(f"Arquivo não encontrado: {file_path}")
            return False
        
        periodos, total_estimado = self.analisar_arquivo(file_path)
        
        if not periodos:
            logger.error("Nenhum período encontrado no arquivo!")
            return False
        
        logger.info(f"Períodos encontrados: {', '.join(periodos)}")
        logger.info(f"Total estimado: {total_estimado:,} registros")
        
        # Verificar períodos existentes
        periodos_existentes = []
        for periodo in periodos:
            if self.validar_periodo_existente(periodo):
                periodos_existentes.append(periodo)
                logger.warning(f"Período {periodo} já existe no banco!")
        
        if periodos_existentes and not sobrescrever:
            logger.error("Existem períodos já carregados. Use sobrescrever=True para substituir.")
            return False
        
        if periodos_existentes and sobrescrever:
            logger.info("Removendo períodos existentes...")
            for periodo in periodos_existentes:
                self.deletar_periodo(periodo)
        
        # Ler arquivo completo
        logger.info("Lendo arquivo Excel completo...")
        try:
            df_completo = pd.read_excel(file_path, engine='openpyxl')
            total_linhas = len(df_completo)
            logger.info(f"Total de linhas lidas: {total_linhas:,}")
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivo: {e}")
            return False
        
        # Processar e inserir dados
        total_processado = 0
        total_erro = 0
        
        conn = self.db_duckdb.get_connection()
        try:
            with tqdm(total=total_linhas, desc="Processando") as pbar:
                for start in range(0, total_linhas, self.chunk_size):
                    end = min(start + self.chunk_size, total_linhas)
                    chunk = df_completo.iloc[start:end]
                    
                    try:
                        chunk_transformado = self.transform_data(chunk)
                        
                        # Inserir no DuckDB
                        colunas = list(chunk_transformado.columns)
                        colunas_str = ', '.join(colunas)
                        
                        conn.register('chunk_df', chunk_transformado)
                        conn.execute(f"""
                            INSERT INTO {self.table_name} ({colunas_str})
                            SELECT {colunas_str} FROM chunk_df
                        """)
                        conn.unregister('chunk_df')
                        
                        total_processado += len(chunk)
                        pbar.update(len(chunk))
                        
                    except Exception as e:
                        logger.error(f"Erro no chunk {start//self.chunk_size + 1}: {e}")
                        total_erro += len(chunk)
                        pbar.update(len(chunk))
            
            count = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]
            logger.info(f"✅ Total no banco: {count:,} registros")
            
            tempo_total = datetime.now() - inicio
            logger.info(f"✅ Processamento concluído em {tempo_total}")
            logger.info(f"   - Registros processados: {total_processado:,}")
            logger.info(f"   - Registros com erro: {total_erro:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro geral no processamento: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            conn.close()