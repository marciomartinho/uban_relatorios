"""
Script para carregar dados de ReceitaLancamento.xlsx
"""
import sys
import os

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_receita_lancamento import ETLReceitaLancamento, validar_carga

def main():
    """Executa o ETL de ReceitaLancamento"""
    print("=" * 80)
    print("ETL - RECEITA LANÇAMENTO")
    print("=" * 80)
    
    etl = ETLReceitaLancamento(chunk_size=10000)
    file_path = "dados_brutos/fato/ReceitaLancamento.xlsx"
    
    print(f"\n📁 Arquivo: {file_path}")
    print(f"📦 Processamento em chunks de: {etl.chunk_size:,} linhas")
    print(f"🎯 Tabela destino: {etl.full_table_name}")
    print(f"⚠️  ATENÇÃO: Este arquivo contém 490.122 registros!")
    print(f"⏱️  Tempo estimado: 5-10 minutos\n")
    
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
        
        # Mostrar exemplo de dados
        try:
            from app.modules.database import db
            print("\n📋 EXEMPLO DE DADOS CARREGADOS (primeiros 3 registros com parse):")
            query = f"""
            SELECT 
                periodo,
                nudocumento,
                cocontacontabil,
                LENGTH(cocontacorrente) as tam_conta,
                tipo_lancamento,
                valancamento,
                cofonte,
                inesfera,
                cosubelemento
            FROM {etl.full_table_name}
            WHERE cofonte IS NOT NULL
            LIMIT 3
            """
            result = db.execute_query(query)
            
            for i, row in enumerate(result, 1):
                print(f"\n   Registro {i}:")
                print(f"      Período: {row[0]}")
                print(f"      Documento: {row[1]}")
                print(f"      Conta Contábil: {row[2]}")
                print(f"      Tamanho Conta: {row[3]} chars")
                print(f"      Tipo: {row[4]}")
                print(f"      Valor: R$ {row[5]:,.2f}")
                print(f"      Fonte: {row[6]}")
                print(f"      Esfera: {row[7] or 'N/A'}")
                print(f"      Subelemento: {row[8] or 'N/A'}")
                
        except Exception as e:
            print(f"\nErro ao mostrar exemplos: {e}")
            
    else:
        print("\n❌ ETL falhou!")

if __name__ == "__main__":
    main()