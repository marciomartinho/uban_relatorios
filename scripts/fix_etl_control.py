"""
Script para corrigir/popular as tabelas de controle ETL
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import db

def fix_etl_control(tabela=None):
    """Popula as tabelas de controle baseado nos dados existentes"""
    
    print("=" * 60)
    print("CORREÇÃO DAS TABELAS DE CONTROLE ETL")
    print("=" * 60)
    
    # Lista de tabelas conhecidas
    tabelas_conhecidas = [
        'receitas.fato_receita_saldo',
        'despesas.fato_despesa_saldo'
    ]
    
    # Se não especificou tabela, perguntar
    if not tabela:
        print("\nTabelas disponíveis:")
        for i, t in enumerate(tabelas_conhecidas, 1):
            print(f"   {i}. {t}")
        
        escolha = input("\nEscolha o número da tabela (ou 0 para todas): ")
        
        if escolha == '0':
            tabelas = tabelas_conhecidas
        else:
            try:
                idx = int(escolha) - 1
                tabelas = [tabelas_conhecidas[idx]]
            except:
                print("❌ Escolha inválida!")
                return
    else:
        tabelas = [tabela]
    
    # Processar cada tabela
    for tabela in tabelas:
        print(f"\n{'=' * 60}")
        print(f"Processando: {tabela}")
        print('=' * 60)
        
        try:
            # Verificar se a tabela existe
            schema_name = tabela.split('.')[0] if '.' in tabela else 'public'
            table_name = tabela.split('.')[1] if '.' in tabela else tabela
            
            query_exists = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = :schema_name 
                AND table_name = :table_name
            );
            """
            result = db.execute_query(query_exists, {"schema_name": schema_name, "table_name": table_name})
            
            if not result or not result[0][0]:
                print(f"❌ Tabela {tabela} não existe!")
                continue
            
            # Obter estatísticas da tabela
            query = f"""
            SELECT 
                COUNT(*) as total_registros,
                MIN(periodo) as periodo_min,
                MAX(periodo) as periodo_max,
                COUNT(DISTINCT periodo) as total_periodos
            FROM {tabela}
            """
            
            result = db.execute_query(query)
            if not result or result[0][0] == 0:
                print(f"❌ Tabela {tabela} está vazia!")
                continue
            
            total_registros = result[0][0]
            periodo_min = result[0][1]
            periodo_max = result[0][2]
            total_periodos = result[0][3]
            
            print(f"\n📊 Estatísticas da tabela {tabela}:")
            print(f"   - Total de registros: {total_registros:,}")
            print(f"   - Período inicial: {periodo_min}")
            print(f"   - Período final: {periodo_max}")
            print(f"   - Total de períodos: {total_periodos}")
            
            # Determinar arquivo de origem baseado no nome da tabela
            if 'receita' in tabela.lower():
                arquivo_origem = 'dados_brutos/fato/ReceitaSaldo.xlsx'
            elif 'despesa' in tabela.lower():
                arquivo_origem = 'dados_brutos/fato/DespesaSaldo.xlsx'
            else:
                arquivo_origem = 'dados_brutos/fato/arquivo_desconhecido.xlsx'
            
            # Inserir/Atualizar etl_control
            print(f"\n📝 Atualizando etl_control...")
            sql_control = f"""
            INSERT INTO public.etl_control (
                tabela_nome, 
                ultima_carga_data, 
                ultimo_periodo_carregado,
                total_registros_carregados, 
                tipo_ultima_carga,
                criado_em,
                atualizado_em
            ) VALUES (
                '{tabela}', 
                CURRENT_DATE, 
                '{periodo_max}',
                {total_registros}, 
                'inicial',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (tabela_nome) DO UPDATE SET
                ultima_carga_data = CURRENT_DATE,
                ultimo_periodo_carregado = '{periodo_max}',
                total_registros_carregados = {total_registros},
                tipo_ultima_carga = 'inicial',
                atualizado_em = CURRENT_TIMESTAMP;
            """
            
            db.execute_ddl(sql_control)
            print("   ✅ etl_control atualizado!")
            
            # Inserir registro em etl_log
            print(f"\n📝 Inserindo registro em etl_log...")
            periodo_dados = f"{periodo_min} a {periodo_max}" if periodo_min != periodo_max else periodo_max
            
            sql_log = f"""
            INSERT INTO public.etl_log (
                tabela_nome, 
                arquivo_origem, 
                tipo_carga, 
                periodo_dados,
                registros_inseridos, 
                registros_atualizados, 
                registros_erro, 
                status,
                inicio_processamento, 
                fim_processamento,
                criado_em
            ) VALUES (
                '{tabela}', 
                '{arquivo_origem}', 
                'inicial', 
                '{periodo_dados}',
                {total_registros}, 
                0, 
                0, 
                'sucesso',
                CURRENT_TIMESTAMP - INTERVAL '10 minutes',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            );
            """
            
            db.execute_ddl(sql_log)
            print("   ✅ etl_log atualizado!")
            
            print(f"\n✅ Tabela {tabela} corrigida com sucesso!")
            
        except Exception as e:
            print(f"\n❌ Erro ao processar {tabela}: {e}")
            import traceback
            traceback.print_exc()
    
    # Verificar registros criados
    print(f"\n{'=' * 60}")
    print("🔍 RESUMO FINAL:")
    print('=' * 60)
    
    try:
        # Verificar etl_control
        control_check = db.execute_query(
            "SELECT tabela_nome, ultimo_periodo_carregado, total_registros_carregados FROM public.etl_control ORDER BY tabela_nome"
        )
        
        if control_check:
            print("\n📋 ETL_CONTROL:")
            for row in control_check:
                print(f"   - {row[0]}: {row[2]:,} registros até {row[1]}")
        
        # Verificar etl_log
        log_check = db.execute_query(
            "SELECT tabela_nome, COUNT(*) FROM public.etl_log GROUP BY tabela_nome ORDER BY tabela_nome"
        )
        
        if log_check:
            print("\n📋 ETL_LOG:")
            for row in log_check:
                print(f"   - {row[0]}: {row[1]} registros de log")
        
    except Exception as e:
        print(f"\n❌ Erro ao verificar tabelas: {e}")

if __name__ == "__main__":
    # Se passar argumento, usa como nome da tabela
    if len(sys.argv) > 1:
        fix_etl_control(sys.argv[1])
    else:
        fix_etl_control()