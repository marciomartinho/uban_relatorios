#!/usr/bin/env python3
"""
Script para carregar DespesaSaldo com nova estrutura no DuckDB
Uso: python scripts/load_despesa_saldo_nova.py DespesaSaldoJulho.xlsx [--recriar]
"""
import sys
import os
from datetime import datetime

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_despesa_saldo_duckdb import ETLDespesaSaldoDuckDB

def main():
    """Executa carga de despesa saldo com nova estrutura"""
    print("=" * 80)
    print("ETL - DESPESA SALDO (NOVA ESTRUTURA) - DuckDB")
    print("=" * 80)
    
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("\n❌ ERRO: Você precisa especificar o arquivo!")
        print("\n💡 Uso correto:")
        print("   python scripts/load_despesa_saldo_nova.py DespesaSaldoJulho.xlsx")
        print("   python scripts/load_despesa_saldo_nova.py DespesaSaldoJulho.xlsx --recriar")
        print("\n   Opções:")
        print("   --recriar : Remove e recria a tabela completamente")
        print("\n📁 Arquivos disponíveis na pasta dados_brutos/fato/:")
        
        # Listar arquivos disponíveis
        pasta = "dados_brutos/fato"
        if os.path.exists(pasta):
            arquivos = [f for f in os.listdir(pasta) if f.startswith("DespesaSaldo") and f.endswith(".xlsx")]
            for arq in sorted(arquivos):
                print(f"   - {arq}")
        return
    
    # Verificar flag --recriar
    recriar_tabela = "--recriar" in sys.argv
    
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
    print(f"🗄️ Banco de dados: DuckDB local (dados_brutos/fato/db_local/uban.duckdb)")
    
    if recriar_tabela:
        print("\n⚠️ MODO RECRIAÇÃO: A tabela será completamente recriada!")
        print("   Todos os dados existentes serão perdidos.")
        resposta = input("\n❓ Confirma a RECRIAÇÃO COMPLETA da tabela? (s/N): ")
        if resposta.lower() != 's':
            print("\n❌ Operação cancelada.")
            return
    
    # Criar instância do ETL
    etl = ETLDespesaSaldoDuckDB(chunk_size=10000)
    
    # Analisar arquivo
    print("\n🔍 Analisando arquivo...")
    periodos, total_estimado = etl.analisar_arquivo(arquivo)
    
    if not periodos:
        print("\n❌ Não foi possível identificar períodos no arquivo!")
        return
    
    print(f"\n📅 Períodos encontrados: {', '.join(sorted(periodos))}")
    print(f"📊 Total estimado de registros: ~{total_estimado:,}")
    
    # Se não for recriação, verificar períodos existentes
    sobrescrever = False
    if not recriar_tabela:
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
    
    # Mostrar estrutura esperada
    print("\n📋 ESTRUTURA ESPERADA DOS CAMPOS:")
    print("   Campos obrigatórios do Excel:")
    print("   - COEXERCICIO, COUG, COGESTAO, COCONTACONTABIL")
    print("   - COCONTACORRENTE, INMES, INESFERA, COUO")
    print("   - COFUNCAO, COSUBFUNCAO, COPROGRAMA, COPROJETO")
    print("   - COSUBTITULO, COFONTE, CONATUREZA")
    print("   - VACREDITO, VADEBITO")
    print("\n   Campos calculados:")
    print("   - saldo_contabil_despesa (baseado no 1º dígito da conta)")
    print("   - incategoria, cogrupo, comodalidade, coelemento (parse de CONATUREZA)")
    print("   - cosubelemento (para contas de 40 caracteres)")
    
    # Confirmar processamento
    print(f"\n📋 RESUMO DA CARGA:")
    print(f"   Arquivo: {nome_arquivo}")
    print(f"   Períodos: {', '.join(sorted(periodos))}")
    print(f"   Registros estimados: ~{total_estimado:,}")
    print(f"   Modo: {'RECRIAÇÃO COMPLETA' if recriar_tabela else ('SOBRESCREVER' if sobrescrever else 'INCREMENTAL')}")
    
    resposta = input("\n✅ Confirma o processamento? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Carga cancelada pelo usuário.")
        return
    
    print("\n🚀 Iniciando processamento...")
    print("📊 A barra de progresso mostrará o avanço...\n")
    
    # Processar arquivo
    inicio = datetime.now()
    sucesso = etl.processar_arquivo(arquivo, sobrescrever=sobrescrever, recriar_tabela=recriar_tabela)
    tempo_total = datetime.now() - inicio
    
    if sucesso:
        print(f"\n✅ Carga concluída com sucesso em {tempo_total}!")
        
        # Mostrar próximos passos
        print("\n📌 PRÓXIMOS PASSOS:")
        print("   1. Para visualizar os dados carregados:")
        print("      python scripts/visualizar_despesa_saldo.py")
        print("   2. Para gerar relatório de conferência:")
        print("      python scripts/relatorio_conferencia_duckdb.py")
        print("   3. Para verificar integridade referencial:")
        print("      python scripts/verificar_integridade_duckdb.py")
        
        if recriar_tabela:
            print("\n⚠️ IMPORTANTE: Como a tabela foi recriada, verifique se:")
            print("   - As tabelas dimensão estão carregadas")
            print("   - Os relacionamentos estão corretos")
            print("   - Use o script de verificação de integridade")
        
    else:
        print(f"\n❌ Carga falhou após {tempo_total}!")
        print("\n💡 Possíveis causas:")
        print("   1. Estrutura do Excel não corresponde à esperada")
        print("   2. Colunas obrigatórias faltando")
        print("   3. Tipos de dados incorretos")
        print("\n📋 Verifique:")
        print("   - Se removeu apenas colunas opcionais")
        print("   - Se manteve todos os campos obrigatórios listados acima")
        print("   - Os logs acima para mais detalhes!")

if __name__ == "__main__":
    main()