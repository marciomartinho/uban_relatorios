"""
Script para carga incremental de ReceitaSaldo
"""
import sys
import os
from datetime import datetime
import pandas as pd

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_receita_saldo import ETLReceitaSaldo, validar_carga
from app.modules.database import db

def verificar_periodo_existente(tabela, periodo):
    """Verifica se um período já foi carregado"""
    query = f"""
    SELECT COUNT(*) 
    FROM {tabela}
    WHERE periodo = '{periodo}'
    """
    result = db.execute_query(query)
    return result[0][0] > 0 if result else False

def analisar_arquivo_periodo(arquivo):
    """Analisa o arquivo para identificar o período dos dados"""
    try:
        df = pd.read_excel(arquivo)
        
        # Identificar períodos únicos
        df['periodo'] = df['COEXERCICIO'].astype(str) + '-' + df['INMES'].astype(str).str.zfill(2)
        periodos = df['periodo'].unique()
        
        print(f"\n📅 Períodos encontrados no arquivo:")
        for p in sorted(periodos):
            print(f"   - {p}")
        
        return sorted(periodos), len(df)
    except Exception as e:
        print(f"❌ Erro ao analisar arquivo: {e}")
        return [], 0

def main():
    """Executa carga incremental"""
    print("=" * 80)
    print("ETL - RECEITA SALDO (CARGA INCREMENTAL)")
    print("=" * 80)
    
    # Verificar argumento do arquivo
    if len(sys.argv) < 2:
        arquivo = "dados_brutos/fato/ReceitaSaldo.xlsx"
        print(f"\n⚠️  Nenhum arquivo especificado.")
        print(f"Usando arquivo padrão: {arquivo}")
        print("\n💡 Dica: Use 'python scripts/load_receita_saldo_incremental.py ReceitaSaldoJulho.xlsx'")
    else:
        arquivo = f"dados_brutos/fato/{sys.argv[1]}"
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo):
        print(f"\n❌ Arquivo não encontrado: {arquivo}")
        return
    
    print(f"\n📁 Arquivo: {arquivo}")
    
    # Analisar períodos no arquivo
    periodos, total_linhas = analisar_arquivo_periodo(arquivo)
    
    if not periodos:
        print("\n❌ Não foi possível identificar períodos no arquivo!")
        return
    
    print(f"\n📊 Total de linhas no arquivo: {total_linhas:,}")
    
    # Verificar períodos já carregados
    etl = ETLReceitaSaldo(chunk_size=5000)
    periodos_existentes = []
    
    print(f"\n🔍 Verificando períodos já carregados...")
    for periodo in periodos:
        if verificar_periodo_existente(etl.full_table_name, periodo):
            periodos_existentes.append(periodo)
            print(f"   ⚠️  {periodo} - JÁ EXISTE NO BANCO!")
        else:
            print(f"   ✅ {periodo} - Novo período")
    
    # Se todos os períodos já existem
    if len(periodos_existentes) == len(periodos):
        print("\n⚠️  ATENÇÃO: Todos os períodos do arquivo já foram carregados!")
        resposta = input("\nDeseja SOBRESCREVER os dados existentes? (s/N): ")
        
        if resposta.lower() != 's':
            print("\n❌ Carga cancelada pelo usuário.")
            return
        
        # Deletar períodos existentes
        print(f"\n🗑️  Removendo períodos existentes...")
        for periodo in periodos_existentes:
            delete_query = f"""
            DELETE FROM {etl.full_table_name}
            WHERE periodo = '{periodo}'
            """
            try:
                db.execute_ddl(delete_query)
                print(f"   - {periodo} removido")
            except Exception as e:
                print(f"   ❌ Erro ao remover {periodo}: {e}")
                return
    
    # Mostrar resumo antes de processar
    print(f"\n📋 RESUMO DA CARGA INCREMENTAL:")
    print(f"   Tabela destino: {etl.full_table_name}")
    print(f"   Tipo de carga: INCREMENTAL")
    print(f"   Períodos a carregar: {', '.join(sorted(set(periodos) - set(periodos_existentes)))}")
    
    resposta = input("\n✅ Confirma o processamento? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Carga cancelada pelo usuário.")
        return
    
    print("\n🚀 Iniciando processamento...\n")
    
    # Processar arquivo (tipo_carga='incremental' não limpa a tabela)
    success = etl.process_file(arquivo, tipo_carga='incremental', recriar_tabela=False)
    
    if success:
        print("\n✅ Carga incremental concluída com sucesso!")
        
        # Validar carga completa
        validar_carga()
        
        # Mostrar registros dos novos períodos
        try:
            novos_periodos = list(set(periodos) - set(periodos_existentes))
            if novos_periodos:
                print(f"\n📊 VALIDAÇÃO DOS NOVOS PERÍODOS CARREGADOS:")
                for periodo in sorted(novos_periodos):
                    query = f"""
                    SELECT 
                        COUNT(*) as registros,
                        SUM(vacredito) as total_credito,
                        SUM(vadebito) as total_debito
                    FROM {etl.full_table_name}
                    WHERE periodo = '{periodo}'
                    """
                    result = db.execute_query(query)
                    if result:
                        row = result[0]
                        print(f"\n   Período {periodo}:")
                        print(f"      - Registros: {row[0]:,}")
                        print(f"      - Total Crédito: R$ {row[1]:,.2f}")
                        print(f"      - Total Débito: R$ {row[2]:,.2f}")
        except Exception as e:
            print(f"\n⚠️  Erro ao validar novos períodos: {e}")
            
        # Verificar tabelas de controle
        print("\n📋 VERIFICANDO TABELAS DE CONTROLE:")
        try:
            # Verificar etl_control
            query_control = "SELECT * FROM public.etl_control WHERE tabela_nome = %s"
            result = db.execute_query(query_control, (etl.full_table_name,))
            if result:
                print("   ✅ Registro encontrado em etl_control")
            else:
                print("   ⚠️  Nenhum registro em etl_control")
            
            # Verificar etl_log
            query_log = """
            SELECT COUNT(*) as total_cargas, MAX(fim_processamento) as ultima_carga 
            FROM public.etl_log 
            WHERE tabela_nome = %s
            """
            result = db.execute_query(query_log, (etl.full_table_name,))
            if result and result[0][0] > 0:
                print(f"   ✅ {result[0][0]} registros em etl_log")
                print(f"   📅 Última carga: {result[0][1]}")
            else:
                print("   ⚠️  Nenhum registro em etl_log")
                
        except Exception as e:
            print(f"   ❌ Erro ao verificar tabelas de controle: {e}")
            
    else:
        print("\n❌ Carga incremental falhou!")

if __name__ == "__main__":
    main()