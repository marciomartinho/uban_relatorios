"""
Entry point para executar a aplicação Flask
"""
import os
from app import create_app

# Criar a aplicação
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Executar a aplicação
    print("=" * 60)
    print("SISTEMA DE RELATÓRIOS UBAN")
    print("=" * 60)
    print(f"Ambiente: {app.config['FLASK_ENV']}")
    print(f"Debug: {app.config['DEBUG']}")
    print(f"Banco: {app.config['DB_NAME']}")
    print("=" * 60)
    print("\n🚀 Servidor iniciado!")
    print("📌 Acesse: http://localhost:5000")
    print("\nPressione CTRL+C para parar\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )