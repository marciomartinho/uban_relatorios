"""
Script para carga incremental de ReceitaLancamento no DuckDB
Uso: python scripts/load_receita_lancamento_duckdb.py ReceitaLancamentoJulho.xlsx
"""
import sys
import os
from datetime import datetime

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_receita_lancamento_duckdb import ETLReceitaLancamentoDuckDB, validar_carga

def main():
    """Executa carga incremental de receita lançamento"""
    print("=" * 80)
    print("ETL - RECEITA LANÇAMENTO (DuckDB Local)")
    print("=" * 80)
    
    # Verificar argumento do arquivo
    if len(sys.argv) < 2:
        print("\n❌ ERRO: Você precisa especificar o arquivo!")
        print("\n💡 Uso correto:")
        print("   python scripts/load_receita_lancamento_duckdb.py ReceitaLancamentoJulho.xlsx")
        print("\n📁 Arquivos disponíveis na pasta dados_brutos/fato/:")
        
        # Listar arquivos disponíveis
        pasta = "dados_brutos/fato"
        if os.path.exists(pasta):
            arquivos = [f for f in os.listdir(pasta) if f.startswith("ReceitaLancamento") and f.endswith(".xlsx")]
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
    etl = ETLReceitaLancamentoDuckDB(chunk_size=10000)
    
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
        print("   1. Se precisar carregar Despesa Lançamento:")
        print("      python scripts/load_despesa_lancamento_duckdb.py DespesaLancamentoJulho.xlsx")
        print("   2. Para gerar relatórios de conferência:")
        print("      python scripts/relatorio_conferencia_duckdb.py")
        
    else:
        print(f"\n❌ Carga falhou após {tempo_total}!")
        print("\n💡 Verifique:")
        print("   1. Se o formato do Excel está correto")
        print("   2. Se todas as colunas obrigatórias existem")
        print("   3. Os logs acima para mais detalhes")

if __name__ == "__main__":
    main()