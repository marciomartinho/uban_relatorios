"""
Script para criar tabelas de controle do ETL
"""
import sys
import os

# Adiciona o diretório pai ao path para encontrar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import db
from datetime import datetime

def create_etl_tables():
    """Cria as tabelas de controle do processo ETL"""
    
    print("=" * 60)
    print("CRIAÇÃO DE TABELAS DE CONTROLE ETL")
    print("=" * 60)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # SQL para criar tabela de controle de cargas
    sql_etl_control = """
    CREATE TABLE IF NOT EXISTS etl_control (
        id SERIAL PRIMARY KEY,
        tabela_nome VARCHAR(100) NOT NULL UNIQUE,
        ultima_carga_data DATE,
        ultimo_periodo_carregado VARCHAR(7), -- formato: YYYY-MM
        total_registros_carregados INTEGER DEFAULT 0,
        tipo_ultima_carga VARCHAR(20), -- 'inicial' ou 'incremental'
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SQL para criar tabela de log de cargas
    sql_etl_log = """
    CREATE TABLE IF NOT EXISTS etl_log (
        id SERIAL PRIMARY KEY,
        tabela_nome VARCHAR(100) NOT NULL,
        arquivo_origem VARCHAR(255),
        tipo_carga VARCHAR(20), -- 'inicial' ou 'incremental'
        periodo_dados VARCHAR(7), -- formato: YYYY-MM
        registros_inseridos INTEGER DEFAULT 0,
        registros_atualizados INTEGER DEFAULT 0,
        registros_erro INTEGER DEFAULT 0,
        status VARCHAR(20), -- 'sucesso', 'erro', 'em_processamento'
        mensagem_erro TEXT,
        inicio_processamento TIMESTAMP,
        fim_processamento TIMESTAMP,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # SQL para criar função de atualização de timestamp
    sql_update_timestamp_function = """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.atualizado_em = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """
    
    # SQL para criar trigger de atualização
    sql_trigger_etl_control = """
    DROP TRIGGER IF EXISTS update_etl_control_updated_at ON etl_control;
    
    CREATE TRIGGER update_etl_control_updated_at 
    BEFORE UPDATE ON etl_control
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
    """
    
    try:
        # 1. Criar tabela etl_control
        print("📋 Criando tabela 'etl_control'...")
        db.execute_ddl(sql_etl_control)
        print("✅ Tabela 'etl_control' criada com sucesso!")
        
        # 2. Criar tabela etl_log
        print("\n📋 Criando tabela 'etl_log'...")
        db.execute_ddl(sql_etl_log)
        print("✅ Tabela 'etl_log' criada com sucesso!")
        
        # 3. Criar função de atualização de timestamp
        print("\n⚙️ Criando função de atualização de timestamp...")
        db.execute_ddl(sql_update_timestamp_function)
        print("✅ Função criada com sucesso!")
        
        # 4. Criar trigger
        print("\n⚙️ Criando trigger de atualização...")
        db.execute_ddl(sql_trigger_etl_control)
        print("✅ Trigger criado com sucesso!")
        
        # 5. Criar índices para melhor performance
        print("\n📊 Criando índices...")
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_etl_log_tabela ON etl_log(tabela_nome);",
            "CREATE INDEX IF NOT EXISTS idx_etl_log_periodo ON etl_log(periodo_dados);",
            "CREATE INDEX IF NOT EXISTS idx_etl_log_status ON etl_log(status);",
            "CREATE INDEX IF NOT EXISTS idx_etl_control_tabela ON etl_control(tabela_nome);"
        ]
        
        for idx in indices:
            db.execute_ddl(idx)
        
        print("✅ Índices criados com sucesso!")
        
        # 6. Verificar se as tabelas foram criadas
        print("\n🔍 Verificando tabelas criadas...")
        if db.table_exists('etl_control'):
            print("   ✅ Tabela 'etl_control' verificada")
        if db.table_exists('etl_log'):
            print("   ✅ Tabela 'etl_log' verificada")
        
        print("\n" + "=" * 60)
        print("✨ TABELAS DE CONTROLE ETL CRIADAS COM SUCESSO!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERRO ao criar tabelas: {e}")
        print("\nVerifique a conexão com o banco de dados e tente novamente.")
        return False
    
    return True

def show_table_structure():
    """Mostra a estrutura das tabelas criadas"""
    print("\n📊 ESTRUTURA DAS TABELAS CRIADAS:")
    print("-" * 60)
    
    for table in ['etl_control', 'etl_log']:
        if db.table_exists(table):
            print(f"\nTabela: {table}")
            columns = db.get_table_info(table)
            for col in columns:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                print(f"   - {col[0]:<30} {col[1]:<20} {nullable}")

if __name__ == "__main__":
    if create_etl_tables():
        show_table_structure()