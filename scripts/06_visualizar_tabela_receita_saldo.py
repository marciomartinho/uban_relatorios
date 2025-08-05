#!/usr/bin/env python3
"""
Script para visualizar os primeiros 50 registros da tabela receita_saldo
Mostra os dados de forma organizada e permite exportar para Excel
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
from pathlib import Path
from datetime import datetime
import pandas as pd

def visualizar_registros():
    """Mostra os primeiros 50 registros da tabela receita_saldo"""
    
    # Caminho do banco
    db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
    
    print("=" * 80)
    print("VISUALIZAÇÃO - PRIMEIROS 50 REGISTROS DE RECEITA_SALDO")
    print("=" * 80)
    print(f"Banco de dados: {db_path}")
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    # Verificar se o banco existe
    if not db_path.exists():
        print(f"❌ ERRO: Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # Conectar ao banco
        conn = duckdb.connect(str(db_path), read_only=True)
        
        # Verificar se a tabela existe
        table_exists = conn.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_name = 'receita_saldo'
        """).fetchone()[0] > 0
        
        if not table_exists:
            print("❌ ERRO: Tabela 'receita_saldo' não encontrada!")
            return False
        
        # Contar total de registros
        total_registros = conn.execute("SELECT COUNT(*) FROM receita_saldo").fetchone()[0]
        print(f"📊 Total de registros na tabela: {total_registros:,}\n")
        
        # Buscar os primeiros 50 registros
        print("🔍 Buscando os primeiros 50 registros...")
        query = """
        SELECT * 
        FROM receita_saldo 
        ORDER BY periodo, coexercicio, inmes, coug
        LIMIT 50
        """
        
        # Carregar em DataFrame para melhor visualização
        df = pd.read_sql(query, conn)
        
        print(f"✅ {len(df)} registros carregados\n")
        
        # Mostrar informações sobre as colunas
        print("📋 ESTRUTURA DOS DADOS:")
        print("-" * 60)
        print(f"Total de colunas: {len(df.columns)}")
        print("\nColunas disponíveis:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i:2d}. {col}")
        print()
        
        # Menu de opções
        while True:
            print("\n" + "=" * 60)
            print("OPÇÕES DE VISUALIZAÇÃO:")
            print("=" * 60)
            print("1. Ver resumo estatístico")
            print("2. Ver primeiros 10 registros (todas as colunas)")
            print("3. Ver colunas principais de saldo")
            print("4. Ver análise de saldos (crédito, débito, saldo contábil)")
            print("5. Ver registros de um período específico")
            print("6. Exportar todos os 50 registros para Excel")
            print("7. Ver registro específico (por índice)")
            print("8. Ver totais por UG")
            print("9. Análise de parsing de conta corrente (receita)")
            print("0. Sair")
            
            opcao = input("\n➤ Escolha uma opção: ")
            
            if opcao == '0':
                break
                
            elif opcao == '1':
                print("\n📊 RESUMO ESTATÍSTICO:")
                print("-" * 60)
                
                # Estatísticas de saldos
                print("\nValores de Crédito:")
                print(df['vacredito'].describe())
                
                print("\nValores de Débito:")
                print(df['vadebito'].describe())
                
                print("\nSaldo Contábil Receita:")
                print(df['saldo_contabil_receita'].describe())
                
                # Períodos
                print(f"\nPeríodos únicos: {df['periodo'].nunique()}")
                print(f"Período mínimo: {df['periodo'].min()}")
                print(f"Período máximo: {df['periodo'].max()}")
                
                # UGs
                print(f"\nUGs únicas: {df['coug'].nunique()}")
                
                # Contas contábeis
                print(f"Contas contábeis únicas: {df['cocontacontabil'].nunique()}")
                
            elif opcao == '2':
                print("\n📄 PRIMEIROS 10 REGISTROS (TODAS AS COLUNAS):")
                print("-" * 60)
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', 30)
                print(df.head(10))
                
            elif opcao == '3':
                print("\n📋 COLUNAS PRINCIPAIS DE SALDO (RECEITA):")
                print("-" * 60)
                
                # Selecionar colunas principais para saldo de receita
                colunas_principais = [
                    'periodo', 'coug', 'cocontacontabil', 
                    'vacredito', 'vadebito', 'saldo_contabil_receita',
                    'coclasseorc', 'cocategoriareceita', 'cofontereceita',
                    'corubrica', 'coalinea'
                ]
                
                # Filtrar apenas colunas que existem
                colunas_mostrar = [col for col in colunas_principais if col in df.columns]
                
                print(df[colunas_mostrar].head(20).to_string(index=True))
                
            elif opcao == '4':
                print("\n💰 ANÁLISE DE SALDOS:")
                print("-" * 60)
                
                # Totais gerais
                total_credito = df['vacredito'].sum()
                total_debito = df['vadebito'].sum()
                total_saldo = df['saldo_contabil_receita'].sum()
                
                print(f"\nTOTAIS GERAIS (50 registros):")
                print(f"  Total Crédito: R$ {total_credito:,.2f}")
                print(f"  Total Débito: R$ {total_debito:,.2f}")
                print(f"  Saldo Total: R$ {total_saldo:,.2f}")
                
                # Registros com maiores saldos
                print(f"\n5 MAIORES SALDOS:")
                maiores = df.nlargest(5, 'saldo_contabil_receita')[
                    ['coug', 'cocontacontabil', 'saldo_contabil_receita', 'periodo']
                ]
                for idx, row in maiores.iterrows():
                    print(f"  UG: {row['coug']} | Conta: {row['cocontacontabil']} | "
                          f"Saldo: R$ {row['saldo_contabil_receita']:,.2f} | "
                          f"Período: {row['periodo']}")
                
                # Registros com saldo negativo
                negativos = df[df['saldo_contabil_receita'] < 0]
                if len(negativos) > 0:
                    print(f"\n⚠️ REGISTROS COM SALDO NEGATIVO: {len(negativos)}")
                    print(negativos[['coug', 'cocontacontabil', 'saldo_contabil_receita']].head(5))
                
                # Análise por conta contábil (primeiro dígito)
                df['primeiro_digito'] = df['cocontacontabil'].astype(str).str[0]
                print("\n📊 SALDOS POR PRIMEIRO DÍGITO DA CONTA:")
                for digito in sorted(df['primeiro_digito'].unique()):
                    mask = df['primeiro_digito'] == digito
                    total = df[mask]['saldo_contabil_receita'].sum()
                    qtd = mask.sum()
                    print(f"  Dígito {digito}: {qtd} registros - R$ {total:,.2f}")
                
            elif opcao == '5':
                periodos_unicos = sorted(df['periodo'].unique())
                print(f"\n📅 Períodos disponíveis: {', '.join(map(str, periodos_unicos))}")
                periodo = input("Digite o período (YYYY-MM): ")
                
                if periodo in periodos_unicos:
                    registros_periodo = df[df['periodo'] == periodo]
                    print(f"\n📊 Registros do período {periodo}: {len(registros_periodo)}")
                    
                    # Resumo do período
                    print("\nRESUMO DO PERÍODO:")
                    print(f"  Total Crédito: R$ {registros_periodo['vacredito'].sum():,.2f}")
                    print(f"  Total Débito: R$ {registros_periodo['vadebito'].sum():,.2f}")
                    print(f"  Saldo Total: R$ {registros_periodo['saldo_contabil_receita'].sum():,.2f}")
                    
                    print("\nPrimeiros 10 registros:")
                    print(registros_periodo[['coug', 'cocontacontabil', 'vacredito', 
                                            'vadebito', 'saldo_contabil_receita']].head(10))
                else:
                    print(f"\n❌ Período '{periodo}' não encontrado nos dados!")
                
            elif opcao == '6':
                nome_arquivo = f"receita_saldo_50_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
                print(f"\n💾 Exportando para Excel: {nome_arquivo}")
                
                # Criar Excel com formatação
                with pd.ExcelWriter(nome_arquivo, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Dados', index=False)
                    
                    # Adicionar uma aba com resumo
                    resumo = pd.DataFrame({
                        'Informação': [
                            'Total de registros',
                            'Período inicial',
                            'Período final',
                            'Total de UGs',
                            'Contas contábeis únicas',
                            'Soma dos créditos',
                            'Soma dos débitos',
                            'Saldo contábil total',
                            'Média do saldo contábil',
                            'Registros com saldo negativo'
                        ],
                        'Valor': [
                            len(df),
                            df['periodo'].min(),
                            df['periodo'].max(),
                            df['coug'].nunique(),
                            df['cocontacontabil'].nunique(),
                            f"R$ {df['vacredito'].sum():,.2f}",
                            f"R$ {df['vadebito'].sum():,.2f}",
                            f"R$ {df['saldo_contabil_receita'].sum():,.2f}",
                            f"R$ {df['saldo_contabil_receita'].mean():,.2f}",
                            len(df[df['saldo_contabil_receita'] < 0])
                        ]
                    })
                    resumo.to_excel(writer, sheet_name='Resumo', index=False)
                
                print(f"✅ Arquivo exportado com sucesso!")
                print(f"📄 Arquivo: {nome_arquivo}")
                
            elif opcao == '7':
                try:
                    idx = int(input("\nDigite o índice do registro (0-49): "))
                    if 0 <= idx < len(df):
                        print(f"\n📋 REGISTRO {idx}:")
                        print("-" * 60)
                        registro = df.iloc[idx]
                        for col, valor in registro.items():
                            print(f"{col}: {valor}")
                    else:
                        print(f"\n❌ Índice inválido! Use valores entre 0 e {len(df)-1}")
                except ValueError:
                    print("\n❌ Digite um número válido!")
            
            elif opcao == '8':
                print("\n🏢 TOTAIS POR UG (nos 50 registros):")
                print("-" * 60)
                
                totais_ug = df.groupby('coug').agg({
                    'vacredito': 'sum',
                    'vadebito': 'sum',
                    'saldo_contabil_receita': 'sum'
                }).round(2)
                
                totais_ug = totais_ug.sort_values('saldo_contabil_receita', ascending=False)
                
                print(f"{'UG':<10} {'Crédito':>20} {'Débito':>20} {'Saldo':>20}")
                print("-" * 70)
                
                for ug, row in totais_ug.iterrows():
                    print(f"{ug:<10} {row['vacredito']:>20,.2f} "
                          f"{row['vadebito']:>20,.2f} "
                          f"{row['saldo_contabil_receita']:>20,.2f}")
                          
            elif opcao == '9':
                print("\n🔍 ANÁLISE DE PARSING DE CONTA CORRENTE (RECEITA SALDO):")
                print("-" * 60)
                
                # Verificar tamanhos de conta corrente
                df['tamanho_conta'] = df['cocontacorrente'].astype(str).str.len()
                tamanhos = df['tamanho_conta'].value_counts().sort_index()
                
                print("Distribuição de tamanhos:")
                for tam, qtd in tamanhos.items():
                    print(f"  {tam} caracteres: {qtd} registros")
                
                # Análise para contas de 17 chars (padrão receita)
                df_17 = df[df['tamanho_conta'] == 17]
                if len(df_17) > 0:
                    print(f"\n📊 Contas de 17 caracteres: {len(df_17)}")
                    print("  Campos parseados:")
                    print("  - coclasseorc (0:8) - Classificação orçamentária")
                    print("  - cofonte (8:18) - Fonte")
                    print("  - Subcampos da classificação:")
                    print("    • cocategoriareceita (0:1)")
                    print("    • cofontereceita (0:2)")
                    print("    • cosubfontereceita (0:3)")
                    print("    • corubrica (0:4)")
                    print("    • coalinea (0:6)")
                    
                    # Análise de classificações
                    if 'coclasseorc' in df_17.columns:
                        print("\n  Classificações orçamentárias únicas:")
                        class_unicas = df_17['coclasseorc'].nunique()
                        print(f"    Total: {class_unicas}")
                        
                        # Categorias de receita
                        if 'cocategoriareceita' in df_17.columns:
                            cats = df_17['cocategoriareceita'].value_counts()
                            print("\n  Categorias de receita:")
                            for cat, qtd in cats.items():
                                print(f"    {cat}: {qtd} registros")
                
                # Análise para contas de outros tamanhos
                outros = df[~df['tamanho_conta'].isin([17])]
                if len(outros) > 0:
                    print(f"\n⚠️ Contas com tamanhos não padrão: {len(outros)}")
                    print("  (Receita normalmente usa contas de 17 caracteres)")
                    for tam in outros['tamanho_conta'].unique():
                        qtd = len(outros[outros['tamanho_conta'] == tam])
                        print(f"    {tam} caracteres: {qtd} registros")
            
            else:
                print("\n❌ Opção inválida!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao acessar o banco: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("\n🔍 VISUALIZADOR DE REGISTROS - RECEITA SALDO")
    print("Este script mostra os primeiros 50 registros da tabela")
    print("com várias opções de visualização e análise\n")
    
    if visualizar_registros():
        print("\n✅ Visualização concluída!")
    else:
        print("\n❌ Erro na visualização!")

if __name__ == "__main__":
    main()