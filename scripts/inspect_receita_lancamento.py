"""
Script para analisar estrutura do arquivo ReceitaLancamento.xlsx
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path
from datetime import datetime

def inspect_receita_lancamento():
    """Analisa o arquivo ReceitaLancamento.xlsx"""
    
    # Caminho do arquivo
    file_path = Path("dados_brutos/fato/ReceitaLancamento.xlsx")
    
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        print(f"   Verifique se o arquivo está em: {file_path.absolute()}")
        return
    
    print("=" * 80)
    print("ANÁLISE DO ARQUIVO: ReceitaLancamento.xlsx")
    print("=" * 80)
    print(f"Data da análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Ler o arquivo
        print("\n📖 Lendo arquivo Excel...")
        df = pd.read_excel(file_path)
        
        # Informações básicas
        print(f"\n📊 INFORMAÇÕES BÁSICAS:")
        print(f"   - Total de linhas: {len(df):,}")
        print(f"   - Total de colunas: {len(df.columns)}")
        print(f"   - Tamanho em memória: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        print(f"\n📋 COLUNAS ENCONTRADAS:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. {col}")
        
        # Análise de tipos de dados
        print(f"\n📈 TIPOS DE DADOS:")
        for col in df.columns:
            tipo = df[col].dtype
            nulls = df[col].isnull().sum()
            print(f"   - {col}: {tipo} (nulls: {nulls:,})")
        
        # Amostra de dados
        print(f"\n📝 PRIMEIRAS 5 LINHAS:")
        print(df.head())
        
        # Valores únicos em colunas importantes
        print(f"\n🔍 ANÁLISE DE VALORES ÚNICOS:")
        
        # Verificar colunas de período/data
        colunas_periodo = ['COEXERCICIO', 'INMES', 'ANO', 'MES', 'DTLANCAMENTO', 
                          'DATA', 'DT_LANCAMENTO', 'PERIODO']
        for col in colunas_periodo:
            if col in df.columns:
                valores = df[col].unique()
                print(f"\n   {col}:")
                print(f"   - Total de valores únicos: {len(valores)}")
                
                # Se for data, mostrar range
                if 'DT' in col or 'DATA' in col:
                    try:
                        datas = pd.to_datetime(df[col])
                        print(f"   - Data mínima: {datas.min()}")
                        print(f"   - Data máxima: {datas.max()}")
                    except:
                        print(f"   - Valores: {sorted(valores)[:10]}")
                else:
                    print(f"   - Valores: {sorted(valores)[:10]}")
                    
                if len(valores) > 10:
                    print(f"   - ... e mais {len(valores) - 10} valores")
        
        # Verificar colunas de conta/classificação
        print(f"\n💳 ANÁLISE DE CAMPOS DE CONTA/CLASSIFICAÇÃO:")
        colunas_conta = []
        for col in df.columns:
            if any(termo in col.upper() for termo in ['CONTA', 'CLASS', 'RECEITA', 'FONTE']):
                colunas_conta.append(col)
        
        for col in colunas_conta:
            print(f"\n   {col}:")
            # Analisar tamanhos se for string
            if df[col].dtype == 'object':
                df['temp_len'] = df[col].astype(str).str.len()
                tamanhos = df['temp_len'].value_counts().sort_index()
                print(f"   - Tamanhos encontrados:")
                for tam, qtd in tamanhos.items():
                    if qtd > 0:  # Só mostrar tamanhos que existem
                        print(f"      {tam} chars: {qtd:,} registros")
                        # Mostrar exemplo
                        exemplo = df[df['temp_len'] == tam][col].iloc[0]
                        print(f"      Exemplo: {exemplo}")
                df.drop('temp_len', axis=1, inplace=True)
            else:
                # Se for numérico, mostrar range
                print(f"   - Min: {df[col].min()}")
                print(f"   - Max: {df[col].max()}")
                print(f"   - Valores únicos: {df[col].nunique()}")
        
        # Análise de valores monetários
        print(f"\n💰 COLUNAS NUMÉRICAS/MONETÁRIAS:")
        colunas_valor = []
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                # Verificar se parece ser valor monetário
                if any(termo in col.upper() for termo in ['VALOR', 'SALDO', 'LANC', 'RECEITA']):
                    colunas_valor.append(col)
        
        for col in colunas_valor:
            print(f"\n   {col}:")
            print(f"   - Min: R$ {df[col].min():,.2f}")
            print(f"   - Max: R$ {df[col].max():,.2f}")
            print(f"   - Soma: R$ {df[col].sum():,.2f}")
            print(f"   - Média: R$ {df[col].mean():,.2f}")
            print(f"   - Zeros: {(df[col] == 0).sum():,}")
            print(f"   - Negativos: {(df[col] < 0).sum():,}")
        
        # Verificar UGs
        colunas_ug = ['COUG', 'UG', 'UNIDADE']
        for col in colunas_ug:
            if col in df.columns:
                print(f"\n🏢 ANÁLISE DE UGs ({col}):")
                ugs = df[col].value_counts().head(10)
                print(f"   - Total de UGs únicas: {df[col].nunique()}")
                print(f"   - Top 10 UGs com mais registros:")
                for ug, qtd in ugs.items():
                    print(f"      {ug}: {qtd:,} registros")
        
        # Análise de possível estrutura hierárquica
        print(f"\n🌳 ANÁLISE DE ESTRUTURA HIERÁRQUICA:")
        # Procurar por colunas que possam indicar hierarquia
        for col in df.columns:
            if any(termo in col.upper() for termo in ['GRUPO', 'CATEGORIA', 'TIPO', 'NATUREZA']):
                print(f"\n   {col}:")
                print(f"   - Valores únicos: {df[col].nunique()}")
                top_valores = df[col].value_counts().head(5)
                for valor, qtd in top_valores.items():
                    print(f"      {valor}: {qtd:,} registros")
        
        # Salvar amostra
        print(f"\n💾 Salvando amostra dos dados...")
        amostra_path = "scripts/amostra_receitalancamento.xlsx"
        
        # Criar amostra com variedade de dados
        # Pegar algumas linhas de cada mês/período se existir
        if 'INMES' in df.columns:
            amostra = pd.DataFrame()
            for mes in sorted(df['INMES'].unique()):
                amostra = pd.concat([amostra, df[df['INMES'] == mes].head(5)])
            amostra = amostra.head(50)  # Limitar a 50 linhas
        else:
            amostra = df.head(50)
        
        amostra.to_excel(amostra_path, index=False)
        print(f"   ✅ Amostra salva em: {amostra_path}")
        print(f"   - Linhas na amostra: {len(amostra)}")
        
        # Sugestões baseadas na análise
        print(f"\n💡 SUGESTÕES PARA O ETL:")
        print("   1. Verificar se há colunas de período (COEXERCICIO, INMES)")
        print("   2. Identificar a coluna principal de valor")
        print("   3. Mapear as classificações de receita")
        print("   4. Verificar se há campos de data para transformar")
        print("   5. Analisar se precisa de parse especial em algum campo")
        
    except Exception as e:
        print(f"\n❌ Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_receita_lancamento()