"""
Script para analisar estrutura das planilhas Excel
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path

def analyze_receitasaldo():
    """Analisa o arquivo ReceitaSaldo.xlsx"""
    
    # Caminho do arquivo
    file_path = Path("dados_brutos/fato/ReceitaSaldo.xlsx")
    
    if not file_path.exists():
        print(f"❌ Arquivo não encontrado: {file_path}")
        return
    
    print("=" * 80)
    print("ANÁLISE DO ARQUIVO: ReceitaSaldo.xlsx")
    print("=" * 80)
    
    # Ler o arquivo
    df = pd.read_excel(file_path)
    
    # Informações básicas
    print(f"\n📊 INFORMAÇÕES BÁSICAS:")
    print(f"   - Total de linhas: {len(df):,}")
    print(f"   - Total de colunas: {len(df.columns)}")
    print(f"   - Colunas: {', '.join(df.columns)}")
    
    # Análise de períodos
    print(f"\n📅 ANÁLISE DE PERÍODOS:")
    print(f"   - Anos únicos: {sorted(df['COEXERCICIO'].unique())}")
    print(f"   - Meses únicos: {sorted(df['INMES'].unique())}")
    
    # Análise de COCONTACORRENTE
    print(f"\n🔍 ANÁLISE DE COCONTACORRENTE:")
    df['tamanho_conta'] = df['COCONTACORRENTE'].astype(str).str.len()
    tamanhos = df['tamanho_conta'].value_counts().sort_index()
    for tam, qtd in tamanhos.items():
        print(f"   - {tam} caracteres: {qtd:,} registros ({qtd/len(df)*100:.1f}%)")
    
    # Exemplos de cada tamanho
    print(f"\n📝 EXEMPLOS DE COCONTACORRENTE:")
    for tam in sorted(df['tamanho_conta'].unique()):
        exemplo = df[df['tamanho_conta'] == tam]['COCONTACORRENTE'].iloc[0]
        print(f"   - {tam} chars: {exemplo}")
    
    # Análise de COCONTACONTABIL
    print(f"\n💰 ANÁLISE DE COCONTACONTABIL (primeiro dígito):")
    df['primeiro_digito'] = df['COCONTACONTABIL'].astype(str).str[0]
    for digito, qtd in df['primeiro_digito'].value_counts().sort_index().items():
        print(f"   - Começam com {digito}: {qtd:,} registros")
    
    # Valores
    print(f"\n💵 ANÁLISE DE VALORES:")
    print(f"   - VACREDITO: {df['VACREDITO'].sum():,.2f}")
    print(f"   - VADEBITO: {df['VADEBITO'].sum():,.2f}")
    
    # Salvar amostra
    print(f"\n💾 Salvando amostra dos dados...")
    df.head(20).to_excel("scripts/amostra_receitasaldo.xlsx", index=False)
    print(f"   ✅ Amostra salva em: scripts/amostra_receitasaldo.xlsx")

if __name__ == "__main__":
    analyze_receitasaldo()