"""
Módulo para conexão com DuckDB local (lançamentos)
"""
import duckdb
import os
from pathlib import Path

class DatabaseDuckDB:
    """Gerencia conexão com DuckDB local"""
    
    def __init__(self):
        # Caminho do banco DuckDB
        self.db_path = Path("dados_brutos/fato/db_local/lancamentos.duckdb")
        # Criar pasta se não existir
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def get_connection(self):
        """Retorna uma conexão com o DuckDB"""
        return duckdb.connect(str(self.db_path))
    
    def test_connection(self):
        """Testa a conexão com o DuckDB"""
        try:
            conn = self.get_connection()
            conn.execute("SELECT 1").fetchall()
            print("✅ Conexão DuckDB local: OK")
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Erro na conexão DuckDB: {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Executa uma query e retorna resultados"""
        conn = self.get_connection()
        try:
            if params:
                result = conn.execute(query, params).fetchall()
            else:
                result = conn.execute(query).fetchall()
            return result
        finally:
            conn.close()
    
    def execute_ddl(self, query):
        """Executa comandos DDL (CREATE, ALTER, DROP)"""
        conn = self.get_connection()
        try:
            conn.execute(query)
            conn.commit()
        finally:
            conn.close()

# Instância global
db_duckdb = DatabaseDuckDB()

if __name__ == "__main__":
    db_duckdb.test_connection()