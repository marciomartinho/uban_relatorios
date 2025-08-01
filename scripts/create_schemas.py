"""
Script para criar os schemas no banco de dados
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.modules.database import db

def create_schemas():
    """Cria os schemas necessários no banco"""
    
    print("=" * 60)
    print("CRIAÇÃO DE SCHEMAS")
    print("=" * 60)
    
    schemas = ['receitas', 'despesas', 'dimensoes']
    
    for schema in schemas:
        try:
            # Criar schema se não existir
            sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"
            db.execute_ddl(sql)
            print(f"✅ Schema '{schema}' criado/verificado")
            
        except Exception as e:
            print(f"❌ Erro ao criar schema '{schema}': {e}")
            return False
    
    # Listar schemas criados
    print("\n📋 Schemas no banco:")
    try:
        result = db.execute_query("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """)
        for row in result:
            print(f"   - {row[0]}")
    except Exception as e:
        print(f"❌ Erro ao listar schemas: {e}")
    
    print("\n✨ Schemas criados com sucesso!")
    return True

if __name__ == "__main__":
    create_schemas()