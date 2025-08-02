"""
Script para migrar dados de lançamentos do PostgreSQL para DuckDB
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import db
from app.modules.database_duckdb import db_duckdb
import pandas as pd
from datetime import datetime
from tqdm import tqdm

def contar_registros_postgres():
    """Conta registros nas tabelas do PostgreSQL"""
    print("\n📊 Contando registros no PostgreSQL...")
    
    # Contar receita_lancamento
    try:
        query_receita = "SELECT COUNT(*) FROM receitas.fato_receita_lancamento"
        result_receita = db.execute_query(query_receita)
        count_receita = result_receita[0][0] if result_receita else 0
        print(f"   Receita Lançamento: {count_receita:,} registros")
    except:
        count_receita = 0
        print("   ❌ Tabela receitas.fato_receita_lancamento não encontrada")
    
    # Contar despesa_lancamento
    try:
        query_despesa = "SELECT COUNT(*) FROM despesas.fato_despesa_lancamento"
        result_despesa = db.execute_query(query_despesa)
        count_despesa = result_despesa[0][0] if result_despesa else 0
        print(f"   Despesa Lançamento: {count_despesa:,} registros")
    except:
        count_despesa = 0
        print("   ❌ Tabela despesas.fato_despesa_lancamento não encontrada")
    
    return count_receita, count_despesa

def migrar_receita_lancamento():
    """Migra dados de receita_lancamento"""
    print("\n💾 Migrando RECEITA LANÇAMENTO...")
    
    try:
        # Query para buscar dados (SEM data_carga!)
        query = """
        SELECT 
            coexercicio, coug, cogestao, nudocumento, nulancamento,
            coevento, cocontacontabil, cocontacorrente, inmes,
            dalancamento, valancamento, indebitocredito, inabreencerra,
            cougdestino, cogestaodestino, datransacao, hotransacao,
            cougcontab, cogestaocontab, coclasseorc, cofonte,
            cocategoriareceita, cofontereceita, cosubfontereceita,
            corubrica, coalinea, inesfera, couo, cofuncao,
            cosubfuncao, coprograma, coprojeto, cosubtitulo,
            conatureza, incategoria, cogrupo, comodalidade,
            coelemento, cosubelemento, periodo, tipo_lancamento
        FROM receitas.fato_receita_lancamento
        ORDER BY periodo, coug, nudocumento
        """
        
        print("   📖 Lendo dados do PostgreSQL...")
        df = pd.read_sql(query, db.engine)
        total_registros = len(df)
        print(f"   📊 Total de registros encontrados: {total_registros:,}")
        
        if total_registros == 0:
            print("   ⚠️ Nenhum registro encontrado para migrar")
            return True
        
        # Conectar no DuckDB
        conn = db_duckdb.get_connection()
        
        # Limpar tabela destino
        print("   🗑️ Limpando tabela destino...")
        conn.execute("DELETE FROM receita_lancamento")
        
        # Inserir dados em chunks
        chunk_size = 10000
        print(f"   📥 Inserindo dados em chunks de {chunk_size:,} registros...")
        
        # Criar lista de colunas explicitamente (sem data_carga)
        colunas = [
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
        
        colunas_str = ', '.join(colunas)
        
        with tqdm(total=total_registros, desc="   Progresso") as pbar:
            for start in range(0, total_registros, chunk_size):
                end = min(start + chunk_size, total_registros)
                chunk = df.iloc[start:end]
                
                # Registrar no DuckDB
                conn.register('chunk_df', chunk)
                conn.execute(f"""
                    INSERT INTO receita_lancamento ({colunas_str})
                    SELECT {colunas_str} FROM chunk_df
                """)
                conn.unregister('chunk_df')
                
                pbar.update(len(chunk))
        
        # Verificar total inserido
        count = conn.execute("SELECT COUNT(*) FROM receita_lancamento").fetchone()[0]
        print(f"   ✅ Total inserido no DuckDB: {count:,} registros")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrar_despesa_lancamento():
    """Migra dados de despesa_lancamento"""
    print("\n💸 Migrando DESPESA LANÇAMENTO...")
    
    try:
        # Primeiro verificar se tem dados
        count_query = "SELECT COUNT(*) FROM despesas.fato_despesa_lancamento"
        result = db.execute_query(count_query)
        total_postgres = result[0][0] if result else 0
        
        if total_postgres == 0:
            print("   ⚠️ Nenhum registro encontrado na tabela de despesas")
            return True
        
        print(f"   📊 Total de registros para migrar: {total_postgres:,}")
        print("   ⚠️ ATENÇÃO: Este processo pode demorar devido ao volume de dados!")
        
        # Query para buscar dados (SEM data_carga!)
        query = """
        SELECT 
            coexercicio, coug, cogestao, nudocumento, nulancamento,
            coevento, cocontacontabil, cocontacorrente, inmes,
            dalancamento, valancamento, indebitocredito, inabreencerra,
            cougdestino, cogestaodestino, datransacao, hotransacao,
            cougcontab, cogestaocontab, inesfera, couo, cofuncao,
            cosubfuncao, coprograma, coprojeto, cosubtitulo, cofonte,
            conatureza, incategoria, cogrupo, comodalidade, coelemento,
            cosubelemento, periodo, tipo_lancamento
        FROM despesas.fato_despesa_lancamento
        ORDER BY periodo, coug, nudocumento
        """
        
        print("   📖 Lendo dados do PostgreSQL (pode demorar)...")
        df = pd.read_sql(query, db.engine)
        total_registros = len(df)
        
        # Conectar no DuckDB
        conn = db_duckdb.get_connection()
        
        # Limpar tabela destino
        print("   🗑️ Limpando tabela destino...")
        conn.execute("DELETE FROM despesa_lancamento")
        
        # Inserir dados em chunks maiores para despesa
        chunk_size = 50000
        print(f"   📥 Inserindo dados em chunks de {chunk_size:,} registros...")
        
        # Criar lista de colunas explicitamente (sem data_carga)
        colunas = [
            'coexercicio', 'coug', 'cogestao', 'nudocumento', 'nulancamento',
            'coevento', 'cocontacontabil', 'cocontacorrente', 'inmes',
            'dalancamento', 'valancamento', 'indebitocredito', 'inabreencerra',
            'cougdestino', 'cogestaodestino', 'datransacao', 'hotransacao',
            'cougcontab', 'cogestaocontab', 'inesfera', 'couo', 'cofuncao',
            'cosubfuncao', 'coprograma', 'coprojeto', 'cosubtitulo', 'cofonte',
            'conatureza', 'incategoria', 'cogrupo', 'comodalidade', 'coelemento',
            'cosubelemento', 'periodo', 'tipo_lancamento'
        ]
        
        colunas_str = ', '.join(colunas)
        
        with tqdm(total=total_registros, desc="   Progresso") as pbar:
            for start in range(0, total_registros, chunk_size):
                end = min(start + chunk_size, total_registros)
                chunk = df.iloc[start:end]
                
                # Registrar no DuckDB
                conn.register('chunk_df', chunk)
                conn.execute(f"""
                    INSERT INTO despesa_lancamento ({colunas_str})
                    SELECT {colunas_str} FROM chunk_df
                """)
                conn.unregister('chunk_df')
                
                pbar.update(len(chunk))
        
        # Verificar total inserido
        count = conn.execute("SELECT COUNT(*) FROM despesa_lancamento").fetchone()[0]
        print(f"   ✅ Total inserido no DuckDB: {count:,} registros")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Erro na migração: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa a migração completa"""
    print("=" * 60)
    print("MIGRAÇÃO DE LANÇAMENTOS: PostgreSQL → DuckDB")
    print("=" * 60)
    
    inicio = datetime.now()
    
    # Contar registros originais
    count_receita, count_despesa = contar_registros_postgres()
    
    if count_receita == 0 and count_despesa == 0:
        print("\n❌ Nenhum dado de lançamento encontrado no PostgreSQL!")
        print("   Verifique se as tabelas foram carregadas corretamente.")
        return
    
    # Perguntar se quer continuar
    print(f"\n📋 Resumo da migração:")
    print(f"   - Receita Lançamento: {count_receita:,} registros")
    print(f"   - Despesa Lançamento: {count_despesa:,} registros")
    print(f"   - Total: {count_receita + count_despesa:,} registros")
    
    resposta = input("\n▶️ Deseja continuar com a migração? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Migração cancelada pelo usuário.")
        return
    
    # Executar migrações
    sucesso_receita = migrar_receita_lancamento() if count_receita > 0 else True
    sucesso_despesa = migrar_despesa_lancamento() if count_despesa > 0 else True
    
    # Resumo final
    tempo_total = datetime.now() - inicio
    print("\n" + "=" * 60)
    print("RESUMO DA MIGRAÇÃO")
    print("=" * 60)
    
    if sucesso_receita and sucesso_despesa:
        print("✅ Migração concluída com SUCESSO!")
    else:
        print("⚠️ Migração concluída com ERROS!")
        if not sucesso_receita:
            print("   ❌ Erro na migração de Receita Lançamento")
        if not sucesso_despesa:
            print("   ❌ Erro na migração de Despesa Lançamento")
    
    print(f"\n⏱️ Tempo total: {tempo_total}")
    
    # Verificar dados no DuckDB
    print("\n🔍 Verificando dados migrados no DuckDB...")
    conn = db_duckdb.get_connection()
    
    count_rec = conn.execute("SELECT COUNT(*) FROM receita_lancamento").fetchone()[0]
    count_desp = conn.execute("SELECT COUNT(*) FROM despesa_lancamento").fetchone()[0]
    
    print(f"   Receita Lançamento: {count_rec:,} registros")
    print(f"   Despesa Lançamento: {count_desp:,} registros")
    print(f"   Total no DuckDB: {count_rec + count_desp:,} registros")
    
    conn.close()

if __name__ == "__main__":
    main()