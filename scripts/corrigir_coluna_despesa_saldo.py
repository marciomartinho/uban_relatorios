#!/usr/bin/env python3
"""
Script para corrigir o nome da coluna incategoria para cogrupo na tabela despesa_saldo
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
from pathlib import Path
from datetime import datetime

def corrigir_coluna_despesa_saldo():
    """Renomeia a coluna incategoria para cogrupo em despesa_saldo"""
    
    db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
    
    print("=" * 80)
    print("CORREÇÃO DE COLUNA - DESPESA_SALDO")
    print("=" * 80)
    print(f"Banco de dados: {db_path}")
    print(f"Correção: incategoria → cogrupo")
    print()
    
    if not db_path.exists():
        print(f"❌ ERRO: Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        conn = duckdb.connect(str(db_path))
        
        # 1. Verificar estrutura atual
        print("📊 Verificando estrutura atual da tabela despesa_saldo...")
        colunas = conn.execute("""
            SELECT column_name, data_type, ordinal_position
            FROM information_schema.columns 
            WHERE table_name = 'despesa_saldo'
            ORDER BY ordinal_position
        """).fetchall()
        
        # Verificar se incategoria existe e cogrupo não existe
        tem_incategoria = any(col[0] == 'incategoria' for col in colunas)
        tem_cogrupo = any(col[0] == 'cogrupo' for col in colunas)
        
        if not tem_incategoria:
            print("❌ ERRO: Coluna 'incategoria' não encontrada!")
            print("\nColunas existentes:")
            for col, tipo, pos in colunas:
                print(f"   {pos}. {col} ({tipo})")
            return False
        
        if tem_cogrupo:
            print("⚠️ AVISO: Coluna 'cogrupo' já existe!")
            print("   Pode ser que a correção já foi aplicada.")
            return False
        
        print("✅ Coluna 'incategoria' encontrada")
        print("✅ Coluna 'cogrupo' não existe (OK para criar)")
        
        # 2. Mostrar valores únicos atuais
        print("\n📈 Analisando valores atuais de 'incategoria'...")
        valores = conn.execute("""
            SELECT incategoria, COUNT(*) as qtd
            FROM despesa_saldo
            GROUP BY incategoria
            ORDER BY incategoria
        """).fetchall()
        
        print(f"   Valores distintos: {len(valores)}")
        for val, qtd in valores[:10]:  # Mostrar até 10
            print(f"   - {val}: {qtd:,} registros")
        
        # 3. Verificar relacionamento atual (que está falhando)
        print("\n🔍 Verificando relacionamento atual com dim_categoria_despesa...")
        orfaos = conn.execute("""
            SELECT COUNT(DISTINCT ds.incategoria)
            FROM despesa_saldo ds
            LEFT JOIN dim_categoria_despesa dcd ON ds.incategoria = dcd.incategoria
            WHERE ds.incategoria IS NOT NULL
            AND dcd.incategoria IS NULL
        """).fetchone()[0]
        
        print(f"   Valores órfãos em dim_categoria_despesa: {orfaos}")
        
        # 4. Verificar se os valores batem com dim_grupo_despesa
        print("\n🔍 Verificando se os valores correspondem a dim_grupo_despesa...")
        
        # Primeiro, verificar se dim_grupo_despesa existe
        dim_grupo_exists = conn.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'dim_grupo_despesa'
        """).fetchone()[0] > 0
        
        if dim_grupo_exists:
            # Verificar correspondência
            correspondem = conn.execute("""
                SELECT COUNT(DISTINCT ds.incategoria)
                FROM despesa_saldo ds
                INNER JOIN dim_grupo_despesa dgd ON ds.incategoria = dgd.cogrupo
                WHERE ds.incategoria IS NOT NULL
            """).fetchone()[0]
            
            total_distintos = conn.execute("""
                SELECT COUNT(DISTINCT incategoria)
                FROM despesa_saldo
                WHERE incategoria IS NOT NULL
            """).fetchone()[0]
            
            print(f"   Total de valores distintos: {total_distintos}")
            print(f"   Valores que correspondem em dim_grupo_despesa: {correspondem}")
            
            if correspondem == total_distintos:
                print("   ✅ PERFEITO! Todos os valores correspondem a cogrupo em dim_grupo_despesa!")
            else:
                print(f"   ⚠️ ATENÇÃO: {total_distintos - correspondem} valores não correspondem")
                
                # Mostrar valores que não correspondem
                nao_correspondem = conn.execute("""
                    SELECT DISTINCT ds.incategoria
                    FROM despesa_saldo ds
                    LEFT JOIN dim_grupo_despesa dgd ON ds.incategoria = dgd.cogrupo
                    WHERE ds.incategoria IS NOT NULL
                    AND dgd.cogrupo IS NULL
                    LIMIT 10
                """).fetchall()
                
                if nao_correspondem:
                    print("\n   Valores que NÃO correspondem:")
                    for (val,) in nao_correspondem:
                        print(f"   - {val}")
        else:
            print("   ❌ Tabela dim_grupo_despesa não encontrada!")
        
        # 5. Confirmar a alteração
        print("\n" + "="*60)
        print("⚠️  ATENÇÃO: Esta operação irá:")
        print("   1. Renomear a coluna 'incategoria' para 'cogrupo'")
        print("   2. Manter todos os dados intactos")
        print("   3. Permitir o relacionamento correto com dim_grupo_despesa")
        print("="*60)
        
        resposta = input("\n❓ Confirma a alteração? (s/N): ")
        if resposta.lower() != 's':
            print("\n❌ Operação cancelada.")
            return False
        
        # 6. Fazer backup dos dados (criar tabela temporária)
        print("\n💾 Criando backup temporário...")
        conn.execute("""
            CREATE TABLE despesa_saldo_backup AS 
            SELECT * FROM despesa_saldo
        """)
        print("   ✅ Backup criado em 'despesa_saldo_backup'")
        
        # 7. Executar a alteração
        print("\n🔧 Renomeando coluna...")
        conn.execute("ALTER TABLE despesa_saldo RENAME COLUMN incategoria TO cogrupo")
        print("   ✅ Coluna renomeada com sucesso!")
        
        # 8. Verificar resultado
        print("\n📋 Verificando resultado...")
        novas_colunas = conn.execute("""
            SELECT column_name
            FROM information_schema.columns 
            WHERE table_name = 'despesa_saldo'
            AND column_name IN ('incategoria', 'cogrupo')
        """).fetchall()
        
        tem_cogrupo_agora = any(col[0] == 'cogrupo' for col in novas_colunas)
        tem_incategoria_agora = any(col[0] == 'incategoria' for col in novas_colunas)
        
        if tem_cogrupo_agora and not tem_incategoria_agora:
            print("   ✅ Sucesso! Coluna 'cogrupo' existe e 'incategoria' foi removida")
            
            # Testar novo relacionamento
            if dim_grupo_exists:
                print("\n🔍 Testando novo relacionamento com dim_grupo_despesa...")
                orfaos_novo = conn.execute("""
                    SELECT COUNT(DISTINCT ds.cogrupo)
                    FROM despesa_saldo ds
                    LEFT JOIN dim_grupo_despesa dgd ON ds.cogrupo = dgd.cogrupo
                    WHERE ds.cogrupo IS NOT NULL
                    AND dgd.cogrupo IS NULL
                """).fetchone()[0]
                
                if orfaos_novo == 0:
                    print("   ✅ PERFEITO! Nenhum valor órfão com dim_grupo_despesa!")
                else:
                    print(f"   ⚠️ Ainda existem {orfaos_novo} valores órfãos")
            
            # Remover backup se tudo OK
            resposta = input("\n❓ Remover tabela de backup? (S/n): ")
            if resposta.lower() != 'n':
                conn.execute("DROP TABLE despesa_saldo_backup")
                print("   ✅ Backup removido")
            else:
                print("   ℹ️ Backup mantido em 'despesa_saldo_backup'")
            
            return True
        else:
            print("   ❌ ERRO: Algo deu errado na alteração!")
            print("   Use a tabela 'despesa_saldo_backup' para restaurar se necessário")
            return False
        
    except Exception as e:
        print(f"\n❌ ERRO durante a correção: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Função principal"""
    print("\n🔧 CORREÇÃO DE NOME DE COLUNA")
    print("Este script irá renomear a coluna 'incategoria' para 'cogrupo'")
    print("na tabela despesa_saldo, corrigindo o relacionamento com dim_grupo_despesa\n")
    
    if corrigir_coluna_despesa_saldo():
        print("\n🎉 Correção concluída com sucesso!")
        print("\n📌 Próximos passos:")
        print("   1. Execute novamente a verificação de integridade:")
        print("      python scripts/verificar_integridade_duckdb.py")
        print("   2. A coluna agora deve se relacionar corretamente com dim_grupo_despesa")
        print("\n⚠️ IMPORTANTE: Se você recarregar o Excel futuramente,")
        print("   lembre-se de corrigir o nome da coluna no arquivo também!")
    else:
        print("\n❌ Falha na correção.")

if __name__ == "__main__":
    main()