#!/usr/bin/env python3
"""
Script para corrigir a tabela dim_subtitulo no DuckDB
Recria a tabela com a chave primária correta (cosubtitulo)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import duckdb
from pathlib import Path
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def corrigir_dim_subtitulo():
    """Corrige a tabela dim_subtitulo com a chave correta"""
    
    db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
    arquivo_path = Path("dados_brutos/dimensao/Despesa_Subtitulo.xlsx")
    
    print("=" * 80)
    print("CORREÇÃO DA TABELA DIM_SUBTITULO")
    print("=" * 80)
    print(f"Banco de dados: {db_path}")
    print(f"Arquivo: {arquivo_path}")
    print()
    
    # Verificar se o arquivo existe
    if not arquivo_path.exists():
        print(f"❌ ERRO: Arquivo não encontrado: {arquivo_path}")
        return False
    
    if not db_path.exists():
        print(f"❌ ERRO: Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # Conectar ao banco
        conn = duckdb.connect(str(db_path))
        
        # 1. Verificar se a tabela existe
        table_exists = conn.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'dim_subtitulo'
        """).fetchone()[0] > 0
        
        if table_exists:
            print("📊 Tabela dim_subtitulo encontrada")
            
            # Verificar estrutura atual
            print("\n🔍 Estrutura atual da tabela:")
            colunas = conn.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'dim_subtitulo'
                ORDER BY ordinal_position
            """).fetchall()
            
            for col, tipo in colunas:
                print(f"   - {col} ({tipo})")
            
            # Contar registros
            count_antes = conn.execute("SELECT COUNT(*) FROM dim_subtitulo").fetchone()[0]
            print(f"\n📈 Registros atuais: {count_antes:,}")
            
            # Dropar tabela antiga
            print("\n🗑️ Removendo tabela antiga...")
            conn.execute("DROP TABLE dim_subtitulo")
            print("   ✅ Tabela removida")
        else:
            print("ℹ️ Tabela dim_subtitulo não existe (será criada)")
        
        # 2. Ler o arquivo Excel correto
        print("\n📖 Lendo arquivo Excel...")
        df = pd.read_excel(arquivo_path)
        print(f"   Linhas: {len(df):,}")
        print(f"   Colunas originais: {', '.join(df.columns)}")
        
        # Converter colunas para minúsculas
        df.columns = df.columns.str.lower()
        print(f"   Colunas (minúsculas): {', '.join(df.columns)}")
        
        # Verificar se cosubtitulo existe
        if 'cosubtitulo' not in df.columns:
            print(f"\n❌ ERRO: Coluna 'cosubtitulo' não encontrada!")
            print(f"   Colunas disponíveis: {', '.join(df.columns)}")
            return False
        
        # 3. Criar nova tabela
        print("\n📝 Criando nova tabela dim_subtitulo...")
        conn.register('df_temp', df)
        conn.execute("""
            CREATE TABLE dim_subtitulo AS 
            SELECT * FROM df_temp
        """)
        conn.unregister('df_temp')
        
        # 4. Verificar duplicatas antes de criar índice
        print("\n🔍 Verificando integridade da chave primária...")
        duplicatas = conn.execute("""
            SELECT cosubtitulo, COUNT(*) as qtd 
            FROM dim_subtitulo 
            GROUP BY cosubtitulo 
            HAVING COUNT(*) > 1
        """).fetchall()
        
        if duplicatas:
            print(f"   ⚠️ AVISO: Encontradas {len(duplicatas)} chaves duplicadas")
            for cod, qtd in duplicatas[:5]:  # Mostrar até 5 exemplos
                print(f"      - cosubtitulo '{cod}': {qtd} ocorrências")
        else:
            print("   ✅ Sem duplicatas - criando índice único...")
            conn.execute("""
                CREATE UNIQUE INDEX idx_dim_subtitulo_cosubtitulo 
                ON dim_subtitulo(cosubtitulo)
            """)
            print("   🔑 Índice único criado com sucesso!")
        
        # 5. Verificar resultado
        count_depois = conn.execute("SELECT COUNT(*) FROM dim_subtitulo").fetchone()[0]
        print(f"\n✅ Tabela recriada com sucesso!")
        print(f"   Total de registros: {count_depois:,}")
        
        # Mostrar nova estrutura
        print("\n📋 Nova estrutura da tabela:")
        colunas_novas = conn.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'dim_subtitulo'
            ORDER BY ordinal_position
        """).fetchall()
        
        for col, tipo in colunas_novas:
            marca = "🔑" if col == "cosubtitulo" else "  "
            print(f"   {marca} {col} ({tipo})")
        
        # 6. Testar integridade com tabelas fato
        print("\n🔄 Testando integridade com tabelas fato...")
        
        for tabela_fato in ['despesa_lancamento', 'despesa_saldo']:
            # Verificar se a coluna cosubtitulo existe
            col_exists = conn.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = '{tabela_fato}' 
                AND column_name = 'cosubtitulo'
            """).fetchone()[0] > 0
            
            if col_exists:
                # Verificar valores órfãos
                orfaos = conn.execute(f"""
                    SELECT COUNT(DISTINCT f.cosubtitulo)
                    FROM {tabela_fato} f
                    LEFT JOIN dim_subtitulo d ON f.cosubtitulo = d.cosubtitulo
                    WHERE f.cosubtitulo IS NOT NULL
                    AND d.cosubtitulo IS NULL
                """).fetchone()[0]
                
                if orfaos > 0:
                    print(f"   ⚠️ {tabela_fato}: {orfaos} valores órfãos encontrados")
                else:
                    print(f"   ✅ {tabela_fato}: Integridade OK!")
            else:
                print(f"   ➖ {tabela_fato}: Coluna cosubtitulo não existe")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO durante a correção: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("\n🔧 CORREÇÃO DA TABELA DIM_SUBTITULO")
    print("Este script irá:")
    print("  1. Remover a tabela dim_subtitulo existente")
    print("  2. Recarregar do arquivo Despesa_Subtitulo.xlsx")
    print("  3. Usar 'cosubtitulo' como chave primária")
    print("  4. Verificar integridade com as tabelas fato\n")
    
    resposta = input("Confirma a correção? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Operação cancelada.")
        return
    
    print()
    if corrigir_dim_subtitulo():
        print("\n🎉 Correção concluída com sucesso!")
        print("\n📌 Próximos passos:")
        print("   1. Execute novamente a verificação de integridade:")
        print("      python scripts/verificar_integridade_duckdb.py")
        print("   2. Se necessário, corrija os outros problemas identificados")
    else:
        print("\n❌ Falha na correção.")

if __name__ == "__main__":
    main()