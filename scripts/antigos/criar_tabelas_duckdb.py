"""
Script para criar as tabelas de lançamento no DuckDB
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database_duckdb import db_duckdb

def criar_tabelas():
    """Cria as tabelas de lançamento no DuckDB"""
    print("🏗️ Criando estrutura das tabelas no DuckDB...")
    
    conn = db_duckdb.get_connection()
    
    try:
        # Criar tabela receita_lancamento
        print("\n📊 Criando tabela receita_lancamento...")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS receita_lancamento (
            -- Colunas originais
            coexercicio INTEGER,
            coug INTEGER,
            cogestao INTEGER,
            nudocumento VARCHAR(20),
            nulancamento INTEGER,
            coevento INTEGER,
            cocontacontabil BIGINT,
            cocontacorrente VARCHAR(50),
            inmes INTEGER,
            dalancamento DATE,
            valancamento DECIMAL(18,2),
            indebitocredito VARCHAR(1),
            inabreencerra INTEGER,
            cougdestino INTEGER,
            cogestaodestino INTEGER,
            datransacao DATE,
            hotransacao TIME,
            cougcontab INTEGER,
            cogestaocontab INTEGER,
            
            -- Colunas derivadas (todas as do PostgreSQL)
            coclasseorc VARCHAR(8),
            cofonte VARCHAR(10),
            cocategoriareceita VARCHAR(1),
            cofontereceita VARCHAR(2),
            cosubfontereceita VARCHAR(3),
            corubrica VARCHAR(4),
            coalinea VARCHAR(6),
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
            cosubelemento VARCHAR(2),
            
            -- Metadados
            periodo VARCHAR(7),
            tipo_lancamento VARCHAR(10),
            data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ Tabela receita_lancamento criada!")
        
        # Criar tabela despesa_lancamento
        print("\n💰 Criando tabela despesa_lancamento...")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS despesa_lancamento (
            -- Colunas originais
            coexercicio INTEGER,
            coug INTEGER,
            cogestao INTEGER,
            nudocumento VARCHAR(20),
            nulancamento INTEGER,
            coevento INTEGER,
            cocontacontabil BIGINT,
            cocontacorrente VARCHAR(50),
            inmes INTEGER,
            dalancamento DATE,
            valancamento DECIMAL(18,2),
            indebitocredito VARCHAR(1),
            inabreencerra INTEGER,
            cougdestino INTEGER,
            cogestaodestino INTEGER,
            datransacao DATE,
            hotransacao TIME,
            cougcontab INTEGER,
            cogestaocontab INTEGER,
            
            -- Colunas derivadas
            inesfera VARCHAR(1),
            couo VARCHAR(5),
            cofuncao VARCHAR(2),
            cosubfuncao VARCHAR(3),
            coprograma VARCHAR(4),
            coprojeto VARCHAR(4),
            cosubtitulo VARCHAR(4),
            cofonte VARCHAR(10),
            conatureza VARCHAR(6),
            incategoria VARCHAR(1),
            cogrupo VARCHAR(1),
            comodalidade VARCHAR(2),
            coelemento VARCHAR(2),
            cosubelemento VARCHAR(2),
            
            -- Metadados
            periodo VARCHAR(7),
            tipo_lancamento VARCHAR(10),
            data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ Tabela despesa_lancamento criada!")
        
        # Verificar tabelas criadas
        print("\n🔍 Verificando tabelas criadas...")
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"Tabelas no banco: {[t[0] for t in tables]}")
        
        print("\n✅ Estrutura do banco DuckDB criada com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    criar_tabelas()