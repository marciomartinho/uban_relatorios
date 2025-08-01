"""
Script para criar e popular tabela de cache para filtros
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import db
from datetime import datetime

def criar_cache_filtros():
    """Cria tabelas de cache para melhorar performance dos filtros"""
    
    print("=" * 60)
    print("CRIAÇÃO DE CACHE DE FILTROS")
    print("=" * 60)
    
    # Criar tabela de cache
    print("\n📋 Criando tabela de cache...")
    sql_create = """
    CREATE TABLE IF NOT EXISTS public.cache_filtros_despesa (
        tipo_filtro VARCHAR(20),
        valor VARCHAR(100),
        descricao VARCHAR(255),
        ordem INTEGER,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (tipo_filtro, valor)
    );
    
    CREATE INDEX IF NOT EXISTS idx_cache_filtros_tipo 
        ON public.cache_filtros_despesa(tipo_filtro);
    """
    
    try:
        db.execute_ddl(sql_create)
        print("   ✅ Tabela criada")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return
    
    # Limpar cache existente
    print("\n🗑️  Limpando cache antigo...")
    db.execute_ddl("TRUNCATE TABLE public.cache_filtros_despesa;")
    
    # Popular cache
    filtros = [
        {
            'tipo': 'ano',
            'query': """
                INSERT INTO public.cache_filtros_despesa (tipo_filtro, valor, ordem)
                SELECT DISTINCT 'ano', coexercicio::varchar, coexercicio
                FROM despesas.fato_despesa_saldo
                ORDER BY 3 DESC
            """
        },
        {
            'tipo': 'conta',
            'query': """
                INSERT INTO public.cache_filtros_despesa (tipo_filtro, valor, ordem)
                SELECT DISTINCT 'conta', cocontacontabil::varchar, cocontacontabil::bigint
                FROM despesas.fato_despesa_saldo
                ORDER BY 3
            """
        },
        {
            'tipo': 'ug',
            'query': """
                INSERT INTO public.cache_filtros_despesa (tipo_filtro, valor, descricao, ordem)
                SELECT DISTINCT 'ug', coug::varchar, MAX(noug), coug
                FROM despesas.fato_despesa_saldo
                GROUP BY coug
                ORDER BY 4
            """
        }
    ]
    
    for filtro in filtros:
        print(f"\n📊 Populando cache de {filtro['tipo']}...")
        inicio = datetime.now()
        try:
            db.execute_ddl(filtro['query'])
            tempo = (datetime.now() - inicio).total_seconds()
            
            # Contar registros
            count_query = f"SELECT COUNT(*) FROM public.cache_filtros_despesa WHERE tipo_filtro = '{filtro['tipo']}'"
            result = db.execute_query(count_query)
            qtd = result[0][0] if result else 0
            
            print(f"   ✅ {qtd} valores em {tempo:.2f} segundos")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    print("\n✨ Cache criado com sucesso!")
    
    # Criar procedure para atualizar cache
    print("\n🔄 Criando procedure de atualização...")
    sql_procedure = """
    CREATE OR REPLACE FUNCTION atualizar_cache_filtros_despesa()
    RETURNS void AS $$
    BEGIN
        -- Limpar cache
        DELETE FROM public.cache_filtros_despesa;
        
        -- Repopular
        INSERT INTO public.cache_filtros_despesa (tipo_filtro, valor, ordem)
        SELECT DISTINCT 'ano', coexercicio::varchar, coexercicio
        FROM despesas.fato_despesa_saldo;
        
        INSERT INTO public.cache_filtros_despesa (tipo_filtro, valor, ordem)
        SELECT DISTINCT 'conta', cocontacontabil::varchar, cocontacontabil::bigint
        FROM despesas.fato_despesa_saldo;
        
        INSERT INTO public.cache_filtros_despesa (tipo_filtro, valor, descricao, ordem)
        SELECT DISTINCT 'ug', coug::varchar, MAX(noug), coug
        FROM despesas.fato_despesa_saldo
        GROUP BY coug;
        
        -- Atualizar timestamp
        UPDATE public.cache_filtros_despesa 
        SET atualizado_em = CURRENT_TIMESTAMP;
    END;
    $$ LANGUAGE plpgsql;
    """
    
    try:
        db.execute_ddl(sql_procedure)
        print("   ✅ Procedure criada")
        print("\n💡 Para atualizar o cache após cargas, execute:")
        print("   SELECT atualizar_cache_filtros_despesa();")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    criar_cache_filtros()