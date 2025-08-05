#!/usr/bin/env python3
"""
Script para visualizar os primeiros 50 registros da tabela receita_lancamento
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
    """Mostra os primeiros 50 registros da tabela receita_lancamento"""
    
    # Caminho do banco
    db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
    
    print("=" * 80)
    print("VISUALIZAÇÃO - PRIMEIROS 50 REGISTROS DE RECEITA_LANCAMENTO")
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
            WHERE table_name = 'receita_lancamento'
        """).fetchone()[0] > 0
        
        if not table_exists:
            print("❌ ERRO: Tabela 'receita_lancamento' não encontrada!")
            return False
        
        # Contar total de registros
        total_registros = conn.execute("SELECT COUNT(*) FROM receita_lancamento").fetchone()[0]
        print(f"📊 Total de registros na tabela: {total_registros:,}\n")
        
        # Buscar os primeiros 50 registros
        print("🔍 Buscando os primeiros 50 registros...")
        query = """
        SELECT * 
        FROM receita_lancamento 
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
            print("8. Análise de parsing de conta corrente (17 e 38 chars)")
            print("9. Verificar valores órfãos (problemas de integridade)")
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
                print("\n📋 COLUNAS PRINCIPAIS DE RECEITA:")
                print("-" * 60)
                
                # Selecionar colunas principais para receita
                colunas_principais = [
                    'periodo', 'coug', 'nudocumento', 'nulancamento',
                    'dalancamento', 'valancamento', 'tipo_lancamento',
                    'cocontacontabil', 'coevento', 'coclasseorc',
                    'cocategoriareceita', 'cofontereceita'
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
                nome_arquivo = f"receita_lancamento_50_registros_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                
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
                            'Total créditos',
                            'Eventos únicos',
                            'Contas contábeis únicas'
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
                            len(df[df['tipo_lancamento'] == 'CREDITO']),
                            df['coevento'].nunique(),
                            df['cocontacontabil'].nunique()
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
                print("\n🔍 ANÁLISE DE PARSING DE CONTA CORRENTE (RECEITA):")
                print("-" * 60)
                
                # Verificar tamanhos de conta corrente
                df['tamanho_conta'] = df['cocontacorrente'].astype(str).str.len()
                tamanhos = df['tamanho_conta'].value_counts().sort_index()
                
                print("Distribuição de tamanhos:")
                for tam, qtd in tamanhos.items():
                    print(f"  {tam} caracteres: {qtd} registros")
                
                # Análise para contas de 17 chars (específico de receita)
                df_17 = df[df['tamanho_conta'] == 17]
                if len(df_17) > 0:
                    print(f"\n📊 Contas de 17 caracteres: {len(df_17)}")
                    print("  Campos parseados:")
                    print("  - coclasseorc (0:8) - Classificação orçamentária")
                    print("  - cofonte (8:18) - Fonte")
                    print("  - cocategoriareceita (0:1) - Categoria")
                    print("  - cofontereceita (0:2) - Fonte receita")
                    print("  - cosubfontereceita (0:3) - Subfonte")
                    print("  - corubrica (0:4) - Rubrica")
                    print("  - coalinea (0:6) - Alínea")
                    
                    # Mostrar exemplos
                    if 'coclasseorc' in df.columns:
                        class_orc = df_17['coclasseorc'].value_counts().head(3)
                        print("\n  Classificações orçamentárias mais comuns:")
                        for cls, qtd in class_orc.items():
                            print(f"    {cls}: {qtd} ocorrências")
                
                # Análise para contas de 38 chars
                df_38 = df[df['tamanho_conta'] == 38]
                if len(df_38) > 0:
                    print(f"\n📊 Contas de 38 caracteres: {len(df_38)}")
                    print("  Campos parseados (despesa em receita?):")
                    print("  - inesfera, couo, cofuncao, cosubfuncao, etc.")
                    print("  (Verificar se está correto ter contas de 38 chars em receita)")
            
            elif opcao == '9':
                print("\n⚠️ VERIFICAÇÃO DE VALORES ÓRFÃOS:")
                print("-" * 60)
                print("Baseado no relatório de integridade, há problemas com:")
                
                # Verificar eventos órfãos
                print("\n1. EVENTOS ÓRFÃOS (800281, 805281):")
                eventos_problema = [800281, 805281]
                for evento in eventos_problema:
                    qtd = len(df[df['coevento'] == evento]) if 'coevento' in df.columns else 0
                    if qtd > 0:
                        print(f"   Evento {evento}: {qtd} registros nos 50 primeiros")
                        exemplo = df[df['coevento'] == evento].head(1)
                        if len(exemplo) > 0:
                            print(f"   Exemplo: Doc {exemplo.iloc[0]['nudocumento']}, "
                                  f"Valor: R$ {exemplo.iloc[0]['valancamento']:,.2f}")
                
                # Verificar contas contábeis órfãs
                print("\n2. CONTAS CONTÁBEIS ÓRFÃS (621340199, 621340101):")
                contas_problema = ['621340199', '621340101']
                for conta in contas_problema:
                    qtd = len(df[df['cocontacontabil'] == conta]) if 'cocontacontabil' in df.columns else 0
                    if qtd > 0:
                        print(f"   Conta {conta}: {qtd} registros nos 50 primeiros")
                        exemplo = df[df['cocontacontabil'] == conta].head(1)
                        if len(exemplo) > 0:
                            print(f"   Exemplo: Doc {exemplo.iloc[0]['nudocumento']}, "
                                  f"Valor: R$ {exemplo.iloc[0]['valancamento']:,.2f}")
                
                print("\n💡 Recomendação: Adicionar estes valores nas tabelas dimensão correspondentes")
            
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
    print("\n🔍 VISUALIZADOR DE REGISTROS - RECEITA LANÇAMENTO")
    print("Este script mostra os primeiros 50 registros da tabela")
    print("com várias opções de visualização e análise\n")
    
    if visualizar_registros():
        print("\n✅ Visualização concluída!")
    else:
        print("\n❌ Erro na visualização!")

if __name__ == "__main__":
    main()