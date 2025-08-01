import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

class Config:
    """Configurações gerais da aplicação"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'chave-desenvolvimento-insegura'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    DEBUG = FLASK_ENV == 'development'
    
    # Database
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME')
    
    # URL de conexão do SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    # Desabilita notificações do SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de upload (para os arquivos Excel)
    UPLOAD_FOLDER = 'dados_brutos'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max

    @staticmethod
    def init_app(app):
        """Inicializa configurações específicas da aplicação"""
        pass

class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    DEBUG = True

class ProductionConfig(Config):
    """Configurações de produção"""
    DEBUG = False

# Dicionário de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}