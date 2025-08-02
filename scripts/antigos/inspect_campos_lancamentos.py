"""
Script para inspecionar os campos das tabelas de lançamento
Mostra todos os campos com seus tipos de dados
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import db
import pandas as pd

def inspecionar_campos_tabela(schema, tabela):
    """Inspeciona e mostra os campos de uma tabela"""
    print(f"\n{'='*80}")
    print(f"TABELA: {schema}.{tabela}")
    print(f"{'='*80}")
    
    try:
        # Query para buscar informações das colunas
        query = """
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            numeric_precision,
            numeric_scale,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = %s 
        AND table_name = %s
        ORDER BY ordinal_position
        """
        
        df = db.read_sql(query, (schema, tabela))
        
        if df.empty:
            print(f"❌ Tabela {schema}.{tabela} não encontrada ou sem colunas!")
            return
        
        print(f"\n✅ Total de campos: {len(df)}")
        print("\nCAMPOS DA TABELA:")
        print("-" * 80)
        
        for idx, row in df.iterrows():
            # Formatar tipo de dado
            tipo = row['data_type']
            if row['character_maximum_length']:
                tipo += f"({row['character_maximum_length']})"
            elif row['numeric_precision']:
                if row['numeric_scale']:
                    tipo += f"({row['numeric_precision']},{row['numeric_scale']})"
                else:
                    tipo += f"({row['numeric_precision']})"
            
            # Nullable
            nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
            
            # Default
            default = f"DEFAULT {row['column_default']}" if row['column_default'] else ""
            
            print(f"{idx+1:3d}. {row['column_name']:30s} {tipo:20s} {nullable:10s} {default}")
        
        # Buscar também uma amostra de dados
        print("\n" + "-" * 80)
        print("AMOSTRA DE DADOS (5 primeiros registros):")
        print("-" * 80)
        
        sample_query = f"SELECT * FROM {schema}.{tabela} LIMIT 5"
        df_sample = db.read_sql(sample_query)
        
        if not df_sample.empty:
            # Mostrar apenas algumas colunas importantes
            colunas_importantes = ['dalancamento', 'dtlancamento', 'coexercicio', 'inmes', 
                                 'coug', 'cocontacontabil', 'nudocumento', 'coevento', 
                                 'valancamento', 'indebitocredito', 'tipo_lancamento']
            
            colunas_existentes = [col for col in colunas_importantes if col in df_sample.columns]
            
            if colunas_existentes:
                print("\nColunas principais:")
                for col in colunas_existentes:
                    print(f"\n{col}:")
                    for i, val in enumerate(df_sample[col].head()):
                        print(f"  [{i}] {val}")
        else:
            print("❌ Tabela vazia!")
            
    except Exception as e:
        print(f"❌ Erro ao inspecionar tabela: {str(e)}")

def verificar_totais():
    """Verifica totais de registros em cada tabela"""
    print("\n" + "="*80)
    print("TOTAIS DE REGISTROS")
    print("="*80)
    
    tabelas = [
        ('receitas', 'fato_receita_lancamento'),
        ('despesas', 'fato_despesa_lancamento')
    ]
    
    for schema, tabela in tabelas:
        try:
            query = f"SELECT COUNT(*) as total FROM {schema}.{tabela}"
            result = db.execute_query(query)
            total = result[0][0] if result else 0
            print(f"{schema}.{tabela}: {total:,} registros")
        except Exception as e:
            print(f"{schema}.{tabela}: Erro - {str(e)}")

def main():
    """Função principal"""
    print("\n🔍 INSPEÇÃO DE CAMPOS DAS TABELAS DE LANÇAMENTO")
    
    # Verificar totais primeiro
    verificar_totais()
    
    # Inspecionar tabela de receitas
    inspecionar_campos_tabela('receitas', 'fato_receita_lancamento')
    
    # Inspecionar tabela de despesas
    inspecionar_campos_tabela('despesas', 'fato_despesa_lancamento')
    
    print("\n✅ Inspeção concluída!")

if __name__ == "__main__":
    main()