"""
Módulo de conexão e gerenciamento do banco de dados
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import pandas as pd
from config import Config

class Database:
    """Classe para gerenciar conexões com o PostgreSQL"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.init_engine()
    
    def init_engine(self):
        """Inicializa o engine do SQLAlchemy"""
        try:
            self.engine = create_engine(
                Config.SQLALCHEMY_DATABASE_URI,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verifica conexões antes de usar
                echo=Config.DEBUG    # Mostra SQL queries em debug
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            print("✅ Conexão com banco de dados configurada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao configurar banco de dados: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager para sessões do banco"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def test_connection(self):
        """Testa a conexão com o banco de dados"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ Conectado ao PostgreSQL: {version}")
                return True
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False
    
    def create_database_if_not_exists(self):
        """Cria o banco de dados se não existir"""
        # Conecta no banco postgres padrão para criar o novo banco
        temp_engine = create_engine(
            f'postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/postgres',
            isolation_level='AUTOCOMMIT'
        )
        
        try:
            with temp_engine.connect() as conn:
                # Verifica se o banco existe
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                    {"dbname": Config.DB_NAME}
                )
                
                if not result.fetchone():
                    # Cria o banco se não existir
                    conn.execute(text(f'CREATE DATABASE {Config.DB_NAME}'))
                    print(f"✅ Banco de dados '{Config.DB_NAME}' criado com sucesso!")
                else:
                    print(f"ℹ️ Banco de dados '{Config.DB_NAME}' já existe.")
                    
        except Exception as e:
            print(f"❌ Erro ao criar banco de dados: {e}")
            raise
        finally:
            temp_engine.dispose()
    
    def execute_query(self, query, params=None):
        """Executa uma query SELECT e retorna os resultados"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return result.fetchall()
    
    def execute_ddl(self, query):
        """Executa comandos DDL (CREATE, ALTER, DROP) que não retornam resultados"""
        with self.engine.connect() as conn:
            conn.execute(text(query))
            conn.commit()
    
    def df_to_sql(self, dataframe, table_name, if_exists='replace', index=False):
        """Salva um DataFrame pandas no banco de dados"""
        try:
            dataframe.to_sql(
                name=table_name,
                con=self.engine,
                if_exists=if_exists,
                index=index
            )
            print(f"✅ Tabela '{table_name}' salva com sucesso! ({len(dataframe)} registros)")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar tabela '{table_name}': {e}")
            return False
    
    def read_sql(self, query, params=None):
        """Lê dados do banco e retorna um DataFrame pandas"""
        return pd.read_sql(query, self.engine, params=params)
    
    def table_exists(self, table_name):
        """Verifica se uma tabela existe no banco"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        );
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {"table_name": table_name})
            return result.scalar()
    
    def get_table_info(self, table_name):
        """Retorna informações sobre as colunas de uma tabela"""
        query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = :table_name
        ORDER BY ordinal_position;
        """
        return self.execute_query(query, {"table_name": table_name})

# Instância global do banco de dados
db = Database()