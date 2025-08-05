#!/usr/bin/env python3
"""
Script unificado para carga mensal das 4 tabelas no DuckDB
Uso: python scripts/carga_mensal_duckdb.py Julho
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from pathlib import Path

# Importar ETLs
from app.modules.etl_despesa_lancamento_duckdb import ETLDespesaLancamentoDuckDB
from app.modules.etl_receita_lancamento_duckdb import ETLReceitaLancamentoDuckDB
from app.modules.etl_despesa_saldo_duckdb import ETLDespesaSaldoDuckDB
from app.modules.etl_receita_saldo_duckdb import ETLReceitaSaldoDuckDB

def validar_arquivos_mes(mes):
    """Valida se todos os arquivos do mês existem"""
    pasta = Path("dados_brutos/fato")
    arquivos_necessarios = [
        f"DespesaLancamento{mes}.xlsx",
        f"DespesaSaldo{mes}.xlsx",
        f"ReceitaLancamento{mes}.xlsx",
        f"ReceitaSaldo{mes}.xlsx"
    ]
    
    arquivos_existentes = []
    arquivos_faltando = []
    
    for arquivo in arquivos_necessarios:
        caminho = pasta / arquivo
        if caminho.exists():
            arquivos_existentes.append(arquivo)
        else:
            arquivos_faltando.append(arquivo)
    
    return arquivos_existentes, arquivos_faltando

def processar_arquivo(tipo_arquivo, nome_arquivo, mes):
    """Processa um arquivo específico"""
    caminho_arquivo = f"dados_brutos/fato/{nome_arquivo}"
    
    print(f"\n{'='*60}")
    print(f"📄 Processando: {nome_arquivo}")
    print(f"{'='*60}")
    
    # Escolher ETL correto
    if tipo_arquivo == "DespesaLancamento":
        etl = ETLDespesaLancamentoDuckDB(chunk_size=50000)
    elif tipo_arquivo == "ReceitaLancamento":
        etl = ETLReceitaLancamentoDuckDB(chunk_size=10000)
    elif tipo_arquivo == "DespesaSaldo":
        etl = ETLDespesaSaldoDuckDB(chunk_size=10000)
    else:  # ReceitaSaldo
        etl = ETLReceitaSaldoDuckDB(chunk_size=5000)
    
    # Analisar arquivo
    periodos, total_estimado = etl.analisar_arquivo(caminho_arquivo)
    
    if not periodos:
        print(f"❌ Não foi possível identificar períodos no arquivo!")
        return False
    
    print(f"📅 Períodos encontrados: {', '.join(sorted(periodos))}")
    print(f"📊 Total estimado: ~{total_estimado:,} registros")
    
    # Verificar períodos existentes
    periodos_existentes = []
    for periodo in periodos:
        if etl.validar_periodo_existente(periodo):
            periodos_existentes.append(periodo)
    
    sobrescrever = False
    if periodos_existentes:
        print(f"\n⚠️ ATENÇÃO: Os seguintes períodos já existem:")
        for p in periodos_existentes:
            print(f"   - {p}")
        
        resposta = input("\n❓ Deseja SOBRESCREVER? (s/N): ")
        if resposta.lower() != 's':
            print("⏭️ Pulando este arquivo...")
            return False
        sobrescrever = True
    
    # Processar
    inicio = datetime.now()
    print(f"\n🚀 Processando {tipo_arquivo}...")
    
    sucesso = etl.processar_arquivo(caminho_arquivo, sobrescrever=sobrescrever)
    
    tempo_total = datetime.now() - inicio
    
    if sucesso:
        print(f"✅ {tipo_arquivo} processado com sucesso em {tempo_total}!")
    else:
        print(f"❌ Erro ao processar {tipo_arquivo}")
    
    return sucesso

def main():
    """Função principal"""
    print("=" * 80)
    print("CARGA MENSAL UNIFICADA - DUCKDB")
    print("=" * 80)
    
    # Verificar argumento
    if len(sys.argv) < 2:
        print("\n❌ ERRO: Você precisa especificar o mês!")
        print("\n💡 Uso correto:")
        print("   python scripts/carga_mensal_duckdb.py Julho")
        print("   python scripts/carga_mensal_duckdb.py Agosto")
        print("   python scripts/carga_mensal_duckdb.py Setembro")
        return
    
    mes = sys.argv[1]
    print(f"\n📅 Processando dados do mês: {mes}")
    
    # Validar arquivos
    print("\n🔍 Verificando arquivos...")
    arquivos_existentes, arquivos_faltando = validar_arquivos_mes(mes)
    
    if arquivos_faltando:
        print(f"\n❌ ERRO: Arquivos faltando:")
        for arq in arquivos_faltando:
            print(f"   - {arq}")
        print("\n💡 Certifique-se de que todos os 4 arquivos estejam na pasta dados_brutos/fato/")
        return
    
    print(f"\n✅ Todos os arquivos encontrados:")
    for arq in arquivos_existentes:
        print(f"   - {arq}")
    
    # Confirmar processamento
    print(f"\n📋 RESUMO DA CARGA:")
    print(f"   Mês: {mes}")
    print(f"   Arquivos: 4")
    print(f"   Banco: dados_brutos/fato/db_local/uban.duckdb")
    
    resposta = input("\n✅ Confirma o processamento? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Carga cancelada pelo usuário.")
        return
    
    # Processar cada arquivo
    inicio_total = datetime.now()
    resultados = {
        "DespesaLancamento": False,
        "DespesaSaldo": False,
        "ReceitaLancamento": False,
        "ReceitaSaldo": False
    }
    
    # Ordem de processamento (lançamentos primeiro, depois saldos)
    ordem = [
        ("DespesaLancamento", f"DespesaLancamento{mes}.xlsx"),
        ("ReceitaLancamento", f"ReceitaLancamento{mes}.xlsx"),
        ("DespesaSaldo", f"DespesaSaldo{mes}.xlsx"),
        ("ReceitaSaldo", f"ReceitaSaldo{mes}.xlsx")
    ]
    
    for tipo, arquivo in ordem:
        try:
            resultados[tipo] = processar_arquivo(tipo, arquivo, mes)
        except Exception as e:
            print(f"\n❌ Erro ao processar {tipo}: {e}")
            resultados[tipo] = False
    
    # Resumo final
    tempo_total = datetime.now() - inicio_total
    
    print("\n" + "=" * 80)
    print("RESUMO DO PROCESSAMENTO")
    print("=" * 80)
    
    todos_sucesso = True
    for tipo, sucesso in resultados.items():
        status = "✅ SUCESSO" if sucesso else "❌ FALHOU"
        print(f"{tipo:.<30} {status}")
        if not sucesso:
            todos_sucesso = False
    
    print(f"\nTempo total: {tempo_total}")
    
    if todos_sucesso:
        print("\n🎉 CARGA MENSAL CONCLUÍDA COM SUCESSO!")
        print("\n📌 Próximos passos:")
        print("   1. Conferir os dados:")
        print("      python scripts/relatorio_conferencia_duckdb.py")
        print("   2. Consultar dados específicos:")
        print("      python scripts/consultar_lancamentos_duckdb.py")
    else:
        print("\n⚠️ CARGA MENSAL CONCLUÍDA COM ERROS!")
        print("   Verifique os logs acima para detalhes.")

if __name__ == "__main__":
    main()