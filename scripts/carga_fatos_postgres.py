#!/usr/bin/env python3
"""
Script unificado para carregar arquivos de FATO (lançamentos e saldos)
para o banco de dados PostgreSQL na VPS.
Uso: python carga_fatos_postgres.py <nome_do_arquivo_excel.xlsx>
"""
import sys
import os
from datetime import datetime
from pathlib import Path
import pandas as pd

# Adiciona o diretório raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa a conexão do PostgreSQL
from app.modules.database import db

# Importa as classes de transformação de dados que já existem
from app.modules.etl_despesa_lancamento_duckdb import ETLDespesaLancamentoDuckDB
from app.modules.etl_receita_lancamento_duckdb import ETLReceitaLancamentoDuckDB
from app.modules.etl_despesa_saldo_duckdb import ETLDespesaSaldoDuckDB
from app.modules.etl_receita_saldo_duckdb import ETLReceitaSaldoDuckDB

def carregar_dados_fato(nome_arquivo):
    """
    Processa um único arquivo de fato (Excel) e o carrega no PostgreSQL.
    """
    caminho_arquivo = Path("dados_brutos/fato") / nome_arquivo
    
    if not caminho_arquivo.exists():
        print(f"❌ ERRO: Arquivo não encontrado: {caminho_arquivo}")
        return

    print("=" * 80)
    print(f"📄 Iniciando carga do arquivo: {nome_arquivo}")
    print("=" * 80)

    # Identifica o tipo de ETL e a tabela de destino com base no nome do arquivo
    etl_instance = None
    table_name = None
    if "DespesaLancamento" in nome_arquivo:
        etl_instance = ETLDespesaLancamentoDuckDB()
        table_name = 'despesa_lancamento'
    elif "ReceitaLancamento" in nome_arquivo:
        etl_instance = ETLReceitaLancamentoDuckDB()
        table_name = 'receita_lancamento'
    elif "DespesaSaldo" in nome_arquivo:
        etl_instance = ETLDespesaSaldoDuckDB()
        table_name = 'despesa_saldo'
    elif "ReceitaSaldo" in nome_arquivo:
        etl_instance = ETLReceitaSaldoDuckDB()
        table_name = 'receita_saldo'

    if not etl_instance:
        print(f"❌ ERRO: Não foi possível determinar o tipo de ETL para o arquivo '{nome_arquivo}'")
        return

    try:
        # 1. Ler o arquivo Excel completo para um DataFrame do pandas
        print(f"📖 Lendo arquivo Excel (isso pode demorar para arquivos grandes)...")
        df_completo = pd.read_excel(caminho_arquivo, engine='openpyxl')
        print(f"   ✅ Leitura concluída: {len(df_completo):,} linhas encontradas.")

        # 2. Usar a lógica de transformação que você já criou!
        print("⚙️  Aplicando transformações de dados...")
        df_transformado = etl_instance.transform_data(df_completo)
        print("   ✅ Transformação concluída.")

        # 3. Carregar o DataFrame transformado no PostgreSQL
        print(f"🚀 Conectando à VPS e inserindo dados na tabela '{table_name}'...")
        
        # 'append' adiciona os dados. Se a tabela já tiver dados de outro mês,
        # os novos serão adicionados no final.
        df_transformado.to_sql(
            name=table_name,
            con=db.engine,
            if_exists='append',
            index=False,
            chunksize=10000  # Insere os dados em lotes para melhor performance
        )
        
        print(f"🎉 SUCESSO! {len(df_transformado):,} registros foram carregados no PostgreSQL.")

    except Exception as e:
        print(f"🔥 OCORREU UM ERRO DURANTE A CARGA: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Função principal que gerencia a execução do script."""
    if len(sys.argv) < 2:
        print("\n❌ ERRO: Você precisa especificar o nome do arquivo Excel para carregar.")
        print("\n💡 Uso correto:")
        print("   python scripts/carga_fatos_postgres.py DespesaLancamentoJulho.xlsx")
        print("   python scripts/carga_fatos_postgres.py ReceitaSaldoAgosto.xlsx\n")
        return
        
    nome_arquivo = sys.argv[1]
    carregar_dados_fato(nome_arquivo)

if __name__ == "__main__":
    main()