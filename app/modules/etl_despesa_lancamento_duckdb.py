"""
Módulo ETL para processar DespesaLancamento no DuckDB
Baseado no etl_despesa_lancamento.py original
"""
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import logging
from app.modules.etl_lancamento_duckdb import ETLLancamentoDuckDB
from app.modules.database_duckdb import db_duckdb

logger = logging.getLogger(__name__)

class ETLDespesaLancamentoDuckDB(ETLLancamentoDuckDB):
    """Classe para processar DespesaLancamento no DuckDB"""
    
    def __init__(self, chunk_size=50000):  # Chunks maiores para despesa
        super().__init__(tipo_lancamento='despesa', chunk_size=chunk_size)
    
    def transform_data(self, df):
        """Aplica as transformações necessárias"""
        # Criar cópia para não modificar o original
        df = df.copy()
        
        # Converter tipos e limpar dados
        df['coexercicio'] = df['COEXERCICIO'].astype(int)
        df['coug'] = df['COUG'].astype(int)
        df['cogestao'] = df['COGESTAO'].astype(int)
        df['nudocumento'] = df['NUDOCUMENTO'].astype(str).str.strip()
        df['nulancamento'] = df['NULANCAMENTO'].astype(int)
        df['coevento'] = df['COEVENTO'].astype(int)
        df['cocontacontabil'] = df['COCONTACONTABIL'].astype(str).str.strip()
        
        # IMPORTANTE: Limpar espaços em branco do COCONTACORRENTE
        df['cocontacorrente'] = df['COCONTACORRENTE'].astype(str).str.strip()
        
        df['inmes'] = df['INMES'].astype(int)
        df['dalancamento'] = pd.to_datetime(df['DALANCAMENTO'])
        df['valancamento'] = pd.to_numeric(df['VALANCAMENTO'], errors='coerce').fillna(0)
        df['indebitocredito'] = df['INDEBITOCREDITO'].astype(str).str.strip()
        df['inabreencerra'] = df['INABREENCERRA'].astype(int)
        df['cougdestino'] = df['COUGDESTINO'].astype(int)
        df['cogestaodestino'] = df['COGESTAODESTINO'].astype(int)
        df['datransacao'] = pd.to_datetime(df['DATRANSACAO'])
        df['hotransacao'] = df['HOTRANSACAO'].astype(str).str.strip()
        df['cougcontab'] = df['COUGCONTAB'].astype(int)
        df['cogestaocontab'] = df['COGESTAOCONTAB'].astype(int)
        
        # Criar coluna periodo (YYYY-MM)
        df['periodo'] = df['coexercicio'].astype(str) + '-' + df['inmes'].astype(str).str.zfill(2)
        
        # Criar coluna tipo_lancamento baseado em INDEBITOCREDITO
        df['tipo_lancamento'] = df['indebitocredito'].map({'D': 'DEBITO', 'C': 'CREDITO'}).fillna('INDEFINIDO')
        
        # Tamanho REAL da conta corrente (após strip)
        df['tamanho_conta'] = df['cocontacorrente'].str.len()
        
        # Inicializar todas as colunas derivadas com None
        colunas_derivadas = [
            'inesfera', 'couo', 'cofuncao', 'cosubfuncao', 'coprograma', 
            'coprojeto', 'cosubtitulo', 'cofonte', 'conatureza', 'incategoria', 
            'cogrupo', 'comodalidade', 'coelemento', 'cosubelemento'
        ]
        for col in colunas_derivadas:
            df[col] = None
        
        # Parse para contas de 38 caracteres
        mask_38 = df['tamanho_conta'] == 38
        if mask_38.any():
            df.loc[mask_38, 'inesfera'] = df.loc[mask_38, 'cocontacorrente'].str[0:1]
            df.loc[mask_38, 'couo'] = df.loc[mask_38, 'cocontacorrente'].str[1:6]
            df.loc[mask_38, 'cofuncao'] = df.loc[mask_38, 'cocontacorrente'].str[6:8]
            df.loc[mask_38, 'cosubfuncao'] = df.loc[mask_38, 'cocontacorrente'].str[8:11]
            df.loc[mask_38, 'coprograma'] = df.loc[mask_38, 'cocontacorrente'].str[11:15]
            df.loc[mask_38, 'coprojeto'] = df.loc[mask_38, 'cocontacorrente'].str[15:19]
            df.loc[mask_38, 'cosubtitulo'] = df.loc[mask_38, 'cocontacorrente'].str[19:23]
            df.loc[mask_38, 'cofonte'] = df.loc[mask_38, 'cocontacorrente'].str[23:32]
            df.loc[mask_38, 'conatureza'] = df.loc[mask_38, 'cocontacorrente'].str[32:38]
            df.loc[mask_38, 'incategoria'] = df.loc[mask_38, 'cocontacorrente'].str[32:33]
            df.loc[mask_38, 'cogrupo'] = df.loc[mask_38, 'cocontacorrente'].str[33:34]
            df.loc[mask_38, 'comodalidade'] = df.loc[mask_38, 'cocontacorrente'].str[34:36]
            df.loc[mask_38, 'coelemento'] = df.loc[mask_38, 'cocontacorrente'].str[36:38]
        
        # Parse para contas de 40 caracteres
        mask_40 = df['tamanho_conta'] == 40
        if mask_40.any():
            # Aplicar mesmo parse das contas de 38 chars
            df.loc[mask_40, 'inesfera'] = df.loc[mask_40, 'cocontacorrente'].str[0:1]
            df.loc[mask_40, 'couo'] = df.loc[mask_40, 'cocontacorrente'].str[1:6]
            df.loc[mask_40, 'cofuncao'] = df.loc[mask_40, 'cocontacorrente'].str[6:8]
            df.loc[mask_40, 'cosubfuncao'] = df.loc[mask_40, 'cocontacorrente'].str[8:11]
            df.loc[mask_40, 'coprograma'] = df.loc[mask_40, 'cocontacorrente'].str[11:15]
            df.loc[mask_40, 'coprojeto'] = df.loc[mask_40, 'cocontacorrente'].str[15:19]
            df.loc[mask_40, 'cosubtitulo'] = df.loc[mask_40, 'cocontacorrente'].str[19:23]
            df.loc[mask_40, 'cofonte'] = df.loc[mask_40, 'cocontacorrente'].str[23:32]
            df.loc[mask_40, 'conatureza'] = df.loc[mask_40, 'cocontacorrente'].str[32:38]
            df.loc[mask_40, 'incategoria'] = df.loc[mask_40, 'cocontacorrente'].str[32:33]
            df.loc[mask_40, 'cogrupo'] = df.loc[mask_40, 'cocontacorrente'].str[33:34]
            df.loc[mask_40, 'comodalidade'] = df.loc[mask_40, 'cocontacorrente'].str[34:36]
            df.loc[mask_40, 'coelemento'] = df.loc[mask_40, 'cocontacorrente'].str[36:38]
            # Campo especial subelemento (caracteres 39-40)
            df.loc[mask_40, 'cosubelemento'] = df.loc[mask_40, 'cocontacorrente'].str[38:40]
        
        # Log de debug para verificar distribuição de tamanhos
        tamanhos_unicos = df['tamanho_conta'].value_counts()
        logger.info(f"Distribuição de tamanhos de COCONTACORRENTE no chunk:")
        for tam, qtd in tamanhos_unicos.items():
            logger.info(f"   {tam} chars: {qtd} registros")
        
        # Selecionar apenas as colunas finais necessárias
        colunas_finais = self.get_colunas_insert()
        
        return df[colunas_finais]
    
    def processar_arquivo(self, file_path, sobrescrever=False):
        """Processa um arquivo Excel e carrega no DuckDB"""
        logger.info(f"Iniciando processamento: {file_path}")
        inicio = datetime.now()
        
        # Verificar se arquivo existe
        if not Path(file_path).exists():
            logger.error(f"Arquivo não encontrado: {file_path}")
            return False
        
        # Analisar arquivo
        periodos, total_estimado = self.analisar_arquivo(file_path)
        
        if not periodos:
            logger.error("Nenhum período encontrado no arquivo!")
            return False
        
        logger.info(f"Períodos encontrados: {', '.join(periodos)}")
        logger.info(f"Total estimado: {total_estimado:,} registros")
        
        # Aviso para arquivos grandes
        if total_estimado > 500000:
            logger.warning(f"⚠️ ARQUIVO GRANDE! Processamento pode demorar 10-20 minutos")
        
        # Verificar períodos existentes
        periodos_existentes = []
        for periodo in periodos:
            if self.validar_periodo_existente(periodo):
                periodos_existentes.append(periodo)
                logger.warning(f"Período {periodo} já existe no banco!")
        
        # Se tem períodos existentes e não quer sobrescrever
        if periodos_existentes and not sobrescrever:
            logger.error("Existem períodos já carregados. Use sobrescrever=True para substituir.")
            return False
        
        # Deletar períodos existentes se necessário
        if periodos_existentes and sobrescrever:
            logger.info("Removendo períodos existentes...")
            for periodo in periodos_existentes:
                self.deletar_periodo(periodo)
        
        # Ler arquivo completo
        logger.info("Lendo arquivo Excel completo (pode demorar para arquivos grandes)...")
        try:
            df_completo = pd.read_excel(file_path, engine='openpyxl')
            total_linhas = len(df_completo)
            logger.info(f"Total de linhas lidas: {total_linhas:,}")
            
            # Validar colunas
            self.validar_colunas_obrigatorias(df_completo)
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivo: {e}")
            return False
        
        # Processar e inserir dados
        total_processado = 0
        total_erro = 0
        
        conn = db_duckdb.get_connection()
        try:
            # Processar em chunks
            with tqdm(total=total_linhas, desc="Processando") as pbar:
                for start in range(0, total_linhas, self.chunk_size):
                    end = min(start + self.chunk_size, total_linhas)
                    chunk = df_completo.iloc[start:end]
                    
                    try:
                        # Transformar dados
                        chunk_transformado = self.transform_data(chunk)
                        
                        # Inserir no DuckDB
                        colunas = self.get_colunas_insert()
                        colunas_str = ', '.join(colunas)
                        
                        conn.register('chunk_df', chunk_transformado)
                        conn.execute(f"""
                            INSERT INTO {self.table_name} ({colunas_str})
                            SELECT {colunas_str} FROM chunk_df
                        """)
                        conn.unregister('chunk_df')
                        
                        total_processado += len(chunk)
                        pbar.update(len(chunk))
                        
                        # Log a cada 200k registros
                        if total_processado % 200000 == 0:
                            logger.info(f"   Processados: {total_processado:,} registros")
                        
                    except Exception as e:
                        logger.error(f"Erro no chunk {start//self.chunk_size + 1}: {e}")
                        total_erro += len(chunk)
                        pbar.update(len(chunk))
            
            # Verificar total inserido
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

def validar_carga():
    """Valida os dados carregados"""
    conn = db_duckdb.get_connection()
    try:
        query = """
        SELECT 
            COUNT(*) as total_registros,
            COUNT(DISTINCT periodo) as periodos_distintos,
            MIN(periodo) as primeiro_periodo,
            MAX(periodo) as ultimo_periodo,
            SUM(valancamento) as total_lancamentos,
            COUNT(CASE WHEN tipo_lancamento = 'DEBITO' THEN 1 END) as total_debitos,
            COUNT(CASE WHEN tipo_lancamento = 'CREDITO' THEN 1 END) as total_creditos,
            COUNT(DISTINCT nudocumento) as documentos_unicos,
            COUNT(DISTINCT coug) as ugs_distintas,
            COUNT(DISTINCT coevento) as eventos_distintos,
            COUNT(CASE WHEN LENGTH(cocontacorrente) = 38 THEN 1 END) as contas_38_chars,
            COUNT(CASE WHEN LENGTH(cocontacorrente) = 40 THEN 1 END) as contas_40_chars,
            COUNT(CASE WHEN LENGTH(cocontacorrente) NOT IN (38, 40) THEN 1 END) as contas_outros_tamanhos
        FROM despesa_lancamento
        """
        
        result = conn.execute(query).fetchone()
        if result:
            print("\n📊 VALIDAÇÃO DOS DADOS CARREGADOS:")
            print(f"   Total de registros: {result[0]:,}")
            print(f"   Períodos distintos: {result[1]}")
            print(f"   Período inicial: {result[2]}")
            print(f"   Período final: {result[3]}")
            print(f"   Total lançamentos: R$ {result[4]:,.2f}")
            print(f"   Total débitos: {result[5]:,}")
            print(f"   Total créditos: {result[6]:,}")
            print(f"   Documentos únicos: {result[7]:,}")
            print(f"   UGs distintas: {result[8]}")
            print(f"   Eventos distintos: {result[9]}")
            print(f"   Contas com 38 caracteres: {result[10]:,}")
            print(f"   Contas com 40 caracteres: {result[11]:,}")
            print(f"   Contas com outros tamanhos: {result[12]:,}")
            
    except Exception as e:
        logger.error(f"Erro na validação: {e}")
    finally:
        conn.close()