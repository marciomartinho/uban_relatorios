#!/usr/bin/env python3
"""
Script para documentar a estrutura do banco de dados (DuckDB ou PostgreSQL).
Gera um relatório detalhado em formato TXT com todas as tabelas, colunas, tipos e amostras.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from datetime import datetime
import argparse

def documentar_duckdb(output_file=None):
    """Documenta estrutura do banco DuckDB"""
    import duckdb
    
    db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
    
    if not db_path.exists():
        print(f"❌ Banco DuckDB não encontrado: {db_path}")
        return
    
    # Nome do arquivo de saída
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"estrutura_uban_duckdb_{timestamp}.txt"
    
    print(f"📊 Analisando banco DuckDB: {db_path}")
    print(f"📝 Gerando documentação: {output_file}")
    
    conn = duckdb.connect(str(db_path))
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            # Cabeçalho
            f.write("="*100 + "\n")
            f.write("DOCUMENTAÇÃO DA ESTRUTURA DO BANCO DE DADOS DUCKDB\n")
            f.write("="*100 + "\n\n")
            f.write(f"Arquivo: {db_path}\n")
            f.write(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            
            # Pegar tamanho do arquivo
            size_mb = db_path.stat().st_size / (1024 * 1024)
            f.write(f"Tamanho do arquivo: {size_mb:.2f} MB\n")
            
            # Versão do DuckDB
            version = conn.execute("SELECT version()").fetchone()[0]
            f.write(f"Versão do DuckDB: {version}\n")
            
            # Listar todas as tabelas
            tabelas = conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
                ORDER BY 
                    CASE 
                        WHEN table_name LIKE 'dim_%' THEN 1
                        WHEN table_name LIKE 'fato_%' THEN 2
                        ELSE 3
                    END,
                    table_name
            """).fetchall()
            
            f.write("\n" + "="*100 + "\n")
            f.write(f"RESUMO: {len(tabelas)} tabela(s) encontrada(s)\n")
            f.write("-"*100 + "\n")
            
            # Resumo das tabelas com contagem
            for i, (tabela,) in enumerate(tabelas, 1):
                count = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
                f.write(f"{i:3}. {tabela:40} - {count:15,} registros\n")
            
            # Detalhes de cada tabela
            for i, (tabela,) in enumerate(tabelas, 1):
                f.write("\n" + "="*100 + "\n")
                f.write(f"TABELA {i}: {tabela.upper()}\n")
                f.write("="*100 + "\n\n")
                
                # Contagem de registros
                count = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
                f.write(f"Total de registros: {count:,}\n\n")
                
                # Estrutura da tabela
                f.write("ESTRUTURA DA TABELA:\n")
                f.write("-"*100 + "\n")
                f.write(f"{'#':<5} {'Campo':<30} {'Tipo':<20} {'Nulo?':<10} {'Padrão':<30}\n")
                f.write("-"*100 + "\n")
                
                colunas = conn.execute(f"""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = '{tabela}'
                    ORDER BY ordinal_position
                """).fetchall()
                
                for j, (col_name, col_type, nullable, default) in enumerate(colunas, 1):
                    nullable_str = "SIM" if nullable == 'YES' else "NÃO"
                    default_str = str(default) if default else "-"
                    if len(default_str) > 28:
                        default_str = default_str[:25] + "..."
                    f.write(f"{j:<5} {col_name:<30} {col_type:<20} {nullable_str:<10} {default_str:<30}\n")
                
                # Amostra de dados (se houver registros)
                if count > 0:
                    f.write("\nAMOSTRA DE DADOS (5 primeiros registros):\n")
                    f.write("-"*100 + "\n")
                    
                    # Pegar primeiras 5-8 colunas para mostrar
                    cols_to_show = min(8, len(colunas))
                    col_names = [col[0] for col in colunas[:cols_to_show]]
                    
                    # Cabeçalho da amostra
                    header = ""
                    for col in col_names:
                        header += f"{col[:15]:<16}"
                    f.write(header + "\n")
                    f.write("-"*len(header) + "\n")
                    
                    # Dados da amostra
                    sample_query = f"SELECT {', '.join(col_names)} FROM {tabela} LIMIT 5"
                    sample_data = conn.execute(sample_query).fetchall()
                    
                    for row in sample_data:
                        row_str = ""
                        for val in row:
                            val_str = str(val) if val is not None else "NULL"
                            if len(val_str) > 13:
                                val_str = val_str[:10] + "..."
                            row_str += f"{val_str:<16}"
                        f.write(row_str + "\n")
                
                # Análises específicas para tabelas de fato
                if tabela in ['despesa_lancamento', 'receita_lancamento', 'despesa_saldo', 'receita_saldo']:
                    f.write("\nANÁLISE ADICIONAL:\n")
                    f.write("-"*100 + "\n")
                    
                    # Para lançamentos
                    if 'lancamento' in tabela:
                        # Períodos
                        if 'periodo' in [col[0] for col in colunas]:
                            periodos = conn.execute(f"""
                                SELECT MIN(periodo), MAX(periodo), COUNT(DISTINCT periodo)
                                FROM {tabela}
                            """).fetchone()
                            if periodos[0]:
                                f.write(f"Período inicial: {periodos[0]}\n")
                                f.write(f"Período final: {periodos[1]}\n")
                                f.write(f"Total de períodos: {periodos[2]}\n\n")
                        
                        # Tipos de lançamento
                        if 'tipo_lancamento' in [col[0] for col in colunas]:
                            tipos = conn.execute(f"""
                                SELECT tipo_lancamento, COUNT(*), SUM(valancamento)
                                FROM {tabela}
                                GROUP BY tipo_lancamento
                                ORDER BY tipo_lancamento
                            """).fetchall()
                            
                            if tipos:
                                f.write("Por tipo de lançamento:\n")
                                for tipo, qtd, valor in tipos:
                                    valor_fmt = f"R$ {valor:20,.2f}" if valor else "R$ 0.00"
                                    f.write(f"   {tipo:10} - {qtd:10,} registros - {valor_fmt}\n")
                                f.write("\n")
                        
                        # Top UGs
                        if 'coug' in [col[0] for col in colunas]:
                            top_ugs = conn.execute(f"""
                                SELECT coug, COUNT(*) as qtd, SUM(valancamento) as total
                                FROM {tabela}
                                GROUP BY coug
                                ORDER BY qtd DESC
                                LIMIT 10
                            """).fetchall()
                            
                            if top_ugs:
                                f.write("Top 10 UGs com mais registros:\n")
                                for ug, qtd, total in top_ugs:
                                    total_fmt = f"R$ {total:20,.2f}" if total else "R$ 0.00"
                                    f.write(f"   UG {ug:6} - {qtd:10,} registros - {total_fmt}\n")
            
            # Rodapé
            f.write("\n" + "="*100 + "\n")
            f.write("FIM DO RELATÓRIO\n")
            f.write("="*100 + "\n")
        
        print(f"✅ Documentação gerada com sucesso: {output_file}")
        
    finally:
        conn.close()

def documentar_postgres(output_file=None):
    """Documenta estrutura do banco PostgreSQL"""
    from sqlalchemy import text
    from app.modules.database import db
    
    # Nome do arquivo de saída
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"estrutura_uban_postgres_{timestamp}.txt"
    
    print(f"📊 Analisando banco PostgreSQL...")
    print(f"📝 Gerando documentação: {output_file}")
    
    try:
        with db.engine.connect() as conn:
            # Testar conexão
            conn.execute(text("SELECT 1"))
            
            with open(output_file, 'w', encoding='utf-8') as f:
                # Cabeçalho
                f.write("="*100 + "\n")
                f.write("DOCUMENTAÇÃO DA ESTRUTURA DO BANCO DE DADOS POSTGRESQL\n")
                f.write("="*100 + "\n\n")
                
                # Informações do banco
                db_info = conn.execute(text("""
                    SELECT 
                        current_database() as database,
                        version() as version,
                        pg_database_size(current_database()) as size
                """)).fetchone()
                
                f.write(f"Banco de dados: {db_info[0]}\n")
                f.write(f"Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Versão: {db_info[1][:50]}...\n")
                f.write(f"Tamanho do banco: {db_info[2] / (1024*1024):.2f} MB\n")
                
                # Listar tabelas
                tabelas = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY 
                        CASE 
                            WHEN table_name LIKE 'dim_%' THEN 1
                            WHEN table_name LIKE 'fato_%' THEN 2
                            ELSE 3
                        END,
                        table_name
                """)).fetchall()
                
                f.write("\n" + "="*100 + "\n")
                f.write(f"RESUMO: {len(tabelas)} tabela(s) encontrada(s)\n")
                f.write("-"*100 + "\n")
                
                # Resumo com contagem
                for i, (tabela,) in enumerate(tabelas, 1):
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar()
                    f.write(f"{i:3}. {tabela:40} - {count:15,} registros\n")
                
                # Detalhes de cada tabela
                for i, (tabela,) in enumerate(tabelas, 1):
                    f.write("\n" + "="*100 + "\n")
                    f.write(f"TABELA {i}: {tabela.upper()}\n")
                    f.write("="*100 + "\n\n")
                    
                    # Contagem
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar()
                    f.write(f"Total de registros: {count:,}\n\n")
                    
                    # Estrutura
                    f.write("ESTRUTURA DA TABELA:\n")
                    f.write("-"*100 + "\n")
                    f.write(f"{'#':<5} {'Campo':<30} {'Tipo':<20} {'Nulo?':<10} {'Padrão':<30}\n")
                    f.write("-"*100 + "\n")
                    
                    colunas = conn.execute(text(f"""
                        SELECT 
                            column_name,
                            data_type,
                            is_nullable,
                            column_default
                        FROM information_schema.columns
                        WHERE table_schema = 'public' 
                        AND table_name = '{tabela}'
                        ORDER BY ordinal_position
                    """)).fetchall()
                    
                    for j, (col_name, col_type, nullable, default) in enumerate(colunas, 1):
                        nullable_str = "SIM" if nullable == 'YES' else "NÃO"
                        default_str = str(default) if default else "-"
                        if len(default_str) > 28:
                            default_str = default_str[:25] + "..."
                        f.write(f"{j:<5} {col_name:<30} {col_type:<20} {nullable_str:<10} {default_str:<30}\n")
                    
                    # Amostra de dados
                    if count > 0:
                        f.write("\nAMOSTRA DE DADOS (5 primeiros registros):\n")
                        f.write("-"*100 + "\n")
                        
                        cols_to_show = min(8, len(colunas))
                        col_names = [col[0] for col in colunas[:cols_to_show]]
                        
                        header = ""
                        for col in col_names:
                            header += f"{col[:15]:<16}"
                        f.write(header + "\n")
                        f.write("-"*len(header) + "\n")
                        
                        sample_data = conn.execute(text(f"""
                            SELECT {', '.join(col_names)} 
                            FROM {tabela} 
                            LIMIT 5
                        """)).fetchall()
                        
                        for row in sample_data:
                            row_str = ""
                            for val in row:
                                val_str = str(val) if val is not None else "NULL"
                                if len(val_str) > 13:
                                    val_str = val_str[:10] + "..."
                                row_str += f"{val_str:<16}"
                            f.write(row_str + "\n")
                
                # Rodapé
                f.write("\n" + "="*100 + "\n")
                f.write("FIM DO RELATÓRIO\n")
                f.write("="*100 + "\n")
        
        print(f"✅ Documentação gerada com sucesso: {output_file}")
        
    except Exception as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
        return

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Documenta a estrutura do banco de dados (DuckDB ou PostgreSQL)'
    )
    parser.add_argument(
        '--banco',
        choices=['duckdb', 'postgres', 'ambos'],
        default='ambos',
        help='Qual banco documentar (padrão: ambos)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Nome do arquivo de saída (opcional)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("DOCUMENTADOR DE ESTRUTURA DE BANCO DE DADOS")
    print("="*60)
    
    if args.banco in ['duckdb', 'ambos']:
        print("\n🦆 Processando DuckDB...")
        documentar_duckdb(args.output if args.banco == 'duckdb' else None)
    
    if args.banco in ['postgres', 'ambos']:
        print("\n🐘 Processando PostgreSQL...")
        documentar_postgres(args.output if args.banco == 'postgres' else None)
    
    print("\n✨ Processo concluído!")

if __name__ == "__main__":
    main()