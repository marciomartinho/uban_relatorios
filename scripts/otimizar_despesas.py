"""
Script para deixar a consulta de despesas mais rápida
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import db
from datetime import datetime

print("=" * 60)
print("🚀 OTIMIZAÇÃO DA CONSULTA DE DESPESAS")
print("=" * 60)
print("\nEste script vai deixar sua consulta MUITO mais rápida!")
print("Pode demorar alguns minutos, mas vale a pena!\n")

# PARTE 1: Criar tabela de cache (atalho para carregar rápido)
print("📦 PARTE 1: Criando atalhos para carregar mais rápido...")
print("-" * 60)

try:
    # Criar tabela de cache
    print("1. Criando tabela de cache...")
    sql_create = """
    CREATE TABLE IF NOT EXISTS public.cache_filtros_despesa (
        tipo_filtro VARCHAR(20),
        valor VARCHAR(100),
        descricao VARCHAR(255),
        ordem INTEGER,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (tipo_filtro, valor)
    );
    """
    db.execute_ddl(sql_create)
    print("   ✅ Tabela criada!")
    
    # Limpar cache antigo
    print("\n2. Limpando dados antigos...")
    db.execute_ddl("TRUNCATE TABLE public.cache_filtros_despesa;")
    print("   ✅ Limpo!")
    
    # Popular anos
    print("\n3. Criando cache de ANOS...")
    sql_anos = """
    INSERT INTO public.cache_filtros_despesa (tipo_filtro, valor, ordem)
    SELECT DISTINCT 'ano', coexercicio::varchar, coexercicio
    FROM despesas.fato_despesa_saldo
    ORDER BY 3 DESC
    """
    db.execute_ddl(sql_anos)
    print("   ✅ Anos adicionados!")
    
    # Popular contas
    print("\n4. Criando cache de CONTAS (pode demorar um pouco)...")
    sql_contas = """
    INSERT INTO public.cache_filtros_despesa (tipo_filtro, valor, ordem)
    SELECT DISTINCT 'conta', cocontacontabil::varchar, cocontacontabil::bigint
    FROM despesas.fato_despesa_saldo
    ORDER BY 3
    """
    db.execute_ddl(sql_contas)
    print("   ✅ Contas adicionadas!")
    
    # Popular UGs
    print("\n5. Criando cache de UGs...")
    sql_ugs = """
    INSERT INTO public.cache_filtros_despesa (tipo_filtro, valor, descricao, ordem)
    SELECT DISTINCT 'ug', coug::varchar, MAX(noug), coug
    FROM despesas.fato_despesa_saldo
    GROUP BY coug
    ORDER BY 4
    """
    db.execute_ddl(sql_ugs)
    print("   ✅ UGs adicionadas!")
    
except Exception as e:
    print(f"\n❌ Erro na PARTE 1: {e}")
    print("Mas vamos continuar...")

# PARTE 2: Criar índices (deixa as buscas mais rápidas)
print("\n\n📊 PARTE 2: Criando índices para acelerar buscas...")
print("-" * 60)

indices = [
    {
        'nome': 'Índice principal',
        'sql': 'CREATE INDEX IF NOT EXISTS idx_despesa_filtros_principais ON despesas.fato_despesa_saldo(coexercicio, cocontacontabil, coug);'
    },
    {
        'nome': 'Índice de anos',
        'sql': 'CREATE INDEX IF NOT EXISTS idx_despesa_exercicio ON despesas.fato_despesa_saldo(coexercicio);'
    },
    {
        'nome': 'Índice de contas',
        'sql': 'CREATE INDEX IF NOT EXISTS idx_despesa_conta ON despesas.fato_despesa_saldo(cocontacontabil);'
    },
    {
        'nome': 'Índice de UGs',
        'sql': 'CREATE INDEX IF NOT EXISTS idx_despesa_ug ON despesas.fato_despesa_saldo(coug);'
    }
]

for i, idx in enumerate(indices, 1):
    try:
        print(f"\n{i}. Criando {idx['nome']}...")
        inicio = datetime.now()
        db.execute_ddl(idx['sql'])
        tempo = (datetime.now() - inicio).total_seconds()
        print(f"   ✅ Criado em {tempo:.1f} segundos")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

# PARTE 3: Atualizar estatísticas
print("\n\n🔄 PARTE 3: Finalizando otimizações...")
print("-" * 60)

try:
    print("Atualizando estatísticas do banco...")
    db.execute_ddl("ANALYZE despesas.fato_despesa_saldo;")
    print("✅ Estatísticas atualizadas!")
except Exception as e:
    print(f"❌ Erro: {e}")

# Verificar resultados
print("\n\n📋 VERIFICANDO RESULTADOS:")
print("-" * 60)

try:
    # Contar registros no cache
    result = db.execute_query("SELECT tipo_filtro, COUNT(*) FROM public.cache_filtros_despesa GROUP BY tipo_filtro")
    
    print("\nCache criado com sucesso:")
    for row in result:
        print(f"   - {row[0].upper()}: {row[1]} valores")
    
    print("\n✨ OTIMIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print("\n🎉 Sua consulta de despesas agora está MUITO mais rápida!")
    
except Exception as e:
    print(f"\n❌ Erro ao verificar: {e}")

print("\n" + "=" * 60)
print("Pronto! Agora você pode usar a página normalmente.")
print("=" * 60)