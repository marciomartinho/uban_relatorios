"""
Inicialização da aplicação Flask
"""
from flask import Flask
from config import config

def create_app(config_name='default'):
    """Factory pattern para criar a aplicação Flask"""
    
    # Criar instância do Flask
    app = Flask(__name__)
    
    # Carregar configurações
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Registrar blueprints
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.routes.saldo_receita import saldo_receita as saldo_receita_blueprint
    app.register_blueprint(saldo_receita_blueprint, url_prefix='/saldo-receita')
    
    from app.routes.saldo_despesa import saldo_despesa as saldo_despesa_blueprint
    app.register_blueprint(saldo_despesa_blueprint, url_prefix='/saldo-despesa')

    from app.routes.detalha_receita import detalha_receita
    app.register_blueprint(detalha_receita, url_prefix='/detalha-receita')

    from app.routes.detalha_despesa import detalha_despesa
    app.register_blueprint(detalha_despesa, url_prefix='/detalha-despesa')
    
    # Registrar filtros customizados para o Jinja2
    @app.template_filter('formato_moeda')
    def formato_moeda(valor):
        """Formata valor para moeda brasileira"""
        if valor is None:
            return ''
        try:
            # Formatar com separador de milhares e decimais brasileiros
            return f"{valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
        except:
            return str(valor)
    
    @app.template_filter('formato_mes')
    def formato_mes(mes):
        """Converte número do mês para nome"""
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        return meses.get(mes, str(mes))
    
    return app