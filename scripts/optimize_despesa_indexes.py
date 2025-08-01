"""
Script para criar índices otimizados para melhorar performance dos filtros
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import db
from datetime import datetime

def criar_indices_otimizados():
    """Cria índices específicos para melhorar performance dos filtros"""
    
    print("=" * 60)
    print("CRIAÇÃO DE ÍNDICES OTIMIZADOS - DESPESAS")
    print("=" * 60)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    indices = [
        # Índices para os filtros principais
        {
            'nome': 'idx_despesa_filtros_principais',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_despesa_filtros_principais ON despesas.fato_despesa_saldo(coexercicio, cocontacontabil, coug);'
        },
        # Índices individuais para DISTINCT rápido
        {
            'nome': 'idx_despesa_exercicio',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_despesa_exercicio ON despesas.fato_despesa_saldo(coexercicio);'
        },
        {
            'nome': 'idx_despesa_conta',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_despesa_conta ON despesas.fato_despesa_saldo(cocontacontabil);'
        },
        {
            'nome': 'idx_despesa_ug',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_despesa_ug ON despesas.fato_despesa_saldo(coug);'
        },
        # Índice composto para queries filtradas
        {
            'nome': 'idx_despesa_consulta',
            'sql': 'CREATE INDEX IF NOT EXISTS idx_despesa_consulta ON despesas.fato_despesa_saldo(coexercicio, cocontacontabil, coug, inmes, conatureza);'
        }
    ]
    
    for idx in indices:
        try:
            print(f"\n📊 Criando índice: {idx['nome']}...")
            inicio = datetime.now()
            db.execute_ddl(idx['sql'])
            tempo = (datetime.now() - inicio).total_seconds()
            print(f"   ✅ Criado em {tempo:.2f} segundos")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    
    # Atualizar estatísticas da tabela
    print("\n🔄 Atualizando estatísticas da tabela...")
    try:
        db.execute_ddl("ANALYZE despesas.fato_despesa_saldo;")
        print("   ✅ Estatísticas atualizadas")
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n" + "=" * 60)
    print("✨ PROCESSO CONCLUÍDO!")
    print("=" * 60)

if __name__ == "__main__":
    criar_indices_otimizados()