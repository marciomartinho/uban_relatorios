"""
Script para carga incremental de ReceitaSaldo no DuckDB
Uso: python scripts/load_receita_saldo_duckdb.py ReceitaSaldoJulho.xlsx
"""
import sys
import os
from datetime import datetime

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_receita_saldo_duckdb import ETLReceitaSaldoDuckDB

def validar_carga():
    """Valida os dados carregados"""
    from app.modules.database_duckdb import db_duckdb
    
    conn = db_duckdb.get_connection()
    try:
        query = """
        SELECT 
            COUNT(*) as total_registros,
            COUNT(DISTINCT periodo) as periodos_distintos,
            MIN(periodo) as primeiro_periodo,
            MAX(periodo) as ultimo_periodo,
            SUM(saldo_contabil_receita) as total_saldo_contabil,
            SUM(vacredito) as total_creditos,
            SUM(vadebito) as total_debitos,
            COUNT(DISTINCT coug) as ugs_distintas,
            COUNT(DISTINCT cocontacontabil) as contas_contabeis_distintas,
            COUNT(CASE WHEN LENGTH(cocontacorrente) = 17 THEN 1 END) as contas_17_chars,
            COUNT(CASE WHEN LENGTH(cocontacorrente) = 38 THEN 1 END) as contas_38_chars
        FROM receita_saldo
        """
        
        result = conn.execute(query).fetchone()
        if result:
            print("\n📊 VALIDAÇÃO DOS DADOS CARREGADOS:")
            print(f"   Total de registros: {result[0]:,}")
            print(f"   Períodos distintos: {result[1]}")
            print(f"   Período inicial: {result[2]}")
            print(f"   Período final: {result[3]}")
            print(f"   Total saldo contábil: R$ {result[4]:,.2f}")
            print(f"   Total créditos: R$ {result[5]:,.2f}")
            print(f"   Total débitos: R$ {result[6]:,.2f}")
            print(f"   UGs distintas: {result[7]}")
            print(f"   Contas contábeis distintas: {result[8]}")
            print(f"   Contas com 17 caracteres: {result[9]:,}")
            print(f"   Contas com 38 caracteres: {result[10]:,}")
            
    except Exception as e:
        print(f"\n❌ Erro na validação: {e}")
    finally:
        conn.close()

def main():
    """Executa carga incremental de receita saldo"""
    print("=" * 80)
    print("ETL - RECEITA SALDO (DuckDB Local)")
    print("=" * 80)
    
    # Verificar argumento do arquivo
    if len(sys.argv) < 2:
        print("\n❌ ERRO: Você precisa especificar o arquivo!")
        print("\n💡 Uso correto:")
        print("   python scripts/load_receita_saldo_duckdb.py ReceitaSaldoJulho.xlsx")
        print("\n📁 Arquivos disponíveis na pasta dados_brutos/fato/:")
        
        # Listar arquivos disponíveis
        pasta = "dados_brutos/fato"
        if os.path.exists(pasta):
            arquivos = [f for f in os.listdir(pasta) if f.startswith("ReceitaSaldo") and f.endswith(".xlsx")]
            for arq in sorted(arquivos):
                print(f"   - {arq}")
        return
    
    # Montar caminho do arquivo
    nome_arquivo = sys.argv[1]
    arquivo = f"dados_brutos/fato/{nome_arquivo}"
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo):
        print(f"\n❌ Arquivo não encontrado: {arquivo}")
        print("\n💡 Verifique:")
        print("   1. Se o nome do arquivo está correto")
        print("   2. Se o arquivo está na pasta dados_brutos/fato/")
        print("   3. Se a extensão é .xlsx")
        return
    
    print(f"\n📁 Arquivo: {arquivo}")
    print(f"🗄️ Banco de dados: DuckDB local (dados_brutos/fato/db_local/lancamentos.duckdb)")
    
    # Criar instância do ETL
    etl = ETLReceitaSaldoDuckDB(chunk_size=5000)
    
    # Analisar arquivo
    print("\n🔍 Analisando arquivo...")
    periodos, total_estimado = etl.analisar_arquivo(arquivo)
    
    if not periodos:
        print("\n❌ Não foi possível identificar períodos no arquivo!")
        return
    
    print(f"\n📅 Períodos encontrados: {', '.join(sorted(periodos))}")
    print(f"📊 Total estimado de registros: ~{total_estimado:,}")
    
    # Verificar períodos existentes
    periodos_existentes = []
    for periodo in periodos:
        if etl.validar_periodo_existente(periodo):
            periodos_existentes.append(periodo)
    
    if periodos_existentes:
        print(f"\n⚠️ ATENÇÃO: Os seguintes períodos já existem no banco:")
        for p in periodos_existentes:
            print(f"   - {p}")
        
        resposta = input("\n❓ Deseja SOBRESCREVER os dados existentes? (s/N): ")
        if resposta.lower() != 's':
            print("\n❌ Carga cancelada pelo usuário.")
            return
        sobrescrever = True
    else:
        print("\n✅ Todos os períodos são novos.")
        sobrescrever = False
    
    # Confirmar processamento
    print(f"\n📋 RESUMO DA CARGA:")
    print(f"   Arquivo: {nome_arquivo}")
    print(f"   Períodos: {', '.join(sorted(periodos))}")
    print(f"   Registros estimados: ~{total_estimado:,}")
    print(f"   Modo: {'SOBRESCREVER' if sobrescrever else 'INCREMENTAL'}")
    
    resposta = input("\n✅ Confirma o processamento? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Carga cancelada pelo usuário.")
        return
    
    print("\n🚀 Iniciando processamento...")
    print("💡 Dica: O processamento é rápido no DuckDB local!\n")
    
    # Processar arquivo
    inicio = datetime.now()
    sucesso = etl.processar_arquivo(arquivo, sobrescrever=sobrescrever)
    tempo_total = datetime.now() - inicio
    
    if sucesso:
        print(f"\n✅ Carga concluída com sucesso em {tempo_total}!")
        
        # Validar carga
        validar_carga()
        
        # Mostrar próximos passos
        print("\n📌 PRÓXIMOS PASSOS:")
        print("   1. Se precisar carregar Despesa Saldo:")
        print("      python scripts/load_despesa_saldo_duckdb.py DespesaSaldoJulho.xlsx")
        print("   2. Se precisar carregar Receita Lançamento:")
        print("      python scripts/load_receita_lancamento_duckdb.py ReceitaLancamentoJulho.xlsx")
        print("   3. Para gerar relatórios de conferência:")
        print("      python scripts/relatorio_conferencia_duckdb.py")
        
    else:
        print(f"\n❌ Carga falhou após {tempo_total}!")
        print("\n💡 Verifique:")
        print("   1. Se o formato do Excel está correto")
        print("   2. Se todas as colunas obrigatórias existem")
        print("   3. Os logs acima para mais detalhes")

if __name__ == "__main__":
    main()