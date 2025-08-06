"""
Módulo ETL para processar DespesaSaldo no DuckDB
Versão atualizada com nova estrutura de campos
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
    """Classe para processar DespesaSaldo no DuckDB com nova estrutura"""
    
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
    
    def drop_table_if_exists(self):
        """Remove a tabela se existir (para recriação completa)"""
        conn = self.db_duckdb.get_connection()
        try:
            # Verificar se tabela existe
            check_query = """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'despesa_saldo'
            """
            exists = conn.execute(check_query).fetchone()[0] > 0
            
            if exists:
                logger.info("🗑️ Removendo tabela despesa_saldo existente...")
                conn.execute("DROP TABLE despesa_saldo")
                logger.info("✅ Tabela removida com sucesso")
            
            return True
        finally:
            conn.close()
    
    def create_table(self):
        """Cria a tabela com a nova estrutura"""
        conn = self.db_duckdb.get_connection()
        try:
            logger.info("📝 Criando tabela despesa_saldo com nova estrutura...")
            
            create_query = """
            CREATE TABLE despesa_saldo (
                coexercicio INTEGER,
                coug INTEGER,
                cogestao INTEGER,
                cocontacontabil BIGINT,
                cocontacorrente VARCHAR(50),
                inmes INTEGER,
                inesfera INTEGER,
                couo INTEGER,
                cofuncao INTEGER,
                cosubfuncao INTEGER,
                coprograma INTEGER,
                coprojeto INTEGER,
                cosubtitulo INTEGER,
                cofonte BIGINT,
                conatureza INTEGER,
                vacredito DECIMAL(18,2),
                vadebito DECIMAL(18,2),
                saldo_contabil_despesa DECIMAL(18,2),
                incategoria VARCHAR(1),
                cogrupo VARCHAR(1),
                comodalidade VARCHAR(2),
                coelemento VARCHAR(2),
                cosubelemento VARCHAR(2),
                periodo VARCHAR(7),
                data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            conn.execute(create_query)
            logger.info("✅ Tabela criada com sucesso")
            
            return True
        finally:
            conn.close()
    
    def analisar_arquivo(self, file_path):
        """Analisa o arquivo Excel e retorna informações"""
        logger.info(f"📖 Analisando arquivo: {file_path}")
        
        try:
            df_sample = pd.read_excel(file_path, nrows=1000)
            
            # Listar colunas encontradas
            logger.info(f"Colunas encontradas: {', '.join(df_sample.columns)}")
            
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
        """Aplica as transformações necessárias com a nova estrutura"""
        df = df.copy()
        
        # Converter tipos e limpar dados - campos obrigatórios
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
        df['vacredito'] = pd.to_numeric(df['VACREDITO'], errors='coerce').fillna(0)
        df['vadebito'] = pd.to_numeric(df['VADEBITO'], errors='coerce').fillna(0)
        
        # Criar coluna periodo
        df['periodo'] = df['coexercicio'].astype(str) + '-' + df['inmes'].astype(str).str.zfill(2)
        
        # Calcular saldo_contabil_despesa baseado no primeiro dígito da conta
        df['primeiro_digito'] = df['cocontacontabil'].str[0]
        df['saldo_contabil_despesa'] = np.where(
            df['primeiro_digito'] == '5',
            df['vadebito'] - df['vacredito'],
            df['vacredito'] - df['vadebito']
        )
        
        # Parse de CONATUREZA (6 dígitos)
        df['conatureza_str'] = df['conatureza'].astype(str).str.zfill(6)
        df['incategoria'] = df['conatureza_str'].str[0:1]    # 1º dígito
        df['cogrupo'] = df['conatureza_str'].str[1:2]        # 2º dígito
        df['comodalidade'] = df['conatureza_str'].str[2:4]   # 3º e 4º dígitos
        df['coelemento'] = df['conatureza_str'].str[4:6]     # 5º e 6º dígitos
        
        # Cosubelemento para contas de 40 chars
        df['tamanho_conta'] = df['cocontacorrente'].str.len()
        df['cosubelemento'] = None
        mask_40 = df['tamanho_conta'] == 40
        if mask_40.any():
            df.loc[mask_40, 'cosubelemento'] = df.loc[mask_40, 'cocontacorrente'].str[38:40]
        
        # Log de debug
        logger.info(f"Transformação concluída: {len(df)} registros")
        logger.info(f"Períodos no chunk: {df['periodo'].unique()}")
        
        # Selecionar colunas finais na ordem correta
        colunas_finais = [
            'coexercicio', 'coug', 'cogestao', 'cocontacontabil', 'cocontacorrente',
            'inmes', 'inesfera', 'couo', 'cofuncao', 'cosubfuncao', 
            'coprograma', 'coprojeto', 'cosubtitulo', 'cofonte', 'conatureza',
            'vacredito', 'vadebito', 'saldo_contabil_despesa',
            'incategoria', 'cogrupo', 'comodalidade', 'coelemento',
            'cosubelemento', 'periodo'
        ]
        
        return df[colunas_finais]
    
    def processar_arquivo(self, file_path, sobrescrever=False, recriar_tabela=False):
        """Processa um arquivo Excel e carrega no DuckDB"""
        logger.info(f"Iniciando processamento: {file_path}")
        inicio = datetime.now()
        
        if not Path(file_path).exists():
            logger.error(f"Arquivo não encontrado: {file_path}")
            return False
        
        # Se recriar_tabela, dropar e criar nova
        if recriar_tabela:
            self.drop_table_if_exists()
            self.create_table()
        
        periodos, total_estimado = self.analisar_arquivo(file_path)
        
        if not periodos:
            logger.error("Nenhum período encontrado no arquivo!")
            return False
        
        logger.info(f"Períodos encontrados: {', '.join(periodos)}")
        logger.info(f"Total estimado: {total_estimado:,} registros")
        
        # Verificar períodos existentes (se não for recriação)
        if not recriar_tabela:
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
            
            # Validar dados carregados
            self.validar_carga(conn)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro geral no processamento: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            conn.close()
    
    def validar_carga(self, conn):
        """Valida os dados carregados"""
        logger.info("\n📊 VALIDAÇÃO DA CARGA:")
        
        try:
            # Total de registros
            total = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]
            logger.info(f"Total de registros: {total:,}")
            
            # Períodos
            periodos = conn.execute(f"""
                SELECT periodo, COUNT(*) as qtd 
                FROM {self.table_name} 
                GROUP BY periodo 
                ORDER BY periodo
            """).fetchall()
            
            logger.info(f"Períodos carregados:")
            for periodo, qtd in periodos:
                logger.info(f"   {periodo}: {qtd:,} registros")
            
            # Validar parse de CONATUREZA
            validacao_natureza = conn.execute(f"""
                SELECT 
                    COUNT(DISTINCT incategoria) as categorias,
                    COUNT(DISTINCT cogrupo) as grupos,
                    COUNT(DISTINCT comodalidade) as modalidades,
                    COUNT(DISTINCT coelemento) as elementos
                FROM {self.table_name}
                WHERE conatureza IS NOT NULL
            """).fetchone()
            
            logger.info(f"Parse de CONATUREZA:")
            logger.info(f"   Categorias únicas: {validacao_natureza[0]}")
            logger.info(f"   Grupos únicos: {validacao_natureza[1]}")
            logger.info(f"   Modalidades únicas: {validacao_natureza[2]}")
            logger.info(f"   Elementos únicos: {validacao_natureza[3]}")
            
            # Contas de 40 caracteres
            contas_40 = conn.execute(f"""
                SELECT COUNT(*) 
                FROM {self.table_name} 
                WHERE LENGTH(cocontacorrente) = 40 
                AND cosubelemento IS NOT NULL
            """).fetchone()[0]
            
            if contas_40 > 0:
                logger.info(f"   Contas com subelemento (40 chars): {contas_40:,}")
            
        except Exception as e:
            logger.error(f"Erro na validação: {e}")