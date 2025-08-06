"""
Inicialização do módulo balanco_geral
Arquivo: app/routes/balanco_geral/__init__.py
"""

# Importar os blueprints dos arquivos
from .balanco_geral import balanco_geral
from .receita_estimada import receita_estimada_api
from .receita_tipo_administracao import receita_tipo_adm_api
from .previsao_atualizada import previsao_atualizada_api
from .receita_realizada import receita_realizada_api

# Exportar os blueprints para uso no app principal
__all__ = ['balanco_geral', 'receita_estimada_api', 'receita_tipo_adm_api', 'previsao_atualizada_api', 'receita_realizada_api']