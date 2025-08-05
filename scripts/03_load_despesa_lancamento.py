"""
Script para carga incremental de DespesaLancamento no DuckDB
Uso: python scripts/load_despesa_lancamento_duckdb.py DespesaLancamentoJulho.xlsx
"""
import sys
import os
from datetime import datetime

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_despesa_lancamento_duckdb import ETLDespesaLancamentoDuckDB, validar_carga

def main():
    """Executa carga incremental de despesa lançamento"""
    print("=" * 80)
    print("ETL - DESPESA LANÇAMENTO (DuckDB Local)")
    print("=" * 80)
    
    # Verificar argumento do arquivo
    if len(sys.argv) < 2:
        print("\n❌ ERRO: Você precisa especificar o arquivo!")
        print("\n💡 Uso correto:")
        print("   python scripts/load_despesa_lancamento_duckdb.py DespesaLancamentoJulho.xlsx")
        print("\n📁 Arquivos disponíveis na pasta dados_brutos/fato/:")
        
        # Listar arquivos disponíveis
        pasta = "dados_brutos/fato"
        if os.path.exists(pasta):
            arquivos = [f for f in os.listdir(pasta) if f.startswith("DespesaLancamento") and f.endswith(".xlsx")]
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
    etl = ETLDespesaLancamentoDuckDB(chunk_size=50000)  # Chunks maiores para despesa
    
    # Analisar arquivo
    print("\n🔍 Analisando arquivo...")
    periodos, total_estimado = etl.analisar_arquivo(arquivo)
    
    if not periodos:
        print("\n❌ Não foi possível identificar períodos no arquivo!")
        return
    
    print(f"\n📅 Períodos encontrados: {', '.join(sorted(periodos))}")
    print(f"📊 Total estimado de registros: ~{total_estimado:,}")
    
    # Aviso para arquivos grandes
    if total_estimado > 500000:
        print("\n⚠️ ATENÇÃO: Arquivo grande detectado!")
        print("   Tempo estimado: 10-20 minutos")
        print("   💡 Não feche o terminal durante o processamento!")
    
    # Verificar períodos existentes
    periodos_existentes = []
    for periodo in periodos:
        if etl.validar_periodo_existente(periodo):
            periodos_existentes.append(periodo)
    
    if periodos_existentes:
        print(f"\n⚠️ ATENÇÃO: Os seguintes períodos já existem no banco:")
        for p in periodos_existentes:
            # Contar registros existentes
            conn = etl.db_duckdb.get_connection()
            count = conn.execute(f"SELECT COUNT(*) FROM {etl.table_name} WHERE periodo = ?", [p]).fetchone()[0]
            conn.close()
            print(f"   - {p} ({count:,} registros)")
        
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
    print(f"   Chunks: {etl.chunk_size:,} registros por vez")
    
    resposta = input("\n✅ Confirma o processamento? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Carga cancelada pelo usuário.")
        return
    
    print("\n🚀 Iniciando processamento...")
    print("💡 Dica: DuckDB é muito rápido, mesmo com arquivos grandes!")
    print("📊 A barra de progresso mostrará o avanço...\n")
    
    # Processar arquivo
    inicio = datetime.now()
    sucesso = etl.processar_arquivo(arquivo, sobrescrever=sobrescrever)
    tempo_total = datetime.now() - inicio
    
    if sucesso:
        print(f"\n✅ Carga concluída com sucesso em {tempo_total}!")
        
        # Validar carga
        validar_carga()
        
        # Verificar espaço em disco
        import shutil
        db_path = "dados_brutos/fato/db_local/lancamentos.duckdb"
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"\n💾 Tamanho do banco DuckDB: {size_mb:.1f} MB")
        
        # Mostrar próximos passos
        print("\n📌 PRÓXIMOS PASSOS:")
        print("   1. Para gerar relatórios de conferência:")
        print("      python scripts/relatorio_conferencia_duckdb.py")
        print("   2. Para consultar dados específicos:")
        print("      python scripts/consultar_lancamentos_duckdb.py")
        
    else:
        print(f"\n❌ Carga falhou após {tempo_total}!")
        print("\n💡 Possíveis causas:")
        print("   1. Formato incorreto do Excel")
        print("   2. Colunas obrigatórias faltando")
        print("   3. Dados com problemas de encoding")
        print("   4. Memória insuficiente (feche outros programas)")
        print("\n📋 Verifique os logs acima para mais detalhes!")

if __name__ == "__main__":
    main()