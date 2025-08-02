"""
Script para consultas rápidas no DuckDB de lançamentos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database_duckdb import db_duckdb
from datetime import datetime

def menu_principal():
    """Menu principal de consultas"""
    print("\n" + "=" * 60)
    print("CONSULTA DE LANÇAMENTOS - DuckDB Local")
    print("=" * 60)
    
    conn = db_duckdb.get_connection()
    
    # Estatísticas gerais
    try:
        # Receitas
        rec_count = conn.execute("SELECT COUNT(*) FROM receita_lancamento").fetchone()[0]
        rec_periodos = conn.execute("SELECT MIN(periodo), MAX(periodo) FROM receita_lancamento").fetchone()
        
        # Despesas
        desp_count = conn.execute("SELECT COUNT(*) FROM despesa_lancamento").fetchone()[0]
        desp_periodos = conn.execute("SELECT MIN(periodo), MAX(periodo) FROM despesa_lancamento").fetchone()
        
        print("\n📊 RESUMO DO BANCO:")
        print(f"   Receita Lançamento: {rec_count:,} registros")
        if rec_periodos[0]:
            print(f"   Períodos: {rec_periodos[0]} a {rec_periodos[1]}")
        
        print(f"\n   Despesa Lançamento: {desp_count:,} registros")
        if desp_periodos[0]:
            print(f"   Períodos: {desp_periodos[0]} a {desp_periodos[1]}")
        
    except Exception as e:
        print(f"\n❌ Erro ao consultar banco: {e}")
        conn.close()
        return
    
    while True:
        print("\n📋 OPÇÕES DE CONSULTA:")
        print("   1. Resumo por período")
        print("   2. Totais por UG")
        print("   3. Maiores lançamentos")
        print("   4. Buscar documento específico")
        print("   5. Estatísticas de contas contábeis")
        print("   6. Exportar período para Excel")
        print("   0. Sair")
        
        opcao = input("\n➤ Escolha uma opção: ")
        
        if opcao == '0':
            break
        elif opcao == '1':
            consultar_resumo_periodo(conn)
        elif opcao == '2':
            consultar_totais_ug(conn)
        elif opcao == '3':
            consultar_maiores_lancamentos(conn)
        elif opcao == '4':
            buscar_documento(conn)
        elif opcao == '5':
            estatisticas_contas(conn)
        elif opcao == '6':
            exportar_periodo(conn)
        else:
            print("\n❌ Opção inválida!")
    
    conn.close()
    print("\n👋 Até logo!")

def consultar_resumo_periodo(conn):
    """Mostra resumo por período"""
    tipo = input("\n📊 Tipo (R)eceita ou (D)espesa? ").upper()
    tabela = "receita_lancamento" if tipo == 'R' else "despesa_lancamento"
    
    print(f"\n📅 RESUMO POR PERÍODO - {tabela.upper()}")
    
    query = f"""
    SELECT 
        periodo,
        COUNT(*) as registros,
        COUNT(DISTINCT coug) as ugs,
        SUM(CASE WHEN tipo_lancamento = 'DEBITO' THEN valancamento ELSE 0 END) as debitos,
        SUM(CASE WHEN tipo_lancamento = 'CREDITO' THEN valancamento ELSE 0 END) as creditos
    FROM {tabela}
    GROUP BY periodo
    ORDER BY periodo
    """
    
    result = conn.execute(query).fetchall()
    
    print("\nPeríodo  | Registros |  UGs | Débitos         | Créditos        | Saldo")
    print("-" * 80)
    
    for row in result:
        periodo, registros, ugs, debitos, creditos = row
        saldo = creditos - debitos if tipo == 'R' else debitos - creditos
        print(f"{periodo} | {registros:>9,} | {ugs:>4} | {debitos:>15,.2f} | {creditos:>15,.2f} | {saldo:>15,.2f}")

def consultar_totais_ug(conn):
    """Mostra totais por UG"""
    tipo = input("\n🏢 Tipo (R)eceita ou (D)espesa? ").upper()
    tabela = "receita_lancamento" if tipo == 'R' else "despesa_lancamento"
    periodo = input("📅 Período (YYYY-MM) ou ENTER para todos: ")
    
    query = f"""
    SELECT 
        coug,
        COUNT(*) as registros,
        SUM(CASE WHEN tipo_lancamento = 'DEBITO' THEN valancamento ELSE 0 END) as debitos,
        SUM(CASE WHEN tipo_lancamento = 'CREDITO' THEN valancamento ELSE 0 END) as creditos
    FROM {tabela}
    {f"WHERE periodo = '{periodo}'" if periodo else ""}
    GROUP BY coug
    ORDER BY coug
    LIMIT 20
    """
    
    result = conn.execute(query).fetchall()
    
    print(f"\n🏢 TOTAIS POR UG - {tabela.upper()} {periodo if periodo else '(TODOS)'}")
    print("\nUG     | Registros | Débitos         | Créditos        | Saldo")
    print("-" * 70)
    
    for row in result:
        ug, registros, debitos, creditos = row
        saldo = creditos - debitos if tipo == 'R' else debitos - creditos
        print(f"{ug} | {registros:>9,} | {debitos:>15,.2f} | {creditos:>15,.2f} | {saldo:>15,.2f}")

def consultar_maiores_lancamentos(conn):
    """Mostra maiores lançamentos"""
    tipo = input("\n💰 Tipo (R)eceita ou (D)espesa? ").upper()
    tabela = "receita_lancamento" if tipo == 'R' else "despesa_lancamento"
    dc = input("📊 (D)ébitos ou (C)réditos? ").upper()
    tipo_lanc = 'DEBITO' if dc == 'D' else 'CREDITO'
    
    query = f"""
    SELECT 
        nudocumento,
        dalancamento,
        coug,
        valancamento,
        cocontacontabil,
        periodo
    FROM {tabela}
    WHERE tipo_lancamento = '{tipo_lanc}'
    ORDER BY valancamento DESC
    LIMIT 10
    """
    
    result = conn.execute(query).fetchall()
    
    print(f"\n💰 MAIORES {tipo_lanc}S - {tabela.upper()}")
    print("\nDocumento      | Data       | UG     | Valor           | Conta     | Período")
    print("-" * 85)
    
    for row in result:
        doc, data, ug, valor, conta, periodo = row
        print(f"{doc} | {data} | {ug} | {valor:>15,.2f} | {conta} | {periodo}")

def buscar_documento(conn):
    """Busca um documento específico"""
    doc = input("\n📄 Número do documento: ").strip()
    
    # Buscar em ambas as tabelas
    for tabela in ['receita_lancamento', 'despesa_lancamento']:
        query = f"""
        SELECT 
            nudocumento,
            nulancamento,
            dalancamento,
            coug,
            valancamento,
            tipo_lancamento,
            cocontacontabil,
            coevento
        FROM {tabela}
        WHERE nudocumento = ?
        ORDER BY nulancamento
        """
        
        result = conn.execute(query, [doc]).fetchall()
        
        if result:
            print(f"\n📄 DOCUMENTO ENCONTRADO EM {tabela.upper()}")
            print("\nLanç | Data       | UG     | Valor           | D/C     | Conta     | Evento")
            print("-" * 85)
            
            for row in result:
                _, lanc, data, ug, valor, tipo, conta, evento = row
                print(f"{lanc:>4} | {data} | {ug} | {valor:>15,.2f} | {tipo:>7} | {conta} | {evento}")

def estatisticas_contas(conn):
    """Mostra estatísticas de contas contábeis"""
    tipo = input("\n📊 Tipo (R)eceita ou (D)espesa? ").upper()
    tabela = "receita_lancamento" if tipo == 'R' else "despesa_lancamento"
    
    query = f"""
    SELECT 
        SUBSTR(CAST(cocontacontabil AS TEXT), 1, 1) as digito,
        COUNT(*) as registros,
        COUNT(DISTINCT cocontacontabil) as contas_distintas,
        SUM(valancamento) as total
    FROM {tabela}
    GROUP BY SUBSTR(CAST(cocontacontabil AS TEXT), 1, 1)
    ORDER BY digito
    """
    
    result = conn.execute(query).fetchall()
    
    print(f"\n📊 ESTATÍSTICAS POR PRIMEIRO DÍGITO DA CONTA - {tabela.upper()}")
    print("\nDígito | Registros | Contas | Total")
    print("-" * 50)
    
    for row in result:
        digito, registros, contas, total = row
        print(f"   {digito}   | {registros:>9,} | {contas:>6} | {total:>20,.2f}")

def exportar_periodo(conn):
    """Exporta um período para Excel"""
    try:
        import pandas as pd
        
        tipo = input("\n📤 Tipo (R)eceita ou (D)espesa? ").upper()
        tabela = "receita_lancamento" if tipo == 'R' else "despesa_lancamento"
        periodo = input("📅 Período para exportar (YYYY-MM): ")
        
        query = f"SELECT * FROM {tabela} WHERE periodo = ?"
        df = pd.read_sql(query, conn, params=[periodo])
        
        if len(df) == 0:
            print(f"\n❌ Nenhum registro encontrado para o período {periodo}")
            return
        
        arquivo = f"exportacao_{tabela}_{periodo}.xlsx"
        df.to_excel(arquivo, index=False)
        
        print(f"\n✅ Exportado com sucesso!")
        print(f"   Arquivo: {arquivo}")
        print(f"   Registros: {len(df):,}")
        
    except ImportError:
        print("\n❌ pandas não está instalado. Não é possível exportar para Excel.")
    except Exception as e:
        print(f"\n❌ Erro ao exportar: {e}")

if __name__ == "__main__":
    menu_principal()