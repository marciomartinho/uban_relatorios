#!/usr/bin/env python3
"""
Script para visualizar os primeiros 50 registros da tabela despesa_lancamento
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
    """Mostra os primeiros 50 registros da tabela despesa_lancamento"""
    
    # Caminho do banco
    db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
    
    print("=" * 80)
    print("VISUALIZAÇÃO - PRIMEIROS 50 REGISTROS DE DESPESA_LANCAMENTO")
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
            WHERE table_name = 'despesa_lancamento'
        """).fetchone()[0] > 0
        
        if not table_exists:
            print("❌ ERRO: Tabela 'despesa_lancamento' não encontrada!")
            return False
        
        # Contar total de registros
        total_registros = conn.execute("SELECT COUNT(*) FROM despesa_lancamento").fetchone()[0]
        print(f"📊 Total de registros na tabela: {total_registros:,}\n")
        
        # Buscar os primeiros 50 registros
        print("🔍 Buscando os primeiros 50 registros...")
        query = """
        SELECT * 
        FROM despesa_lancamento 
        ORDER BY periodo, coexercicio, inmes, nudocumento, nulancamento
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
            print("3. Ver colunas principais de lançamento")
            print("4. Ver análise por tipo de lançamento (débito/crédito)")
            print("5. Ver registros de um período específico")
            print("6. Exportar todos os 50 registros para Excel")
            print("7. Ver registro específico (por índice)")
            print("8. Análise de parsing de conta corrente")
            print("9. Ver distribuição por UG")
            print("0. Sair")
            
            opcao = input("\n➤ Escolha uma opção: ")
            
            if opcao == '0':
                break
                
            elif opcao == '1':
                print("\n📊 RESUMO ESTATÍSTICO:")
                print("-" * 60)
                
                # Estatísticas de valores
                print("\nValores de lançamento:")
                print(df['valancamento'].describe())
                
                # Períodos
                print(f"\nPeríodos únicos: {df['periodo'].nunique()}")
                print(f"Período mínimo: {df['periodo'].min()}")
                print(f"Período máximo: {df['periodo'].max()}")
                
                # UGs
                print(f"\nUGs únicas: {df['coug'].nunique()}")
                
                # Tipos de lançamento
                print("\nDistribuição por tipo:")
                print(df['tipo_lancamento'].value_counts())
                
                # Eventos
                print(f"\nEventos únicos: {df['coevento'].nunique()}")
                
            elif opcao == '2':
                print("\n📄 PRIMEIROS 10 REGISTROS (TODAS AS COLUNAS):")
                print("-" * 60)
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', 30)
                print(df.head(10))
                
            elif opcao == '3':
                print("\n📋 COLUNAS PRINCIPAIS DE LANÇAMENTO:")
                print("-" * 60)
                
                # Selecionar colunas principais
                colunas_principais = [
                    'periodo', 'coug', 'nudocumento', 'nulancamento',
                    'dalancamento', 'valancamento', 'tipo_lancamento',
                    'cocontacontabil', 'coevento', 'cofuncao', 'coprograma',
                    'coelemento', 'comodalidade'
                ]
                
                # Filtrar apenas colunas que existem
                colunas_mostrar = [col for col in colunas_principais if col in df.columns]
                
                print(df[colunas_mostrar].head(20).to_string(index=True))
                
            elif opcao == '4':
                print("\n💰 ANÁLISE POR TIPO DE LANÇAMENTO:")
                print("-" * 60)
                
                for tipo in df['tipo_lancamento'].unique():
                    registros_tipo = df[df['tipo_lancamento'] == tipo]
                    total = registros_tipo['valancamento'].sum()
                    qtd = len(registros_tipo)
                    media = registros_tipo['valancamento'].mean()
                    maximo = registros_tipo['valancamento'].max()
                    
                    print(f"\n{tipo}:")
                    print(f"  Quantidade: {qtd}")
                    print(f"  Total: R$ {total:,.2f}")
                    print(f"  Média: R$ {media:,.2f}")
                    print(f"  Máximo: R$ {maximo:,.2f}")
                    
                    # Mostrar alguns exemplos
                    print(f"\n  Exemplos (primeiros 3):")
                    exemplos = registros_tipo[['nudocumento', 'valancamento', 'cocontacontabil']].head(3)
                    for idx, row in exemplos.iterrows():
                        print(f"    Doc: {row['nudocumento']} | "
                              f"Valor: R$ {row['valancamento']:,.2f} | "
                              f"Conta: {row['cocontacontabil']}")
                
            elif opcao == '5':
                periodos_unicos = sorted(df['periodo'].unique())
                print(f"\n📅 Períodos disponíveis: {', '.join(periodos_unicos)}")
                periodo = input("Digite o período (YYYY-MM): ")
                
                if periodo in periodos_unicos:
                    registros_periodo = df[df['periodo'] == periodo]
                    print(f"\n📊 Registros do período {periodo}: {len(registros_periodo)}")
                    print("\nPrimeiros 10 registros:")
                    print(registros_periodo[['nudocumento', 'nulancamento', 'valancamento', 
                                            'tipo_lancamento', 'cocontacontabil']].head(10))
                else:
                    print(f"\n❌ Período '{periodo}' não encontrado nos dados!")
                
            elif opcao == '6':
                nome_arquivo = f"despesa_lancamento_50_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
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
                            'Total de documentos únicos',
                            'Soma dos valores',
                            'Média dos valores',
                            'Total débitos',
                            'Total créditos'
                        ],
                        'Valor': [
                            len(df),
                            df['periodo'].min(),
                            df['periodo'].max(),
                            df['coug'].nunique(),
                            df['nudocumento'].nunique(),
                            f"R$ {df['valancamento'].sum():,.2f}",
                            f"R$ {df['valancamento'].mean():,.2f}",
                            len(df[df['tipo_lancamento'] == 'DEBITO']),
                            len(df[df['tipo_lancamento'] == 'CREDITO'])
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
                print("\n🔍 ANÁLISE DE PARSING DE CONTA CORRENTE:")
                print("-" * 60)
                
                # Verificar tamanhos de conta corrente
                df['tamanho_conta'] = df['cocontacorrente'].astype(str).str.len()
                tamanhos = df['tamanho_conta'].value_counts().sort_index()
                
                print("Distribuição de tamanhos:")
                for tam, qtd in tamanhos.items():
                    print(f"  {tam} caracteres: {qtd} registros")
                
                # Verificar parsing para contas de 38 e 40 chars
                df_38 = df[df['tamanho_conta'] == 38]
                df_40 = df[df['tamanho_conta'] == 40]
                
                if len(df_38) > 0:
                    print(f"\nContas de 38 caracteres: {len(df_38)}")
                    print("  Campos parseados: inesfera, couo, cofuncao, cosubfuncao,")
                    print("                   coprograma, coprojeto, cosubtitulo, cofonte,")
                    print("                   conatureza, incategoria, cogrupo, comodalidade, coelemento")
                
                if len(df_40) > 0:
                    print(f"\nContas de 40 caracteres: {len(df_40)}")
                    print("  Campos adicionais: cosubelemento (chars 39-40)")
                    
                    # Mostrar exemplos de subelemento
                    subelementos = df_40['cosubelemento'].value_counts().head(5)
                    if len(subelementos) > 0:
                        print("\n  Subelementos mais comuns:")
                        for subel, qtd in subelementos.items():
                            print(f"    '{subel}': {qtd} ocorrências")
            
            elif opcao == '9':
                print("\n🏢 DISTRIBUIÇÃO POR UG (nos 50 registros):")
                print("-" * 60)
                
                dist_ug = df.groupby('coug').agg({
                    'nudocumento': 'count',
                    'valancamento': ['sum', 'mean']
                }).round(2)
                
                dist_ug.columns = ['Qtd_Registros', 'Soma_Valores', 'Media_Valores']
                dist_ug = dist_ug.sort_values('Qtd_Registros', ascending=False)
                
                print(dist_ug.head(10))
            
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
    print("\n🔍 VISUALIZADOR DE REGISTROS - DESPESA LANÇAMENTO")
    print("Este script mostra os primeiros 50 registros da tabela")
    print("com várias opções de visualização e análise\n")
    
    if visualizar_registros():
        print("\n✅ Visualização concluída!")
    else:
        print("\n❌ Erro na visualização!")

if __name__ == "__main__":
    main()