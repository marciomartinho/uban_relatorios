"""
Script para testar conexão e criar o banco de dados
"""
import sys
import os

# Adiciona o diretório atual ao path do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Agora importa direto do local correto
from app.modules.database import db

def main():
    print("=" * 50)
    print("TESTE DE CONEXÃO COM POSTGRESQL")
    print("=" * 50)
    
    # Primeiro, tenta criar o banco se não existir
    print("\n1. Criando banco de dados (se necessário)...")
    try:
        db.create_database_if_not_exists()
    except Exception as e:
        print(f"Erro ao criar banco: {e}")
        return
    
    # Depois testa a conexão
    print("\n2. Testando conexão com o banco...")
    if db.test_connection():
        print("\n✅ SUCESSO! Banco de dados pronto para uso!")
        
        # Lista os bancos existentes
        print("\n3. Bancos de dados no servidor:")
        try:
            result = db.execute_query(
                "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"
            )
            for row in result:
                print(f"   - {row[0]}")
        except Exception as e:
            print(f"Erro ao listar bancos: {e}")
    else:
        print("\n❌ FALHA na conexão!")

if __name__ == "__main__":
    main()