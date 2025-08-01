"""
Script para analisar em detalhes a coluna COCONTACORRENTE
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from pathlib import Path

def analyze_cocontacorrente():
    """Analisa detalhadamente a coluna COCONTACORRENTE"""
    
    file_path = Path("dados_brutos/fato/ReceitaSaldo.xlsx")
    df = pd.read_excel(file_path)
    
    print("=" * 80)
    print("ANÁLISE DETALHADA DE COCONTACORRENTE")
    print("=" * 80)
    
    # Converter para string e analisar
    df['COCONTACORRENTE'] = df['COCONTACORRENTE'].astype(str)
    
    # Tamanhos reais
    df['tamanho_real'] = df['COCONTACORRENTE'].str.len()
    print(f"\n📏 TAMANHOS REAIS:")
    for tam, qtd in df['tamanho_real'].value_counts().sort_index().items():
        print(f"   {tam} chars: {qtd} registros")
    
    # Primeiros 10 valores únicos
    print(f"\n📝 PRIMEIROS 10 VALORES ÚNICOS:")
    for i, valor in enumerate(df['COCONTACORRENTE'].unique()[:10], 1):
        print(f"   {i}. '{valor}' (tamanho: {len(valor)})")
    
    # Análise de padrões
    print(f"\n🔍 ANÁLISE DE PADRÕES:")
    
    # Verificar se todos começam com número
    comeca_numero = df['COCONTACORRENTE'].str.match(r'^\d').all()
    print(f"   Todos começam com número? {comeca_numero}")
    
    # Verificar se há apenas números
    apenas_numeros = df['COCONTACORRENTE'].str.match(r'^\d+$').all()
    print(f"   Apenas números? {apenas_numeros}")
    
    # Distribuição por tamanho e primeiros caracteres
    print(f"\n📊 DISTRIBUIÇÃO POR COMPRIMENTO E PADRÃO:")
    for tam in sorted(df['tamanho_real'].unique()):
        subset = df[df['tamanho_real'] == tam]
        print(f"\n   Tamanho {tam} ({len(subset)} registros):")
        
        # Mostrar alguns exemplos
        exemplos = subset['COCONTACORRENTE'].unique()[:3]
        for ex in exemplos:
            print(f"      Exemplo: '{ex}'")
        
        # Se for 17 caracteres, testar o parse original
        if tam == 17:
            print(f"      Parse sugerido (17 chars):")
            ex = exemplos[0]
            print(f"        COCLASSEORC: '{ex[0:8]}'")
            print(f"        COFONTE: '{ex[8:18]}'")
    
    # Verificar valores com diferentes tamanhos
    tamanhos_interesse = [17, 38, 40]
    for tam in tamanhos_interesse:
        qtd = len(df[df['tamanho_real'] == tam])
        if qtd > 0:
            print(f"\n📌 CONTAS COM {tam} CARACTERES: {qtd} registros")
            amostra = df[df['tamanho_real'] == tam].head(3)
            for idx, row in amostra.iterrows():
                print(f"   '{row['COCONTACORRENTE']}'")

if __name__ == "__main__":
    analyze_cocontacorrente()