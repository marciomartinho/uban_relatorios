"""
Inicialização da aplicação Flask
Arquivo: app/__init__.py
"""
from flask import Flask
from config import config
from app.modules.analise_visual_receitas import registrar_modulo
from .db_manager import db_manager

def create_app(config_name='default'):
    """Factory pattern para criar a aplicação Flask"""
    
    # Criar instância do Flask
    app = Flask(__name__)

    # Carregar configurações
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db_manager.init_app(app)

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

    from app.routes.rreo_receita import rreo_receita
    app.register_blueprint(rreo_receita, url_prefix='/rreo-receita')

    from app.routes.rreo_despesa import rreo_despesa
    app.register_blueprint(rreo_despesa, url_prefix='/rreo-despesa')

    from app.routes.rreo_despesa_funcao import rreo_despesa_funcao
    app.register_blueprint(rreo_despesa_funcao, url_prefix='/rreo-despesa-funcao')

    from app.routes.balanco_receita import balanco_receita
    app.register_blueprint(balanco_receita, url_prefix='/balanco-receita')

    # Registrar blueprints do Balanço Geral GDF
    from app.routes.balanco_geral.balanco_geral import balanco_geral
    from app.routes.balanco_geral.receita_estimada import receita_estimada_api
    from app.routes.balanco_geral.receita_tipo_administracao import receita_tipo_adm_api
    from app.routes.balanco_geral.previsao_atualizada import previsao_atualizada_api
    from app.routes.balanco_geral.receita_realizada import receita_realizada_api

    # Registrar o blueprint principal do balanço geral
    app.register_blueprint(balanco_geral, url_prefix='/balanco-geral')

    # Registrar as APIs dentro do contexto do balanço geral
    app.register_blueprint(receita_estimada_api, url_prefix='/balanco-geral')
    app.register_blueprint(receita_tipo_adm_api, url_prefix='/balanco-geral')
    app.register_blueprint(previsao_atualizada_api, url_prefix='/balanco-geral')
    app.register_blueprint(receita_realizada_api, url_prefix='/balanco-geral')

    from app.modules.comparativo_mensal_acumulado import comparativo_mensal
    app.register_blueprint(comparativo_mensal, url_prefix='/comparativo-mensal')

    registrar_modulo(app)

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