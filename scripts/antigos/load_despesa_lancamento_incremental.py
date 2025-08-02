"""
Script para carga incremental de DespesaLancamento
Otimizado para processar arquivos grandes mensalmente
"""
import sys
import os
from datetime import datetime
import pandas as pd

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.etl_despesa_lancamento import ETLDespesaLancamento, validar_carga
from app.modules.database import db

def verificar_periodo_existente(tabela, periodo):
    """Verifica se um período já foi carregado"""
    query = f"""
    SELECT COUNT(*) 
    FROM {tabela}
    WHERE periodo = :periodo
    """
    result = db.execute_query(query, {"periodo": periodo})
    return result[0][0] > 0 if result else False

def analisar_arquivo_periodo(arquivo):
    """Analisa o arquivo para identificar o período dos dados"""
    try:
        print("📖 Lendo arquivo para análise... (amostra de 10.000 linhas)")
        # Para arquivos grandes, ler apenas amostra
        df = pd.read_excel(arquivo, nrows=10000)
        
        # Identificar períodos únicos
        df['periodo'] = df['COEXERCICIO'].astype(str) + '-' + df['INMES'].astype(str).str.zfill(2)
        periodos = df['periodo'].unique()
        
        # Contar registros (aproximado para arquivos grandes)
        print("📊 Estimando total de registros...")
        file_size = os.path.getsize(arquivo)
        # Aproximadamente 200 bytes por linha em Excel
        total_estimado = file_size // 200
        
        print(f"\n📅 Períodos encontrados no arquivo:")
        for p in sorted(periodos):
            print(f"   - {p}")
        
        return sorted(periodos), total_estimado
    except Exception as e:
        print(f"❌ Erro ao analisar arquivo: {e}")
        return [], 0

def main():
    """Executa carga incremental"""
    print("=" * 80)
    print("ETL - DESPESA LANÇAMENTO (CARGA INCREMENTAL)")
    print("=" * 80)
    
    # Verificar argumento do arquivo
    if len(sys.argv) < 2:
        arquivo = "dados_brutos/fato/DespesaLancamento.xlsx"
        print(f"\n⚠️  Nenhum arquivo especificado.")
        print(f"Usando arquivo padrão: {arquivo}")
        print("\n💡 Dica: Use 'python scripts/load_despesa_lancamento_incremental.py DespesaLancamentoJulho.xlsx'")
    else:
        arquivo = f"dados_brutos/fato/{sys.argv[1]}"
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo):
        print(f"\n❌ Arquivo não encontrado: {arquivo}")
        return
    
    print(f"\n📁 Arquivo: {arquivo}")
    
    # Analisar períodos no arquivo
    periodos, total_estimado = analisar_arquivo_periodo(arquivo)
    
    if not periodos:
        print("\n❌ Não foi possível identificar períodos no arquivo!")
        return
    
    print(f"\n📊 Total estimado de linhas: ~{total_estimado:,}")
    
    # Verificar períodos já carregados
    etl = ETLDespesaLancamento(chunk_size=10000)
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
            try:
                # Contar registros antes de deletar
                count_query = f"SELECT COUNT(*) FROM {etl.full_table_name} WHERE periodo = '{periodo}'"
                result = db.execute_query(count_query)
                registros_deletados = result[0][0] if result else 0
                
                # Deletar
                delete_query = f"DELETE FROM {etl.full_table_name} WHERE periodo = '{periodo}'"
                db.execute_ddl(delete_query)
                print(f"   - {periodo}: {registros_deletados:,} registros removidos")
            except Exception as e:
                print(f"   ❌ Erro ao remover {periodo}: {e}")
                return
    
    # Mostrar resumo antes de processar
    print(f"\n📋 RESUMO DA CARGA INCREMENTAL:")
    print(f"   Tabela destino: {etl.full_table_name}")
    print(f"   Tipo de carga: INCREMENTAL")
    novos_periodos = sorted(set(periodos) - set(periodos_existentes))
    if novos_periodos:
        print(f"   Períodos a carregar: {', '.join(novos_periodos)}")
    else:
        print(f"   Períodos a recarregar: {', '.join(periodos)}")
    print(f"   Total estimado: ~{total_estimado:,} registros")
    
    if total_estimado > 100000:
        minutos_min = (total_estimado // 50000) * 3
        minutos_max = (total_estimado // 50000) * 5
        print(f"\n⚠️  ATENÇÃO: Arquivo grande! Tempo estimado: {minutos_min}-{minutos_max} minutos")
    
    resposta = input("\n✅ Confirma o processamento? (S/n): ")
    if resposta.lower() == 'n':
        print("\n❌ Carga cancelada pelo usuário.")
        return
    
    print("\n🚀 Iniciando processamento...")
    print("💡 Dica: Para arquivos grandes, o processamento usa chunks otimizados.")
    print("   A barra de progresso é baseada em estimativa.\n")
    
    # Processar arquivo
    success = etl.process_file(arquivo, tipo_carga='incremental', recriar_tabela=False)
    
    if success:
        print("\n✅ Carga incremental concluída com sucesso!")
        
        # Validar carga completa
        validar_carga()
        
        # Mostrar registros dos novos períodos
        try:
            periodos_processados = novos_periodos if novos_periodos else periodos
            if periodos_processados:
                print(f"\n📊 VALIDAÇÃO DOS PERÍODOS CARREGADOS:")
                for periodo in sorted(periodos_processados):
                    query = f"""
                    SELECT 
                        COUNT(*) as registros,
                        COUNT(DISTINCT coug) as ugs,
                        COUNT(DISTINCT nudocumento) as documentos,
                        COUNT(DISTINCT coevento) as eventos,
                        SUM(CASE WHEN tipo_lancamento = 'DEBITO' THEN valancamento ELSE 0 END) as total_debito,
                        SUM(CASE WHEN tipo_lancamento = 'CREDITO' THEN valancamento ELSE 0 END) as total_credito
                    FROM {etl.full_table_name}
                    WHERE periodo = '{periodo}'
                    """
                    result = db.execute_query(query)
                    if result:
                        row = result[0]
                        print(f"\n   Período {periodo}:")
                        print(f"      - Registros: {row[0]:,}")
                        print(f"      - UGs: {row[1]}")
                        print(f"      - Documentos: {row[2]:,}")
                        print(f"      - Eventos: {row[3]}")
                        print(f"      - Total Débito: R$ {row[4]:,.2f}")
                        print(f"      - Total Crédito: R$ {row[5]:,.2f}")
                        print(f"      - Diferença: R$ {row[4] - row[5]:,.2f}")
        except Exception as e:
            print(f"\n⚠️  Erro ao validar períodos: {e}")
            
        # Verificar tabelas de controle
        print("\n📋 VERIFICANDO TABELAS DE CONTROLE:")
        try:
            # Verificar etl_control
            query_control = f"""
            SELECT ultima_carga_data, ultimo_periodo_carregado, total_registros_carregados, tipo_ultima_carga 
            FROM public.etl_control 
            WHERE tabela_nome = '{etl.full_table_name}'
            """
            result = db.execute_query(query_control)
            if result:
                row = result[0]
                print("   ✅ ETL_CONTROL atualizado:")
                print(f"      - Última carga: {row[0]}")
                print(f"      - Último período: {row[1]}")
                print(f"      - Total acumulado: {row[2]:,} registros")
                print(f"      - Tipo: {row[3]}")
            
            # Verificar último registro em etl_log
            query_log = f"""
            SELECT tipo_carga, periodo_dados, registros_inseridos, status, 
                   fim_processamento - inicio_processamento as tempo_processamento
            FROM public.etl_log 
            WHERE tabela_nome = '{etl.full_table_name}'
            ORDER BY id DESC
            LIMIT 1
            """
            result = db.execute_query(query_log)
            if result:
                row = result[0]
                print("\n   ✅ ETL_LOG - Última carga:")
                print(f"      - Tipo: {row[0]}")
                print(f"      - Período: {row[1]}")
                print(f"      - Registros: {row[2]:,}")
                print(f"      - Status: {row[3]}")
                print(f"      - Tempo: {row[4]}")
                
        except Exception as e:
            print(f"   ❌ Erro ao verificar tabelas de controle: {e}")
            
        print("\n🎉 SUCESSO! Não esqueça de atualizar o cache após esta carga:")
        print("   python scripts/otimizar_despesas.py")
            
    else:
        print("\n❌ Carga incremental falhou!")
        print("\n💡 Dicas para resolver:")
        print("   1. Verifique os logs acima para detalhes do erro")
        print("   2. Certifique-se de ter memória suficiente")
        print("   3. Tente processar um arquivo menor primeiro")
        print("   4. Verifique se o formato do Excel está correto")

if __name__ == "__main__":
    main()