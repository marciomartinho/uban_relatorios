"""
Script para corrigir/popular as tabelas de controle ETL
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import db

def fix_etl_control():
    """Popula as tabelas de controle baseado nos dados existentes"""
    
    print("=" * 60)
    print("CORREÇÃO DAS TABELAS DE CONTROLE ETL")
    print("=" * 60)
    
    tabela = 'receitas.fato_receita_saldo'
    
    try:
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
            print(f"\n❌ Tabela {tabela} está vazia!")
            return
        
        total_registros = result[0][0]
        periodo_min = result[0][1]
        periodo_max = result[0][2]
        total_periodos = result[0][3]
        
        print(f"\n📊 Estatísticas da tabela {tabela}:")
        print(f"   - Total de registros: {total_registros:,}")
        print(f"   - Período inicial: {periodo_min}")
        print(f"   - Período final: {periodo_max}")
        print(f"   - Total de períodos: {total_periodos}")
        
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
            'dados_brutos/fato/ReceitaSaldo.xlsx', 
            'inicial', 
            '{periodo_dados}',
            {total_registros}, 
            0, 
            0, 
            'sucesso',
            CURRENT_TIMESTAMP - INTERVAL '5 minutes',
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );
        """
        
        db.execute_ddl(sql_log)
        print("   ✅ etl_log atualizado!")
        
        # Verificar registros criados
        print(f"\n🔍 Verificando registros criados:")
        
        # Verificar etl_control
        control_check = db.execute_query(
            "SELECT * FROM public.etl_control WHERE tabela_nome = %s",
            (tabela,)
        )
        if control_check:
            row = control_check[0]
            print(f"\n   ETL_CONTROL:")
            print(f"   - Tabela: {row[1]}")
            print(f"   - Última carga: {row[2]}")
            print(f"   - Último período: {row[3]}")
            print(f"   - Total registros: {row[4]:,}")
            print(f"   - Tipo: {row[5]}")
        
        # Verificar etl_log
        log_check = db.execute_query(
            "SELECT COUNT(*) FROM public.etl_log WHERE tabela_nome = %s",
            (tabela,)
        )
        if log_check:
            print(f"\n   ETL_LOG:")
            print(f"   - Total de registros de log: {log_check[0][0]}")
        
        print(f"\n✅ Tabelas de controle corrigidas com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_etl_control()