"""
Módulo de Análise Visual das Receitas
Gera gráficos dinâmicos para visualização de dados do Balanço Orçamentário
"""
from flask import Blueprint, jsonify, render_template_string
import json

# Criar blueprint para o módulo de visualização
analise_visual = Blueprint('analise_visual', __name__)

@analise_visual.route('/api/dados-graficos')
def get_dados_graficos():
    """
    Endpoint para processar dados para os gráficos
    Recebe os dados do relatório e retorna estruturado para visualização
    """
    try:
        # Este endpoint será chamado via JavaScript passando os dados
        return jsonify({
            'status': 'success',
            'message': 'Módulo de análise visual carregado'
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

def processar_dados_para_graficos(dados_relatorio):
    """
    Processa os dados do relatório para formato adequado aos gráficos
    """
    graficos_data = {
        'distribuicao_categorias': [],
        'distribuicao_origens': [],
        'comparativo_exercicios': [],
        'evolucao_realizacao': []
    }
    
    # Processar dados por categoria
    categorias = {}
    origens = {}
    
    for item in dados_relatorio.get('dados', []):
        if item['nivel'] == 0:  # Categorias
            categorias[item['codigo']] = {
                'nome': item['descricao'],
                'valor': item['receita_atual'],
                'percentual': 0
            }
        elif item['nivel'] == 1:  # Fontes/Origens
            origens[item['codigo']] = {
                'nome': item['descricao'],
                'valor': item['receita_atual'],
                'categoria': item.get('categoria_pai', ''),
                'percentual': 0
            }
    
    # Calcular percentuais
    total_categorias = sum(cat['valor'] for cat in categorias.values())
    total_origens = sum(ori['valor'] for ori in origens.values())
    
    if total_categorias > 0:
        for cat in categorias.values():
            cat['percentual'] = (cat['valor'] / total_categorias) * 100
    
    if total_origens > 0:
        for ori in origens.values():
            ori['percentual'] = (ori['valor'] / total_origens) * 100
    
    return {
        'categorias': categorias,
        'origens': origens,
        'totais': dados_relatorio.get('totais', {})
    }

# Template HTML para o componente de análise visual
TEMPLATE_ANALISE_VISUAL = """
<div class="analise-visual-container mt-4">
    <div class="card">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">
                <i class="bi bi-graph-up"></i> Análise Visual das Receitas
                <span class="text-muted float-end">{{ periodo }}</span>
            </h5>
        </div>
        <div class="card-body">
            <ul class="nav nav-tabs" id="graficosTab" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="categorias-tab" data-bs-toggle="tab" 
                            data-bs-target="#categorias" type="button" role="tab">
                        Por Categorias
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="origens-tab" data-bs-toggle="tab" 
                            data-bs-target="#origens" type="button" role="tab">
                        Por Origens
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="comparativo-tab" data-bs-toggle="tab" 
                            data-bs-target="#comparativo" type="button" role="tab">
                        Comparativo
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="evolucao-tab" data-bs-toggle="tab" 
                            data-bs-target="#evolucao" type="button" role="tab">
                        Evolução
                    </button>
                </li>
            </ul>
            
            <div class="tab-content" id="graficosTabContent">
                <div class="tab-pane fade show active" id="categorias" role="tabpanel">
                    <div class="row mt-3">
                        <div class="col-md-8">
                            <canvas id="chartCategorias"></canvas>
                        </div>
                        <div class="col-md-4">
                            <div id="legendaCategorias"></div>
                        </div>
                    </div>
                </div>
                
                <div class="tab-pane fade" id="origens" role="tabpanel">
                    <div class="row mt-3">
                        <div class="col-md-8">
                            <canvas id="chartOrigens"></canvas>
                        </div>
                        <div class="col-md-4">
                            <div id="legendaOrigens"></div>
                        </div>
                    </div>
                </div>
                
                <div class="tab-pane fade" id="comparativo" role="tabpanel">
                    <div class="mt-3">
                        <canvas id="chartComparativo"></canvas>
                    </div>
                </div>
                
                <div class="tab-pane fade" id="evolucao" role="tabpanel">
                    <div class="mt-3">
                        <canvas id="chartEvolucao"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
"""

def registrar_modulo(app):
    """
    Registra o módulo de análise visual na aplicação Flask
    """
    app.register_blueprint(analise_visual, url_prefix='/analise-visual')
    
    # Adicionar template ao contexto
    @app.context_processor
    def inject_templates():
        return {
            'analise_visual_template': TEMPLATE_ANALISE_VISUAL
        }