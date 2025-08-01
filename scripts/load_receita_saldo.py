"""
Script para carregar dados de ReceitaSaldo.xlsx
"""
import sys
import os

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_receita_saldo import ETLReceitaSaldo, validar_carga

def main():
    """Executa o ETL de ReceitaSaldo"""
    print("=" * 80)
    print("ETL - RECEITA SALDO")
    print("=" * 80)
    
    etl = ETLReceitaSaldo(chunk_size=5000)
    file_path = "dados_brutos/fato/ReceitaSaldo.xlsx"
    
    print(f"\n📁 Arquivo: {file_path}")
    print(f"📦 Processamento em chunks de: {etl.chunk_size:,} linhas")
    print(f"🎯 Tabela destino: {etl.full_table_name}")
    
    # Perguntar se deve recriar a tabela
    resposta = input("\n⚠️  Deseja RECRIAR a tabela (apagar e criar nova estrutura)? (s/N): ")
    recriar = resposta.lower() == 's'
    
    if recriar:
        print("\n🔄 A tabela será RECRIADA com a nova estrutura...")
    else:
        print("\n➕ Mantendo tabela existente...")
    
    print("\nIniciando processamento...\n")
    
    success = etl.process_file(file_path, tipo_carga='inicial', recriar_tabela=recriar)
    
    if success:
        print("\n✅ ETL concluído com sucesso!")
        
        # Mostrar estatísticas detalhadas
        validar_carga()
        
        # Mostrar exemplo de dados com as novas colunas
        try:
            from app.modules.database import db
            print("\n📋 EXEMPLO DE DADOS CARREGADOS (primeiros 3 registros):")
            query = f"""
            SELECT 
                periodo,
                cocontacontabil,
                LENGTH(cocontacorrente) as tam_conta,
                cofonte,
                cocategoriareceita,
                cofontereceita,
                vacredito,
                vadebito,
                saldo_contabil_receita
            FROM {etl.full_table_name}
            WHERE cofonte IS NOT NULL
            LIMIT 3
            """
            result = db.execute_query(query)
            
            for i, row in enumerate(result, 1):
                print(f"\n   Registro {i}:")
                print(f"      Período: {row[0]}")
                print(f"      Conta Contábil: {row[1]}")
                print(f"      Tamanho Conta: {row[2]}")
                print(f"      COFONTE: {row[3]}")
                print(f"      Categoria Receita: {row[4]}")
                print(f"      Fonte Receita: {row[5]}")
                print(f"      Crédito: R$ {row[6]:,.2f}")
                print(f"      Débito: R$ {row[7]:,.2f}")
                print(f"      Saldo Contábil: R$ {row[8]:,.2f}")
                
        except Exception as e:
            print(f"\nErro ao mostrar exemplos: {e}")
            
    else:
        print("\n❌ ETL falhou!")

if __name__ == "__main__":
    main()