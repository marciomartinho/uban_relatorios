#!/usr/bin/env python3
"""
Script para gerar documentação completa da estrutura do banco DuckDB
Gera um arquivo TXT detalhado com todas as tabelas e campos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import duckdb
from datetime import datetime
from pathlib import Path

def gerar_relatorio_estrutura():
    """Gera relatório completo da estrutura do banco DuckDB"""
    
    # Caminho do banco
    db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
    
    # Verificar se existe
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    # Nome do arquivo de saída
    output_file = f"estrutura_uban_duckdb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print("=" * 80)
    print("GERADOR DE DOCUMENTAÇÃO - ESTRUTURA DO DUCKDB")
    print("=" * 80)
    print(f"📁 Banco de dados: {db_path}")
    print(f"📄 Arquivo de saída: {output_file}")
    print()
    
    try:
        # Conectar ao DuckDB
        conn = duckdb.connect(str(db_path), read_only=True)
        
        # Abrir arquivo para escrita
        with open(output_file, 'w', encoding='utf-8') as f:
            # Cabeçalho
            f.write("=" * 100 + "\n")
            f.write("DOCUMENTAÇÃO DA ESTRUTURA DO BANCO DE DADOS DUCKDB\n")
            f.write("=" * 100 + "\n\n")
            f.write(f"Arquivo: {db_path}\n")
            f.write(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("\n" + "=" * 100 + "\n\n")
            
            # Listar todas as tabelas
            print("📊 Listando tabelas...")
            tables_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name"
            tables = conn.execute(tables_query).fetchall()
            
            if not tables:
                f.write("NENHUMA TABELA ENCONTRADA NO BANCO!\n")
                print("❌ Nenhuma tabela encontrada!")
                return False
            
            # Resumo das tabelas
            f.write(f"RESUMO: {len(tables)} tabela(s) encontrada(s)\n")
            f.write("-" * 100 + "\n")
            for i, (table_name,) in enumerate(tables, 1):
                # Contar registros
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                f.write(f"{i:2d}. {table_name:<30} - {count:>15,} registros\n")
            f.write("\n" + "=" * 100 + "\n\n")
            
            # Detalhamento de cada tabela
            for table_idx, (table_name,) in enumerate(tables, 1):
                print(f"   Analisando tabela {table_idx}/{len(tables)}: {table_name}...")
                
                f.write(f"TABELA {table_idx}: {table_name.upper()}\n")
                f.write("=" * 100 + "\n\n")
                
                # Informações básicas
                count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                f.write(f"Total de registros: {count:,}\n\n")
                
                # Estrutura da tabela (colunas)
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
                f.write("-" * 100 + "\n")
                f.write(f"{'#':<4} {'Campo':<30} {'Tipo':<20} {'Nulo?':<10} {'Padrão':<30}\n")
                f.write("-" * 100 + "\n")
                
                for i, (col_name, data_type, is_nullable, default) in enumerate(columns, 1):
                    nullable = "SIM" if is_nullable == "YES" else "NÃO"
                    default_val = str(default) if default else "-"
                    if len(default_val) > 30:
                        default_val = default_val[:27] + "..."
                    f.write(f"{i:<4} {col_name:<30} {data_type:<20} {nullable:<10} {default_val:<30}\n")
                
                f.write("\n")
                
                # Análise de dados específicos por tipo de tabela
                if 'lancamento' in table_name.lower():
                    f.write("ANÁLISE DE LANÇAMENTOS:\n")
                    f.write("-" * 100 + "\n")
                    
                    # Períodos disponíveis
                    try:
                        periodos_query = f"""
                        SELECT 
                            MIN(periodo) as periodo_inicial,
                            MAX(periodo) as periodo_final,
                            COUNT(DISTINCT periodo) as total_periodos
                        FROM {table_name}
                        """
                        periodo_info = conn.execute(periodos_query).fetchone()
                        if periodo_info:
                            f.write(f"Período inicial: {periodo_info[0]}\n")
                            f.write(f"Período final: {periodo_info[1]}\n")
                            f.write(f"Total de períodos: {periodo_info[2]}\n\n")
                    except:
                        pass
                    
                    # Estatísticas por tipo de lançamento
                    try:
                        tipo_query = f"""
                        SELECT 
                            tipo_lancamento,
                            COUNT(*) as qtd,
                            SUM(valancamento) as total
                        FROM {table_name}
                        GROUP BY tipo_lancamento
                        ORDER BY tipo_lancamento
                        """
                        tipos = conn.execute(tipo_query).fetchall()
                        if tipos:
                            f.write("Por tipo de lançamento:\n")
                            for tipo, qtd, total in tipos:
                                f.write(f"   {tipo:<10} - {qtd:>10,} registros - R$ {total:>20,.2f}\n")
                            f.write("\n")
                    except:
                        pass
                    
                    # Top 10 UGs
                    try:
                        ug_query = f"""
                        SELECT 
                            coug,
                            COUNT(*) as qtd,
                            SUM(valancamento) as total
                        FROM {table_name}
                        GROUP BY coug
                        ORDER BY COUNT(*) DESC
                        LIMIT 10
                        """
                        ugs = conn.execute(ug_query).fetchall()
                        if ugs:
                            f.write("Top 10 UGs com mais lançamentos:\n")
                            for ug, qtd, total in ugs:
                                f.write(f"   UG {ug} - {qtd:>10,} registros - R$ {total:>20,.2f}\n")
                            f.write("\n")
                    except:
                        pass
                    
                    # Análise de contas correntes
                    try:
                        conta_query = f"""
                        SELECT 
                            LENGTH(cocontacorrente) as tamanho,
                            COUNT(*) as qtd
                        FROM {table_name}
                        WHERE cocontacorrente IS NOT NULL
                        GROUP BY LENGTH(cocontacorrente)
                        ORDER BY tamanho
                        """
                        contas = conn.execute(conta_query).fetchall()
                        if contas:
                            f.write("Distribuição por tamanho de conta corrente:\n")
                            for tam, qtd in contas:
                                f.write(f"   {tam:>2} caracteres - {qtd:>10,} registros\n")
                            f.write("\n")
                    except:
                        pass
                
                # Amostra de dados
                f.write("AMOSTRA DE DADOS (5 primeiros registros):\n")
                f.write("-" * 100 + "\n")
                
                try:
                    # Selecionar apenas algumas colunas importantes
                    sample_cols = []
                    all_cols = [col[0] for col in columns]
                    
                    # Colunas prioritárias
                    priority_cols = ['periodo', 'coexercicio', 'inmes', 'coug', 'nudocumento', 
                                   'valancamento', 'tipo_lancamento', 'cocontacontabil']
                    
                    for col in priority_cols:
                        if col in all_cols:
                            sample_cols.append(col)
                    
                    # Se tiver poucas colunas prioritárias, adicionar mais
                    if len(sample_cols) < 5:
                        for col in all_cols:
                            if col not in sample_cols:
                                sample_cols.append(col)
                            if len(sample_cols) >= 8:  # Máximo 8 colunas na amostra
                                break
                    
                    if sample_cols:
                        cols_str = ", ".join(sample_cols)
                        sample_query = f"SELECT {cols_str} FROM {table_name} LIMIT 5"
                        sample_data = conn.execute(sample_query).fetchall()
                        
                        # Cabeçalho
                        header = ""
                        for col in sample_cols:
                            header += f"{col[:15]:<16}"
                        f.write(header + "\n")
                        f.write("-" * len(header) + "\n")
                        
                        # Dados
                        for row in sample_data:
                            line = ""
                            for val in row:
                                val_str = str(val) if val is not None else "NULL"
                                if len(val_str) > 15:
                                    val_str = val_str[:12] + "..."
                                line += f"{val_str:<16}"
                            f.write(line + "\n")
                except Exception as e:
                    f.write(f"Erro ao obter amostra: {str(e)}\n")
                
                f.write("\n" + "=" * 100 + "\n\n")
            
            # Informações adicionais do banco
            f.write("INFORMAÇÕES ADICIONAIS DO BANCO\n")
            f.write("=" * 100 + "\n\n")
            
            # Tamanho do arquivo
            file_size = db_path.stat().st_size / (1024 * 1024)  # MB
            f.write(f"Tamanho do arquivo: {file_size:.2f} MB\n")
            
            # Versão do DuckDB
            try:
                version = conn.execute("SELECT version()").fetchone()[0]
                f.write(f"Versão do DuckDB: {version}\n")
            except:
                pass
            
            f.write("\n" + "=" * 100 + "\n")
            f.write("FIM DO RELATÓRIO\n")
            f.write("=" * 100 + "\n")
        
        conn.close()
        
        print(f"\n✅ Relatório gerado com sucesso!")
        print(f"📄 Arquivo salvo como: {output_file}")
        
        # Mostrar tamanho do arquivo gerado
        output_size = os.path.getsize(output_file) / 1024  # KB
        print(f"📊 Tamanho do relatório: {output_size:.1f} KB")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao gerar relatório: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("\n🔍 GERADOR DE DOCUMENTAÇÃO - ESTRUTURA DO DUCKDB")
    print("Este script irá gerar um arquivo TXT detalhado com:")
    print("  - Lista de todas as tabelas")
    print("  - Estrutura de cada tabela (campos e tipos)")
    print("  - Estatísticas e análises dos dados")
    print("  - Amostras de dados\n")
    
    resposta = input("Deseja continuar? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Operação cancelada.")
        return
    
    print()
    if gerar_relatorio_estrutura():
        print("\n🎉 Processo concluído com sucesso!")
        print("📋 O arquivo TXT foi gerado no diretório atual.")
    else:
        print("\n❌ Falha ao gerar o relatório.")

if __name__ == "__main__":
    main()