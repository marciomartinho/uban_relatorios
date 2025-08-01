"""
Módulo ETL para processar ReceitaSaldo.xlsx
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

class ETLReceitaSaldo:
    """Classe para processar o arquivo ReceitaSaldo.xlsx"""
    
    def __init__(self, chunk_size=10000):
        self.chunk_size = chunk_size
        self.table_name = 'fato_receita_saldo'
        self.schema_name = 'receitas'
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
        logger.info("Criando tabela fato_receita_saldo...")
        
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.full_table_name} (
            -- Colunas originais
            coexercicio INTEGER,
            inmes INTEGER,
            coug VARCHAR(10),
            cocontacontabil VARCHAR(20),
            cocontacorrente VARCHAR(50),
            intipoadm INTEGER,
            vacredito DECIMAL(18,2),
            vadebito DECIMAL(18,2),
            
            -- Coluna calculada
            saldo_contabil_receita DECIMAL(18,2),
            
            -- Colunas derivadas de COCONTACORRENTE (17 chars)
            coclasseorc VARCHAR(8),
            cofonte VARCHAR(10),  -- Unificado para 17 e 38 chars
            cocategoriareceita VARCHAR(1),
            cofontereceita VARCHAR(2),
            cosubfontereceita VARCHAR(3),
            corubrica VARCHAR(4),
            coalinea VARCHAR(6),
            
            -- Colunas derivadas de COCONTACORRENTE (38 chars)
            inesfera VARCHAR(1),
            couo VARCHAR(5),
            cofuncao VARCHAR(2),
            cosubfuncao VARCHAR(3),
            coprograma VARCHAR(4),
            coprojeto VARCHAR(4),
            cosubtitulo VARCHAR(4),
            conatureza VARCHAR(6),
            incategoria VARCHAR(1),
            cogrupo VARCHAR(1),
            comodalidade VARCHAR(2),
            coelemento VARCHAR(2),
            
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
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_cofonte
            ON {self.full_table_name}(cofonte);
        CREATE INDEX IF NOT EXISTS idx_{self.table_name}_coclasseorc
            ON {self.full_table_name}(coclasseorc);
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
        df['inmes'] = df['INMES'].astype(int)
        df['coug'] = df['COUG'].astype(str).str.strip()
        df['cocontacontabil'] = df['COCONTACONTABIL'].astype(str).str.strip()
        df['cocontacorrente'] = df['COCONTACORRENTE'].astype(str).str.strip()
        df['intipoadm'] = df['INTIPOADM'].astype(int)
        df['vacredito'] = pd.to_numeric(df['VACREDITO'], errors='coerce').fillna(0)
        df['vadebito'] = pd.to_numeric(df['VADEBITO'], errors='coerce').fillna(0)
        
        # Criar coluna periodo (YYYY-MM)
        df['periodo'] = df['coexercicio'].astype(str) + '-' + df['inmes'].astype(str).str.zfill(2)
        
        # Calcular saldo_contabil_receita baseado no primeiro dígito
        df['primeiro_digito'] = df['cocontacontabil'].str[0]
        df['saldo_contabil_receita'] = np.where(
            df['primeiro_digito'] == '5',
            df['vadebito'] - df['vacredito'],  # Se começar com 5
            df['vacredito'] - df['vadebito']   # Se começar com 6 ou outro
        )
        
        # Tamanho real da conta corrente (sem espaços)
        df['tamanho_conta'] = df['cocontacorrente'].str.len()
        
        # Inicializar todas as colunas derivadas com None
        colunas_derivadas = [
            'coclasseorc', 'cofonte', 'cocategoriareceita', 'cofontereceita',
            'cosubfontereceita', 'corubrica', 'coalinea', 'inesfera', 'couo', 
            'cofuncao', 'cosubfuncao', 'coprograma', 'coprojeto', 'cosubtitulo',
            'conatureza', 'incategoria', 'cogrupo', 'comodalidade', 'coelemento'
        ]
        for col in colunas_derivadas:
            df[col] = None
        
        # Parse para contas de 17 caracteres
        mask_17 = df['tamanho_conta'] == 17
        if mask_17.any():
            # COCLASSEORC: caracteres 1-8
            df.loc[mask_17, 'coclasseorc'] = df.loc[mask_17, 'cocontacorrente'].str[0:8]
            
            # COFONTE: caracteres 9-18
            df.loc[mask_17, 'cofonte'] = df.loc[mask_17, 'cocontacorrente'].str[8:18]
            
            # Novas colunas baseadas no COCLASSEORC
            df.loc[mask_17, 'cocategoriareceita'] = df.loc[mask_17, 'cocontacorrente'].str[0:1]
            df.loc[mask_17, 'cofontereceita'] = df.loc[mask_17, 'cocontacorrente'].str[0:2]
            df.loc[mask_17, 'cosubfontereceita'] = df.loc[mask_17, 'cocontacorrente'].str[0:3]
            df.loc[mask_17, 'corubrica'] = df.loc[mask_17, 'cocontacorrente'].str[0:4]
            df.loc[mask_17, 'coalinea'] = df.loc[mask_17, 'cocontacorrente'].str[0:6]
        
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
            df.loc[mask_38, 'cofonte'] = df.loc[mask_38, 'cocontacorrente'].str[23:32]  # COFONTE unificado
            df.loc[mask_38, 'conatureza'] = df.loc[mask_38, 'cocontacorrente'].str[32:38]
            df.loc[mask_38, 'incategoria'] = df.loc[mask_38, 'cocontacorrente'].str[32:33]
            df.loc[mask_38, 'cogrupo'] = df.loc[mask_38, 'cocontacorrente'].str[33:34]
            df.loc[mask_38, 'comodalidade'] = df.loc[mask_38, 'cocontacorrente'].str[34:36]
            df.loc[mask_38, 'coelemento'] = df.loc[mask_38, 'cocontacorrente'].str[36:38]
        
        # Selecionar apenas as colunas finais necessárias
        colunas_finais = [
            'coexercicio', 'inmes', 'coug', 'cocontacontabil', 'cocontacorrente',
            'intipoadm', 'vacredito', 'vadebito', 'saldo_contabil_receita',
            'coclasseorc', 'cofonte', 'cocategoriareceita', 'cofontereceita',
            'cosubfontereceita', 'corubrica', 'coalinea', 'inesfera', 'couo', 
            'cofuncao', 'cosubfuncao', 'coprograma', 'coprojeto', 'cosubtitulo',
            'conatureza', 'incategoria', 'cogrupo', 'comodalidade', 'coelemento',
            'periodo'
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
            logger.info("Lendo arquivo Excel...")
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
            
            # Registrar em etl_log usando execute_query com parâmetros
            sql_log = """
            INSERT INTO public.etl_log (
                tabela_nome, arquivo_origem, tipo_carga, periodo_dados,
                registros_inseridos, registros_atualizados, registros_erro, 
                status, inicio_processamento, fim_processamento
            ) VALUES (
                :tabela, :arquivo, :tipo, :periodo,
                :inseridos, 0, :erros, 'sucesso',
                CURRENT_TIMESTAMP - INTERVAL ':tempo seconds',
                CURRENT_TIMESTAMP
            )
            """
            
            # Usar execute_ddl pois é um INSERT
            sql_log_formatted = f"""
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
            
            db.execute_ddl(sql_log_formatted)
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
            SUM(saldo_contabil_receita) as total_saldo,
            COUNT(DISTINCT cofonte) as fontes_distintas,
            COUNT(CASE WHEN LENGTH(cocontacorrente) = 17 THEN 1 END) as contas_17_chars,
            COUNT(CASE WHEN LENGTH(cocontacorrente) = 38 THEN 1 END) as contas_38_chars
        FROM receitas.fato_receita_saldo
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
            print(f"   Fontes distintas: {row[7]}")
            print(f"   Contas com 17 caracteres: {row[8]:,}")
            print(f"   Contas com 38 caracteres: {row[9]:,}")
            
    except Exception as e:
        logger.error(f"Erro na validação: {e}")

# Função principal para execução direta
def main():
    """Executa o ETL de ReceitaSaldo"""
    etl = ETLReceitaSaldo(chunk_size=5000)
    file_path = "dados_brutos/fato/ReceitaSaldo.xlsx"
    
    # Recriar tabela para aplicar nova estrutura
    success = etl.process_file(file_path, tipo_carga='inicial', recriar_tabela=True)
    
    if success:
        print("\n✅ ETL concluído com sucesso!")
        validar_carga()
    else:
        print("\n❌ ETL falhou!")

if __name__ == "__main__":
    main()