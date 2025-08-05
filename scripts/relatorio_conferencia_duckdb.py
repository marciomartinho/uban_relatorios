#!/usr/bin/env python3
"""
Script para gerar relatório de conferência após carga mensal
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database_duckdb import db_duckdb
from datetime import datetime
import pandas as pd

def gerar_relatorio():
    """Gera relatório de conferência"""
    print("=" * 80)
    print("RELATÓRIO DE CONFERÊNCIA - DUCKDB")
    print("=" * 80)
    print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    conn = db_duckdb.get_connection()
    
    # Nome do arquivo de saída
    output_file = f"conferencia_duckdb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("RELATÓRIO DE CONFERÊNCIA - CARGA MENSAL DUCKDB\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Banco: dados_brutos/fato/db_local/uban.duckdb\n\n")
        
        # Para cada tabela
        tabelas = [
            ('despesa_lancamento', 'DESPESA LANÇAMENTO'),
            ('despesa_saldo', 'DESPESA SALDO'),
            ('receita_lancamento', 'RECEITA LANÇAMENTO'),
            ('receita_saldo', 'RECEITA SALDO')
        ]
        
        for tabela, titulo in tabelas:
            print(f"\n📊 Analisando {titulo}...")
            
            f.write("=" * 100 + "\n")
            f.write(f"{titulo}\n")
            f.write("=" * 100 + "\n\n")
            
            try:
                # Total de registros
                total = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
                f.write(f"Total de registros: {total:,}\n\n")
                
                # Períodos disponíveis
                periodos_query = f"""
                SELECT 
                    periodo,
                    COUNT(*) as registros
                FROM {tabela}
                GROUP BY periodo
                ORDER BY periodo
                """
                periodos = conn.execute(periodos_query).fetchall()
                
                f.write("PERÍODOS CARREGADOS:\n")
                f.write("-" * 50 + "\n")
                f.write(f"{'Período':<10} {'Registros':>15}\n")
                f.write("-" * 50 + "\n")
                
                for periodo, count in periodos:
                    f.write(f"{periodo:<10} {count:>15,}\n")
                
                f.write(f"\nTotal de períodos: {len(periodos)}\n")
                
                # Análise específica por tipo
                if 'lancamento' in tabela:
                    # Análise de lançamentos
                    f.write("\nANÁLISE DE VALORES:\n")
                    f.write("-" * 50 + "\n")
                    
                    valores_query = f"""
                    SELECT 
                        tipo_lancamento,
                        COUNT(*) as qtd,
                        SUM(valancamento) as total,
                        AVG(valancamento) as media,
                        MIN(valancamento) as minimo,
                        MAX(valancamento) as maximo
                    FROM {tabela}
                    GROUP BY tipo_lancamento
                    ORDER BY tipo_lancamento
                    """
                    valores = conn.execute(valores_query).fetchall()
                    
                    for tipo, qtd, total, media, minimo, maximo in valores:
                        f.write(f"\n{tipo}:\n")
                        f.write(f"  Quantidade: {qtd:,}\n")
                        f.write(f"  Total: R$ {total:,.2f}\n")
                        f.write(f"  Média: R$ {media:,.2f}\n")
                        f.write(f"  Mínimo: R$ {minimo:,.2f}\n")
                        f.write(f"  Máximo: R$ {maximo:,.2f}\n")
                    
                    # Top 5 UGs
                    f.write("\nTOP 5 UGs (por quantidade de lançamentos):\n")
                    f.write("-" * 50 + "\n")
                    
                    ug_query = f"""
                    SELECT 
                        coug,
                        COUNT(*) as qtd,
                        SUM(valancamento) as total
                    FROM {tabela}
                    GROUP BY coug
                    ORDER BY COUNT(*) DESC
                    LIMIT 5
                    """
                    ugs = conn.execute(ug_query).fetchall()
                    
                    f.write(f"{'UG':<10} {'Lançamentos':>15} {'Valor Total':>25}\n")
                    f.write("-" * 50 + "\n")
                    for ug, qtd, total in ugs:
                        f.write(f"{ug:<10} {qtd:>15,} {total:>25,.2f}\n")
                
                else:
                    # Análise de saldos
                    f.write("\nANÁLISE DE SALDOS:\n")
                    f.write("-" * 50 + "\n")
                    
                    if 'despesa' in tabela:
                        saldo_col = 'saldo_contabil_despesa'
                    else:
                        saldo_col = 'saldo_contabil_receita'
                    
                    saldos_query = f"""
                    SELECT 
                        COUNT(*) as qtd,
                        SUM(vacredito) as total_credito,
                        SUM(vadebito) as total_debito,
                        SUM({saldo_col}) as total_saldo
                    FROM {tabela}
                    """
                    resultado = conn.execute(saldos_query).fetchone()
                    
                    if resultado:
                        qtd, credito, debito, saldo = resultado
                        f.write(f"Total Crédito: R$ {credito:,.2f}\n")
                        f.write(f"Total Débito: R$ {debito:,.2f}\n")
                        f.write(f"Saldo Total: R$ {saldo:,.2f}\n")
                
                # Verificações de integridade
                f.write("\nVERIFICAÇÕES DE INTEGRIDADE:\n")
                f.write("-" * 50 + "\n")
                
                # Registros com valores zerados
                if 'lancamento' in tabela:
                    zeros = conn.execute(f"SELECT COUNT(*) FROM {tabela} WHERE valancamento = 0").fetchone()[0]
                    f.write(f"Lançamentos com valor zero: {zeros:,}\n")
                
                # Registros sem período
                sem_periodo = conn.execute(f"SELECT COUNT(*) FROM {tabela} WHERE periodo IS NULL").fetchone()[0]
                f.write(f"Registros sem período: {sem_periodo:,}\n")
                
                f.write("\n")
                
            except Exception as e:
                f.write(f"\n❌ ERRO ao analisar {tabela}: {str(e)}\n\n")
                print(f"   ❌ Erro: {e}")
        
        # Resumo geral
        f.write("=" * 100 + "\n")
        f.write("RESUMO GERAL DO BANCO\n")
        f.write("=" * 100 + "\n\n")
        
        try:
            # Total geral
            total_geral = 0
            for tabela, _ in tabelas:
                try:
                    count = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
                    f.write(f"{tabela:.<30} {count:>15,} registros\n")
                    total_geral += count
                except:
                    f.write(f"{tabela:.<30} {'ERRO':>15}\n")
            
            f.write("-" * 50 + "\n")
            f.write(f"{'TOTAL GERAL':.<30} {total_geral:>15,} registros\n")
            
            # Tamanho do banco
            from pathlib import Path
            db_path = Path("dados_brutos/fato/db_local/uban.duckdb")
            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                f.write(f"\nTamanho do banco: {size_mb:.2f} MB\n")
            
        except Exception as e:
            f.write(f"\n❌ Erro no resumo geral: {str(e)}\n")
        
        f.write("\n" + "=" * 100 + "\n")
        f.write("FIM DO RELATÓRIO\n")
        f.write("=" * 100 + "\n")
    
    conn.close()
    
    print(f"\n✅ Relatório gerado com sucesso!")
    print(f"📄 Arquivo: {output_file}")

def main():
    """Função principal"""
    print("\n🔍 GERADOR DE RELATÓRIO DE CONFERÊNCIA")
    print("Este relatório mostra um resumo completo dos dados carregados\n")
    
    resposta = input("Gerar relatório agora? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Operação cancelada.")
        return
    
    gerar_relatorio()

if __name__ == "__main__":
    main()