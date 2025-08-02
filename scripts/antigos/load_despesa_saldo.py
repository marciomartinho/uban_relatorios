"""
Script para carregar dados de DespesaSaldo.xlsx
"""
import sys
import os

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_despesa_saldo import ETLDespesaSaldo, validar_carga

def main():
    """Executa o ETL de DespesaSaldo"""
    print("=" * 80)
    print("ETL - DESPESA SALDO")
    print("=" * 80)
    
    etl = ETLDespesaSaldo(chunk_size=10000)  # Chunks maiores devido ao volume
    file_path = "dados_brutos/fato/DespesaSaldo.xlsx"
    
    print(f"\n📁 Arquivo: {file_path}")
    print(f"📦 Processamento em chunks de: {etl.chunk_size:,} linhas")
    print(f"🎯 Tabela destino: {etl.full_table_name}")
    print(f"⚠️  ATENÇÃO: Este arquivo contém 560.110 registros!")
    print(f"⏱️  Tempo estimado: 5-10 minutos\n")
    
    # Perguntar se deve recriar a tabela
    resposta = input("⚠️  Deseja RECRIAR a tabela (apagar e criar nova estrutura)? (s/N): ")
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
            print("\n📋 EXEMPLO DE DADOS CARREGADOS (primeiros 3 registros com subelemento):")
            query = f"""
            SELECT 
                periodo,
                cocontacontabil,
                coug,
                conatureza,
                cogrupo,
                comodalidade,
                coelemento,
                cosubelemento,
                vacredito,
                vadebito,
                saldo_contabil_despesa
            FROM {etl.full_table_name}
            WHERE cosubelemento IS NOT NULL
            LIMIT 3
            """
            result = db.execute_query(query)
            
            if result:
                for i, row in enumerate(result, 1):
                    print(f"\n   Registro {i}:")
                    print(f"      Período: {row[0]}")
                    print(f"      Conta Contábil: {row[1]}")
                    print(f"      UG: {row[2]}")
                    print(f"      Natureza: {row[3]}")
                    print(f"      Grupo: {row[4]}")
                    print(f"      Modalidade: {row[5]}")
                    print(f"      Elemento: {row[6]}")
                    print(f"      Subelemento: {row[7]}")
                    print(f"      Crédito: R$ {row[8]:,.2f}")
                    print(f"      Débito: R$ {row[9]:,.2f}")
                    print(f"      Saldo Contábil: R$ {row[10]:,.2f}")
            else:
                print("   Nenhum registro com subelemento encontrado.")
                
        except Exception as e:
            print(f"\nErro ao mostrar exemplos: {e}")
            
    else:
        print("\n❌ ETL falhou!")

if __name__ == "__main__":
    main()