"""
Módulo ETL para processar DespesaSaldo.xlsx
"""
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import logging
from app.modules.database import db

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ETLDespesaSaldo:
    """Classe para processar o arquivo DespesaSaldo.xlsx"""
    
    def __init__(self, chunk_size=10000):
        self.chunk_size = chunk_size
        self.table_name = 'fato_despesa_saldo'
        self.schema_name = 'despesas'
        self.full_table_name = f'{self.schema_name}.{self.table_name}'
        
    def drop_table(self):
        """Remove a tabela se existir"""
        logger.info(f"Removendo tabela {self.full_table_name} se existir...")
        try:
            db.execute_ddl(f"DROP TABLE IF EXISTS {self.full_table_name} CASCADE")
            logger.info("✅ Tabela removida com sucesso!")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao remover tabela: {e}")
            return False
        
    def create_table(self):
        """Cria a tabela no banco de dados"""
        logger.info("Criando tabela fato_despesa_saldo...")
        
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.full_table_name} (
            -- Colunas originais
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
            incategoria INTEGER,
            vacredito DECIMAL(18,2),
            vadebito DECIMAL(18,2),
            noug VARCHAR(255),
            cogestao_1 INTEGER,
            nogestao VARCHAR(255),
            intipoadm INTEGER,
            instatus INTEGER,
            ultalteracao VARCHAR(50),
            
            -- Coluna calculada
            saldo_contabil_despesa DECIMAL(18,2),
            
            -- Colunas derivadas de CONATUREZA
            cogrupo VARCHAR(1),
            comodalidade VARCHAR(2),
            coelemento VARCHAR(2),
            
            -- Coluna especial de COCONTACORRENTE
            cosubelemento VARCHAR(2),
            
            -- Metadados
            periodo VARCHAR(7), -- YYYY-MM
            data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Índices
            PRIMARY KEY (coexercicio, inmes, coug, cocontacontabil, cocontacorrente)
        );
        
        -- Criar índices para performance
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_periodo 
            ON {self.full_table_name}(periodo);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_conta_contabil 
            ON {self.full_table_name}(cocontacontabil);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_exercicio_mes 
            ON {self.full_table_name}(coexercicio, inmes);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_ug
            ON {self.full_table_name}(coug);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_natureza
            ON {self.full_table_name}(conatureza);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_fonte
            ON {self.full_table_name}(cofonte);
        """
        
        try:
            db.execute_ddl(sql)
            logger.info("✅ Tabela criada com sucesso!")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao criar tabela: {e}")
            return False
    
    def transform_data(self, df):
        """Aplica as transformações necessárias"""
        # Criar cópia para não modificar o original
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
        
        # Criar coluna periodo (YYYY-MM)
        df['periodo'] = df['coexercicio'].astype(str) + '-' + df['inmes'].astype(str).str.zfill(2)
        
        # Calcular saldo_contabil_despesa baseado no primeiro dígito
        df['primeiro_digito'] = df['cocontacontabil'].str[0]
        df['saldo_contabil_despesa'] = np.where(
            df['primeiro_digito'] == '5',
            df['vadebito'] - df['vacredito'],  # Se começar com 5
            df['vacredito'] - df['vadebito']   # Se começar com 6 ou outro
        )
        
        # Parse de CONATUREZA (6 dígitos)
        df['conatureza_str'] = df['conatureza'].astype(str).str.zfill(6)
        df['cogrupo'] = df['conatureza_str'].str[1:2]  # 2º caracter
        df['comodalidade'] = df['conatureza_str'].str[2:4]  # 3º e 4º caracteres
        df['coelemento'] = df['conatureza_str'].str[4:6]  # 5º e 6º caracteres
        
        # Tamanho da conta corrente
        df['tamanho_conta'] = df['cocontacorrente'].str.len()
        
        # Coluna especial cosubelemento
        df['cosubelemento'] = None
        mask_40 = df['tamanho_conta'] == 40
        if mask_40.any():
            df.loc[mask_40, 'cosubelemento'] = df.loc[mask_40, 'cocontacorrente'].str[38:40]
        
        # Selecionar apenas as colunas finais necessárias
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
    
    def process_file(self, file_path, tipo_carga='inicial', recriar_tabela=False):
        """Processa o arquivo Excel em chunks"""
        logger.info(f"Iniciando processamento: {file_path}")
        inicio = datetime.now()
        
        # Verificar se arquivo existe
        if not Path(file_path).exists():
            logger.error(f"Arquivo não encontrado: {file_path}")
            return False
        
        # Recriar tabela se solicitado
        if recriar_tabela:
            self.drop_table()
        
        # Criar tabela se não existir
        if not self.create_table():
            return False
        
        # Se for carga inicial, limpar tabela
        if tipo_carga == 'inicial':
            logger.info("Limpando tabela para carga inicial...")
            db.execute_ddl(f"TRUNCATE TABLE {self.full_table_name}")
        
        # Ler arquivo completo
        total_processado = 0
        total_erro = 0
        
        try:
            # Ler todo o arquivo
            logger.info("Lendo arquivo Excel... (pode demorar devido ao tamanho)")
            df_completo = pd.read_excel(file_path)
            total_linhas = len(df_completo)
            logger.info(f"Total de linhas a processar: {total_linhas:,}")
            
            # Processar em chunks manualmente
            with tqdm(total=total_linhas, desc="Processando") as pbar:
                for start in range(0, total_linhas, self.chunk_size):
                    end = min(start + self.chunk_size, total_linhas)
                    chunk = df_completo.iloc[start:end]
                    chunk_num = start // self.chunk_size + 1
                    
                    try:
                        # Transformar dados
                        chunk_transformado = self.transform_data(chunk)
                        
                        # Salvar no banco
                        chunk_transformado.to_sql(
                            name=self.table_name,
                            schema=self.schema_name,
                            con=db.engine,
                            if_exists='append',
                            index=False,
                            method='multi'
                        )
                        
                        total_processado += len(chunk)
                        pbar.update(len(chunk))
                        
                    except Exception as e:
                        logger.error(f"Erro no chunk {chunk_num}: {e}")
                        total_erro += len(chunk)
                        pbar.update(len(chunk))
            
            # Registrar no controle ETL
            self._registrar_carga(
                tipo_carga=tipo_carga,
                registros_inseridos=total_processado,
                registros_erro=total_erro,
                arquivo_origem=str(file_path),
                tempo_processamento=(datetime.now() - inicio)
            )
            
            logger.info(f"✅ Processamento concluído!")
            logger.info(f"   - Registros processados: {total_processado:,}")
            logger.info(f"   - Registros com erro: {total_erro:,}")
            logger.info(f"   - Tempo total: {datetime.now() - inicio}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro geral no processamento: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _registrar_carga(self, tipo_carga, registros_inseridos, registros_erro, 
                        arquivo_origem, tempo_processamento):
        """Registra a carga nas tabelas de controle"""
        try:
            # Obter período dos dados
            query = f"""
            SELECT MIN(periodo), MAX(periodo) 
            FROM {self.full_table_name}
            """
            result = db.execute_query(query)
            periodo_min = result[0][0] if result and result[0][0] else 'N/A'
            periodo_max = result[0][1] if result and result[0][1] else 'N/A'
            
            # Se períodos iguais, mostrar apenas um
            periodo_dados = periodo_max if periodo_min == periodo_max else f"{periodo_min} a {periodo_max}"
            
            # Calcular tempo em segundos
            tempo_segundos = int(tempo_processamento.total_seconds())
            
            # Registrar em etl_log
            sql_log = f"""
            INSERT INTO public.etl_log (
                tabela_nome, arquivo_origem, tipo_carga, periodo_dados,
                registros_inseridos, registros_atualizados, registros_erro, 
                status, inicio_processamento, fim_processamento
            ) VALUES (
                '{self.full_table_name}', '{arquivo_origem}', '{tipo_carga}', '{periodo_dados}',
                {registros_inseridos}, 0, {registros_erro}, 'sucesso',
                CURRENT_TIMESTAMP - INTERVAL '{tempo_segundos} seconds',
                CURRENT_TIMESTAMP
            )
            """
            
            db.execute_ddl(sql_log)
            logger.info("✅ Registro em etl_log criado")
            
            # Atualizar etl_control
            sql_control = f"""
            INSERT INTO public.etl_control (
                tabela_nome, ultima_carga_data, ultimo_periodo_carregado,
                total_registros_carregados, tipo_ultima_carga
            ) VALUES (
                '{self.full_table_name}', CURRENT_DATE, '{periodo_max}',
                {registros_inseridos}, '{tipo_carga}'
            )
            ON CONFLICT (tabela_nome) DO UPDATE SET
                ultima_carga_data = CURRENT_DATE,
                ultimo_periodo_carregado = '{periodo_max}',
                total_registros_carregados = CASE 
                    WHEN '{tipo_carga}' = 'inicial' THEN {registros_inseridos}
                    ELSE etl_control.total_registros_carregados + {registros_inseridos}
                END,
                tipo_ultima_carga = '{tipo_carga}',
                atualizado_em = CURRENT_TIMESTAMP
            """
            
            db.execute_ddl(sql_control)
            logger.info("✅ Registro em etl_control atualizado")
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar carga: {e}")
            import traceback
            logger.error(traceback.format_exc())

# Função para validar dados carregados
def validar_carga():
    """Valida os dados carregados"""
    try:
        # Contar registros
        query = """
        SELECT 
            COUNT(*) as total_registros,
            COUNT(DISTINCT periodo) as periodos_distintos,
            MIN(periodo) as primeiro_periodo,
            MAX(periodo) as ultimo_periodo,
            SUM(vacredito) as total_credito,
            SUM(vadebito) as total_debito,
            SUM(saldo_contabil_despesa) as total_saldo,
            COUNT(DISTINCT coug) as ugs_distintas,
            COUNT(DISTINCT cofonte) as fontes_distintas,
            COUNT(CASE WHEN LENGTH(cocontacorrente) = 40 THEN 1 END) as contas_40_chars,
            COUNT(CASE WHEN cosubelemento IS NOT NULL THEN 1 END) as com_subelemento
        FROM despesas.fato_despesa_saldo
        """
        
        result = db.execute_query(query)
        if result:
            row = result[0]
            print("\n📊 VALIDAÇÃO DOS DADOS CARREGADOS:")
            print(f"   Total de registros: {row[0]:,}")
            print(f"   Períodos distintos: {row[1]}")
            print(f"   Período inicial: {row[2]}")
            print(f"   Período final: {row[3]}")
            print(f"   Total crédito: R$ {row[4]:,.2f}")
            print(f"   Total débito: R$ {row[5]:,.2f}")
            print(f"   Total saldo contábil: R$ {row[6]:,.2f}")
            print(f"   UGs distintas: {row[7]}")
            print(f"   Fontes distintas: {row[8]}")
            print(f"   Contas com 40 caracteres: {row[9]:,}")
            print(f"   Registros com subelemento: {row[10]:,}")
            
    except Exception as e:
        logger.error(f"Erro na validação: {e}")

# Função principal para execução direta
def main():
    """Executa o ETL de DespesaSaldo"""
    etl = ETLDespesaSaldo(chunk_size=10000)  # Chunks maiores por ser arquivo grande
    file_path = "dados_brutos/fato/DespesaSaldo.xlsx"
    
    # Recriar tabela para aplicar nova estrutura
    success = etl.process_file(file_path, tipo_carga='inicial', recriar_tabela=True)
    
    if success:
        print("\n✅ ETL concluído com sucesso!")
        validar_carga()
    else:
        print("\n❌ ETL falhou!")

if __name__ == "__main__":
    main()