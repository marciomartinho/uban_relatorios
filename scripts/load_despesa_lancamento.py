"""
Script para carregar dados de DespesaLancamento.xlsx
Otimizado para processar mais de 1 milhão de registros
"""
import sys
import os

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_despesa_lancamento import ETLDespesaLancamento, validar_carga

def main():
    """Executa o ETL de DespesaLancamento"""
    print("=" * 80)
    print("ETL - DESPESA LANÇAMENTO")
    print("=" * 80)
    
    etl = ETLDespesaLancamento(chunk_size=10000)
    file_path = "dados_brutos/fato/DespesaLancamento.xlsx"
    
    print(f"\n📁 Arquivo: {file_path}")
    print(f"📦 Processamento em chunks de: {etl.chunk_size:,} linhas")
    print(f"🎯 Tabela destino: {etl.full_table_name}")
    print(f"⚠️  ATENÇÃO: Este arquivo contém ~1.000.000+ registros!")
    print(f"⏱️  Tempo estimado: 15-30 minutos\n")
    
    # Perguntar se deve recriar a tabela
    resposta = input("\n⚠️  Deseja RECRIAR a tabela (apagar e criar nova estrutura)? (s/N): ")
    recriar = resposta.lower() == 's'
    
    if recriar:
        print("\n🔄 A tabela será RECRIADA com a nova estrutura...")
    else:
        print("\n➕ Mantendo tabela existente...")
    
    print("\nIniciando processamento...\n")
    print("💡 Dica: O processamento usa chunks para otimizar memória.")
    print("   Não se preocupe se parecer lento no início - está otimizando!")
    
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
                conatureza,
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
                print(f"      Natureza: {row[7] or 'N/A'}")
                print(f"      Subelemento: {row[8] or 'N/A'}")
                
        except Exception as e:
            print(f"\nErro ao mostrar exemplos: {e}")
            
    else:
        print("\n❌ ETL falhou!")
        print("\n💡 Dicas para resolver:")
        print("   1. Verifique se o arquivo existe no caminho correto")
        print("   2. Certifique-se de ter memória suficiente (mínimo 4GB livres)")
        print("   3. Verifique a conexão com o banco de dados")
        print("   4. Olhe os logs acima para mais detalhes do erro")

if __name__ == "__main__":
    main()