"""
Script para analisar estrutura do arquivo DespesaLancamento.xlsx
Baseado no inspect_receita_lancamento.py
OTIMIZADO para arquivos grandes (1M+ linhas) - analisa apenas amostra de 10.000 linhas
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path
from datetime import datetime

def inspect_despesa_lancamento():
    """Analisa o arquivo DespesaLancamento.xlsx"""
    
    # Caminho do arquivo (relativo à raiz do projeto)
    file_path = Path("dados_brutos/fato/DespesaLancamento.xlsx")
    
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        print(f"   Verifique se o arquivo está em: {file_path.absolute()}")
        return
    
    print("=" * 80)
    print("ANÁLISE DO ARQUIVO: DespesaLancamento.xlsx")
    print("=" * 80)
    print(f"Data da análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Ler o arquivo - APENAS AMOSTRA para arquivos grandes
        print("\n📖 Lendo arquivo Excel (amostra de 10.000 linhas)...")
        # Primeiro, vamos ver o tamanho total sem carregar tudo
        df_info = pd.read_excel(file_path, nrows=1)
        print(f"   - Colunas detectadas: {len(df_info.columns)}")
        
        # Agora ler apenas 10.000 linhas para análise
        df = pd.read_excel(file_path, nrows=10000)
        print(f"   ⚡ Carregando apenas primeiras 10.000 linhas para análise rápida")
        
        # Informações básicas
        print(f"\n📊 INFORMAÇÕES BÁSICAS:")
        print(f"   - Linhas analisadas: {len(df):,} (amostra)")
        print(f"   - Total estimado no arquivo: ~1.000.000 linhas")
        print(f"   - Total de colunas: {len(df.columns)}")
        print(f"   - Tamanho da amostra em memória: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
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
                          'DATA', 'DT_LANCAMENTO', 'PERIODO', 'DTLIQUIDACAO']
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
        
        # Verificar colunas de conta/classificação específicas de despesa
        print(f"\n💳 ANÁLISE DE CAMPOS DE CONTA/CLASSIFICAÇÃO:")
        colunas_conta = []
        for col in df.columns:
            if any(termo in col.upper() for termo in ['CONTA', 'CLASS', 'DESPESA', 'FONTE', 
                                                       'NATUREZA', 'ELEMENTO', 'MODALIDADE']):
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
        
        # Análise de valores monetários (foco em despesa)
        print(f"\n💰 COLUNAS NUMÉRICAS/MONETÁRIAS:")
        colunas_valor = []
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                # Verificar se parece ser valor monetário
                if any(termo in col.upper() for termo in ['VALOR', 'SALDO', 'LANC', 'DESPESA', 
                                                          'EMPENHO', 'LIQUIDACAO', 'PAGAMENTO']):
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
        
        # Análise específica de despesa
        print(f"\n💸 ANÁLISE ESPECÍFICA DE DESPESA:")
        
        # Procurar por tipos de despesa
        colunas_tipo_despesa = ['TIPO', 'TIPODESPESA', 'TIPO_DESPESA', 'INDEBITOCREDITO']
        for col in colunas_tipo_despesa:
            if col in df.columns:
                print(f"\n   {col}:")
                valores = df[col].value_counts()
                for valor, qtd in valores.items():
                    print(f"      {valor}: {qtd:,} registros")
        
        # Procurar por documentos fiscais
        colunas_doc = ['NUDOCUMENTO', 'DOCUMENTO', 'NOTA', 'NF', 'EMPENHO', 'NUEMPENHO']
        for col in colunas_doc:
            if col in df.columns:
                print(f"\n   {col}:")
                print(f"   - Total de documentos únicos: {df[col].nunique()}")
                print(f"   - Amostra: {df[col].head(5).tolist()}")
        
        # Análise de estrutura hierárquica de despesa
        print(f"\n🌳 ANÁLISE DE ESTRUTURA HIERÁRQUICA DE DESPESA:")
        # Procurar por colunas específicas de despesa
        for col in df.columns:
            if any(termo in col.upper() for termo in ['FUNCAO', 'SUBFUNCAO', 'PROGRAMA', 
                                                       'PROJETO', 'ATIVIDADE', 'OPERACAO']):
                print(f"\n   {col}:")
                print(f"   - Valores únicos: {df[col].nunique()}")
                top_valores = df[col].value_counts().head(5)
                for valor, qtd in top_valores.items():
                    print(f"      {valor}: {qtd:,} registros")
        
        # Verificar eventos específicos de despesa
        colunas_evento = ['COEVENTO', 'EVENTO', 'TIPOEVENTO']
        for col in colunas_evento:
            if col in df.columns:
                print(f"\n   {col}:")
                eventos = df[col].value_counts().head(10)
                print(f"   - Total de eventos únicos: {df[col].nunique()}")
                print(f"   - Top 10 eventos:")
                for evento, qtd in eventos.items():
                    print(f"      {evento}: {qtd:,} registros")
        
        # Salvar amostra
        print(f"\n💾 Salvando amostra dos dados...")
        amostra_path = "scripts/amostra_despesalancamento.xlsx"
        
        # Criar amostra com variedade de dados
        # Pegar algumas linhas de cada mês/período se existir
        print(f"   - Usando dados já carregados (primeiras 10.000 linhas)")
        if 'INMES' in df.columns:
            amostra = pd.DataFrame()
            meses_unicos = sorted(df['INMES'].unique())
            print(f"   - Meses encontrados na amostra: {meses_unicos}")
            for mes in meses_unicos:
                linhas_mes = df[df['INMES'] == mes].head(5)
                amostra = pd.concat([amostra, linhas_mes])
            amostra = amostra.head(50)  # Limitar a 50 linhas
        else:
            amostra = df.head(50)
        
        amostra.to_excel(amostra_path, index=False)
        print(f"   ✅ Amostra salva em: {amostra_path}")
        print(f"   - Linhas na amostra: {len(amostra)}")
        
        # Análise de possíveis estágios da despesa
        print(f"\n📊 ANÁLISE DE ESTÁGIOS DA DESPESA:")
        estagios = ['EMPENHO', 'LIQUIDACAO', 'PAGAMENTO']
        for estagio in estagios:
            colunas_estagio = [col for col in df.columns if estagio in col.upper()]
            if colunas_estagio:
                print(f"\n   Estágio: {estagio}")
                for col in colunas_estagio:
                    print(f"   - {col}")
        
        # Sugestões baseadas na análise
        print(f"\n💡 SUGESTÕES PARA O ETL:")
        print("   1. Verificar se há colunas de período (COEXERCICIO, INMES)")
        print("   2. Identificar se há diferentes estágios de despesa (empenho, liquidação, pagamento)")
        print("   3. Mapear as classificações orçamentárias (função, subfunção, programa, etc.)")
        print("   4. Analisar o campo COCONTACORRENTE para parse (17, 38 ou 40 chars)")
        print("   5. Verificar se há campo INDEBITOCREDITO para tipo de lançamento")
        print("   6. Identificar campos de natureza da despesa para parse")
        print("   7. Mapear campos de documento fiscal/empenho")
        
    except Exception as e:
        print(f"\n❌ Erro ao processar arquivo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_despesa_lancamento()