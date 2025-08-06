# app/db_manager.py

import os
from flask import current_app
from app.modules.database_duckdb import db_duckdb
from app.modules.database import db as db_postgres
import pandas as pd

class DBManager:
    """
    Gerente de Conexão que escolhe o banco de dados (DuckDB ou PostgreSQL)
    com base no ambiente da aplicação (desenvolvimento ou produção).
    """
    def __init__(self):
        self.db_engine = None
        self.is_duckdb = True

    def init_app(self, app):
        """Inicializa o gerente com base na configuração do Flask."""
        with app.app_context():
            if current_app.config['FLASK_ENV'] == 'development':
                print("▶️  Ambiente de Desenvolvimento: Usando DuckDB.")
                self.is_duckdb = True
            else:
                print("🚀 Ambiente de Produção: Usando PostgreSQL.")
                self.db_engine = db_postgres.engine
                self.is_duckdb = False

    def execute_query(self, query, params=None):
        """
        Executa uma query SELECT e retorna os resultados como uma lista de dicionários,
        unificando o comportamento do DuckDB e do PostgreSQL.
        """
        if self.is_duckdb:
            conn = db_duckdb.get_connection()
            try:
                # CORRIGIDO: DuckDB espera uma LISTA de parâmetros para os '?'
                # e não um dicionário. A query precisa usar '?' em vez de ':nome'.
                # A conversão de dicionário para lista será feita na rota.
                df = conn.execute(query, params).fetchdf()
                return df.to_dict(orient='records')
            finally:
                conn.close()
        else:
            # Para o PostgreSQL, usamos a conexão SQLAlchemy que aceita dicionários
            df = pd.read_sql(query, self.db_engine, params=params)
            return df.to_dict(orient='records')

# Instância global do nosso gerente
db_manager = DBManager()