"""
Script para analisar estrutura do arquivo DespesaSaldo.xlsx
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path

def inspect_despesa_saldo():
    """Analisa o arquivo DespesaSaldo.xlsx"""
    
    # Caminho do arquivo
    file_path = Path("dados_brutos/fato/DespesaSaldo.xlsx")
    
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        return
    
    print("=" * 80)
    print("ANÁLISE DO ARQUIVO: DespesaSaldo.xlsx")
    print("=" * 80)
    
    try:
        # Ler o arquivo
        df = pd.read_excel(file_path)
        
        # Informações básicas
        print(f"\n📊 INFORMAÇÕES BÁSICAS:")
        print(f"   - Total de linhas: {len(df):,}")
        print(f"   - Total de colunas: {len(df.columns)}")
        print(f"\n📋 COLUNAS ENCONTRADAS:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        
        # Análise de tipos de dados
        print(f"\n📈 TIPOS DE DADOS:")
        for col in df.columns:
            print(f"   - {col}: {df[col].dtype}")
        
        # Amostra de dados
        print(f"\n📝 PRIMEIRAS 5 LINHAS:")
        print(df.head())
        
        # Valores únicos em colunas importantes
        print(f"\n🔍 ANÁLISE DE VALORES ÚNICOS:")
        
        # Verificar se tem coluna de período
        for col in ['COEXERCICIO', 'INMES', 'ANO', 'MES']:
            if col in df.columns:
                valores = df[col].unique()
                print(f"\n   {col}:")
                print(f"   - Valores únicos: {sorted(valores)[:10]}")  # Mostrar até 10
                if len(valores) > 10:
                    print(f"   - ... e mais {len(valores) - 10} valores")
        
        # Verificar colunas que parecem ser conta corrente
        print(f"\n💳 ANÁLISE DE CAMPOS ESPECIAIS:")
        for col in df.columns:
            if 'CONTA' in col.upper() or 'CORRENTE' in col.upper():
                # Analisar tamanhos
                df['temp_len'] = df[col].astype(str).str.len()
                tamanhos = df['temp_len'].value_counts().sort_index()
                print(f"\n   {col} - Tamanhos encontrados:")
                for tam, qtd in tamanhos.items():
                    print(f"      {tam} chars: {qtd:,} registros")
                    # Mostrar exemplo
                    exemplo = df[df['temp_len'] == tam][col].iloc[0]
                    print(f"      Exemplo: {exemplo}")
                df.drop('temp_len', axis=1, inplace=True)
        
        # Análise de valores monetários
        print(f"\n💰 COLUNAS NUMÉRICAS/MONETÁRIAS:")
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                print(f"\n   {col}:")
                print(f"   - Min: {df[col].min():,.2f}")
                print(f"   - Max: {df[col].max():,.2f}")
                print(f"   - Soma: {df[col].sum():,.2f}")
                print(f"   - Média: {df[col].mean():,.2f}")
        
        # Salvar amostra
        print(f"\n💾 Salvando amostra dos dados...")
        df.head(20).to_excel("scripts/amostra_despesasaldo.xlsx", index=False)
        print(f"   ✅ Amostra salva em: scripts/amostra_despesasaldo.xlsx")
        
    except Exception as e:
        print(f"\n❌ Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_despesa_saldo()