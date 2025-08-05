#!/usr/bin/env python3
"""
Script para atualizar a documentação da estrutura do banco DuckDB
Gera um arquivo TXT detalhado incluindo as novas tabelas dimensão
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
from datetime import datetime
from pathlib import Path

def gerar_documentacao_atualizada():
    """Gera documentação completa e atualizada do banco DuckDB"""
    
    # Caminho do banco
    db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
    
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    # Nome do arquivo de saída
    output_file = f"estrutura_uban_duckdb_atualizada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print("=" * 80)
    print("GERADOR DE DOCUMENTAÇÃO ATUALIZADA - ESTRUTURA DO DUCKDB")
    print("=" * 80)
    print(f"📁 Banco de dados: {db_path}")
    print(f"📄 Arquivo de saída: {output_file}")
    print()
    
    try:
        conn = duckdb.connect(str(db_path), read_only=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Cabeçalho
            f.write("=" * 120 + "\n")
            f.write("DOCUMENTAÇÃO DA ESTRUTURA DO BANCO DE DADOS DUCKDB - VERSÃO ATUALIZADA\n")
            f.write("=" * 120 + "\n\n")
            f.write(f"Arquivo: {db_path}\n")
            f.write(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("\n" + "=" * 120 + "\n\n")
            
            # Listar todas as tabelas
            print("📊 Analisando estrutura do banco...")
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main' 
            ORDER BY 
                CASE 
                    WHEN table_name LIKE 'dim_%' THEN 1 
                    ELSE 2 
                END,
                table_name
            """
            tables = conn.execute(tables_query).fetchall()
            
            if not tables:
                f.write("NENHUMA TABELA ENCONTRADA NO BANCO!\n")
                print("❌ Nenhuma tabela encontrada!")
                return False
            
            # Separar tabelas por tipo
            tabelas_fato = []
            tabelas_dimensao = []
            
            for (table_name,) in tables:
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                if table_name.startswith('dim_'):
                    tabelas_dimensao.append((table_name, count))
                else:
                    tabelas_fato.append((table_name, count))
            
            # Resumo geral
            f.write(f"RESUMO GERAL: {len(tables)} tabela(s) encontrada(s)\n")
            f.write(f"   - Tabelas Fato: {len(tabelas_fato)}\n")
            f.write(f"   - Tabelas Dimensão: {len(tabelas_dimensao)}\n")
            f.write("\n" + "-" * 120 + "\n\n")
            
            # Listar tabelas FATO
            if tabelas_fato:
                f.write("TABELAS FATO:\n")
                f.write("-" * 120 + "\n")
                for i, (table_name, count) in enumerate(tabelas_fato, 1):
                    f.write(f"{i:2d}. {table_name:<40} - {count:>15,} registros\n")
                f.write("\n")
            
            # Listar tabelas DIMENSÃO
            if tabelas_dimensao:
                f.write("TABELAS DIMENSÃO:\n")
                f.write("-" * 120 + "\n")
                for i, (table_name, count) in enumerate(tabelas_dimensao, 1):
                    f.write(f"{i:2d}. {table_name:<40} - {count:>15,} registros\n")
                f.write("\n")
            
            f.write("=" * 120 + "\n\n")
            
            # Detalhamento das TABELAS FATO
            if tabelas_fato:
                f.write("DETALHAMENTO - TABELAS FATO\n")
                f.write("=" * 120 + "\n\n")
                
                for idx, (table_name, count) in enumerate(tabelas_fato, 1):
                    print(f"   Analisando tabela fato {idx}/{len(tabelas_fato)}: {table_name}...")
                    documentar_tabela(conn, f, table_name, count, idx, 'FATO')
            
            # Detalhamento das TABELAS DIMENSÃO
            if tabelas_dimensao:
                f.write("\n\nDETALHAMENTO - TABELAS DIMENSÃO\n")
                f.write("=" * 120 + "\n\n")
                
                for idx, (table_name, count) in enumerate(tabelas_dimensao, 1):
                    print(f"   Analisando tabela dimensão {idx}/{len(tabelas_dimensao)}: {table_name}...")
                    documentar_tabela(conn, f, table_name, count, idx, 'DIMENSÃO')
            
            # Análise de Relacionamentos
            f.write("\n\nANÁLISE DE RELACIONAMENTOS (FATO x DIMENSÃO)\n")
            f.write("=" * 120 + "\n\n")
            
            # Identificar possíveis relacionamentos
            relacionamentos = identificar_relacionamentos(conn, tabelas_fato, tabelas_dimensao)
            
            if relacionamentos:
                f.write("RELACIONAMENTOS IDENTIFICADOS:\n")
                f.write("-" * 120 + "\n")
                for rel in relacionamentos:
                    f.write(f"{rel}\n")
            else:
                f.write("Nenhum relacionamento óbvio identificado automaticamente.\n")
            
            # Informações adicionais
            f.write("\n\nINFORMAÇÕES ADICIONAIS DO BANCO\n")
            f.write("=" * 120 + "\n\n")
            
            # Tamanho do arquivo
            file_size = db_path.stat().st_size / (1024 * 1024)  # MB
            f.write(f"Tamanho do arquivo: {file_size:.2f} MB\n")
            
            # Versão do DuckDB
            try:
                version = conn.execute("SELECT version()").fetchone()[0]
                f.write(f"Versão do DuckDB: {version}\n")
            except:
                pass
            
            # Estatísticas gerais
            f.write("\nESTATÍSTICAS GERAIS:\n")
            f.write("-" * 50 + "\n")
            
            total_registros_fato = sum(count for _, count in tabelas_fato)
            total_registros_dim = sum(count for _, count in tabelas_dimensao)
            
            f.write(f"Total de registros (Fato): {total_registros_fato:,}\n")
            f.write(f"Total de registros (Dimensão): {total_registros_dim:,}\n")
            f.write(f"Total geral de registros: {total_registros_fato + total_registros_dim:,}\n")
            
            f.write("\n" + "=" * 120 + "\n")
            f.write("FIM DO RELATÓRIO\n")
            f.write("=" * 120 + "\n")
        
        conn.close()
        
        print(f"\n✅ Documentação gerada com sucesso!")
        print(f"📄 Arquivo salvo como: {output_file}")
        
        # Mostrar tamanho do arquivo gerado
        output_size = os.path.getsize(output_file) / 1024  # KB
        print(f"📊 Tamanho do relatório: {output_size:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao gerar documentação: {e}")
        import traceback
        traceback.print_exc()
        return False

def documentar_tabela(conn, f, table_name, count, idx, tipo):
    """Documenta uma tabela específica"""
    f.write(f"TABELA {tipo} {idx}: {table_name.upper()}\n")
    f.write("=" * 120 + "\n\n")
    f.write(f"Total de registros: {count:,}\n\n")
    
    # Estrutura da tabela
    columns_query = f"""
    SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name = '{table_name}'
    ORDER BY ordinal_position
    """
    columns = conn.execute(columns_query).fetchall()
    
    f.write("ESTRUTURA DA TABELA:\n")
    f.write("-" * 120 + "\n")
    f.write(f"{'#':<4} {'Campo':<30} {'Tipo':<20} {'Nulo?':<10} {'Padrão':<30}\n")
    f.write("-" * 120 + "\n")
    
    for i, (col_name, data_type, is_nullable, default) in enumerate(columns, 1):
        nullable = "SIM" if is_nullable == "YES" else "NÃO"
        default_val = str(default) if default else "-"
        if len(default_val) > 30:
            default_val = default_val[:27] + "..."
        f.write(f"{i:<4} {col_name:<30} {data_type:<20} {nullable:<10} {default_val:<30}\n")
    
    f.write("\n")
    
    # Para tabelas dimensão, mostrar informações específicas
    if tipo == 'DIMENSÃO':
        # Verificar índices únicos
        try:
            indices_query = f"""
            SELECT DISTINCT index_name 
            FROM duckdb_indexes() 
            WHERE table_name = '{table_name}'
            """
            indices = conn.execute(indices_query).fetchall()
            if indices:
                f.write("ÍNDICES:\n")
                for (idx_name,) in indices:
                    f.write(f"   - {idx_name}\n")
                f.write("\n")
        except:
            pass
        
        # Amostra de dados
        f.write("AMOSTRA DE DADOS (5 primeiros registros):\n")
        f.write("-" * 120 + "\n")
        
        try:
            # Pegar todas as colunas
            all_cols = [col[0] for col in columns]
            cols_str = ", ".join(all_cols[:6])  # Máximo 6 colunas na amostra
            
            sample_query = f"SELECT {cols_str} FROM {table_name} LIMIT 5"
            sample_data = conn.execute(sample_query).fetchall()
            
            # Cabeçalho
            header = ""
            for col in all_cols[:6]:
                header += f"{col[:18]:<20}"
            f.write(header + "\n")
            f.write("-" * len(header) + "\n")
            
            # Dados
            for row in sample_data:
                line = ""
                for val in row:
                    val_str = str(val) if val is not None else "NULL"
                    if len(val_str) > 18:
                        val_str = val_str[:15] + "..."
                    line += f"{val_str:<20}"
                f.write(line + "\n")
        except Exception as e:
            f.write(f"Erro ao obter amostra: {str(e)}\n")
    
    # Para tabelas fato, manter análises existentes
    elif 'lancamento' in table_name.lower():
        # Análise específica de lançamentos (como no script original)
        try:
            periodos_query = f"""
            SELECT 
                MIN(periodo) as periodo_inicial,
                MAX(periodo) as periodo_final,
                COUNT(DISTINCT periodo) as total_periodos
            FROM {table_name}
            """
            periodo_info = conn.execute(periodos_query).fetchone()
            if periodo_info and periodo_info[0]:
                f.write("ANÁLISE DE PERÍODOS:\n")
                f.write("-" * 50 + "\n")
                f.write(f"Período inicial: {periodo_info[0]}\n")
                f.write(f"Período final: {periodo_info[1]}\n")
                f.write(f"Total de períodos: {periodo_info[2]}\n")
        except:
            pass
    
    f.write("\n" + "=" * 120 + "\n\n")

def identificar_relacionamentos(conn, tabelas_fato, tabelas_dimensao):
    """Identifica possíveis relacionamentos entre tabelas fato e dimensão"""
    relacionamentos = []
    
    # Mapear colunas das tabelas fato
    colunas_fato = {}
    for table_name, _ in tabelas_fato:
        query = f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        """
        cols = conn.execute(query).fetchall()
        colunas_fato[table_name] = [col[0].lower() for col in cols]
    
    # Mapear chaves primárias esperadas das dimensões
    pk_dimensoes = {
        'dim_classificacao_orcamentaria': 'coclasseorc',
        'dim_conta_contabil': 'cocontacontabil',
        'dim_categoria_despesa': 'incategoria',
        'dim_funcao': 'cofuncao',
        'dim_grupo_despesa': 'cogrupo',
        'dim_modalidade': 'comodalidade',
        'dim_programa': 'coprograma',
        'dim_projeto': 'coprojeto',
        'dim_subfuncao': 'cosubfuncao',
        'dim_subtitulo': 'cosubtitulo',
        'dim_elemento': 'coelemento',
        'dim_evento': 'coevento',
        'dim_fonte': 'cofonte',
        'dim_gestao': 'cogestao',
        'dim_receita_alinea': 'coalinea',
        'dim_receita_categoria': 'cocategoriareceita',
        'dim_receita_especie': 'cosubfontereceita',
        'dim_receita_especificacao': 'corubrica',
        'dim_receita_origem': 'cofontereceita',
        'dim_unidade_gestora': 'coug'
    }
    
    # Verificar relacionamentos
    for table_fato, _ in tabelas_fato:
        for table_dim, _ in tabelas_dimensao:
            if table_dim in pk_dimensoes:
                pk = pk_dimensoes[table_dim]
                if pk in colunas_fato[table_fato]:
                    relacionamentos.append(f"{table_fato}.{pk} -> {table_dim}.{pk}")
    
    return sorted(relacionamentos)

def main():
    """Função principal"""
    print("\n🔍 GERADOR DE DOCUMENTAÇÃO ATUALIZADA - ESTRUTURA DO DUCKDB")
    print("Este script irá gerar um arquivo TXT atualizado com:")
    print("  - Todas as tabelas (fato e dimensão)")
    print("  - Estrutura detalhada de cada tabela")
    print("  - Análise de relacionamentos")
    print("  - Estatísticas gerais\n")
    
    resposta = input("Deseja continuar? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Operação cancelada.")
        return
    
    print()
    if gerar_documentacao_atualizada():
        print("\n🎉 Processo concluído com sucesso!")
        print("📋 O arquivo TXT foi gerado no diretório atual.")
    else:
        print("\n❌ Falha ao gerar a documentação.")

if __name__ == "__main__":
    main()