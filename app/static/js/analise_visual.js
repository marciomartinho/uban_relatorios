/**
 * Módulo de Análise Visual das Receitas
 * Responsável pela criação e atualização dos gráficos
 */

class AnaliseVisualReceitas {
    constructor() {
        this.charts = {};
        this.cores = {
            categorias: [
                '#1e3c72', '#2a5298', '#3468c0', '#4d7ea8', '#6395b0',
                '#7aabb8', '#91c1c0', '#a8d8c8', '#bfeed0', '#d6ffd8'
            ],
            origens: [
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57',
                '#54A0FF', '#48C9B0', '#F8B500', '#FF6348', '#786FA6',
                '#FDA7DF', '#4834D4', '#30336B', '#22A6B3', '#6C5CE7'
            ]
        };
        this.dadosOriginais = null;
        this.filtroAtivo = 'todas';
    }

    /**
     * Inicializa o módulo com os dados do relatório
     */
    inicializar(dadosRelatorio) {
        console.log('🎨 Inicializando Análise Visual com dados:', dadosRelatorio);
        
        this.dadosOriginais = dadosRelatorio;
        this.filtroAtivo = $('#selectTipoReceita').val() || 'todas';
        
        // Criar container se não existir
        if ($('#analiseVisualContainer').length === 0) {
            $('#relatorioContainer').after(`
                <div id="analiseVisualContainer" class="mt-4">
                    ${this.criarHTML()}
                </div>
            `);
        }
        
        // Processar dados
        const dadosProcessados = this.processarDados(dadosRelatorio);
        
        // Criar gráficos
        setTimeout(() => {
            this.criarGraficoCategorias(dadosProcessados);
            this.criarGraficoOrigens(dadosProcessados);
            this.criarGraficoComparativo(dadosProcessados);
            this.criarGraficoEvolucao(dadosProcessados);
        }, 100);
    }

    /**
     * Cria o HTML do componente
     */
    criarHTML() {
        return `
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h5 class="mb-0">
                                <i class="bi bi-graph-up"></i> Análise Visual das Receitas
                            </h5>
                            <small>Distribuição por categorias e origens</small>
                        </div>
                        <div class="col-md-4 text-end">
                            <button class="btn btn-light btn-sm" onclick="analiseVisual.exportarGraficos()">
                                <i class="bi bi-download"></i> Exportar Gráficos
                            </button>
                        </div>
                    </div>
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
                    
                    <div class="tab-content mt-3" id="graficosTabContent">
                        <div class="tab-pane fade show active" id="categorias" role="tabpanel">
                            <div class="row">
                                <div class="col-md-8">
                                    <div style="position: relative; height: 400px;">
                                        <canvas id="chartCategorias"></canvas>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div id="legendaCategorias" class="mt-3"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="tab-pane fade" id="origens" role="tabpanel">
                            <div class="row">
                                <div class="col-md-8">
                                    <div style="position: relative; height: 400px;">
                                        <canvas id="chartOrigens"></canvas>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div id="legendaOrigens" class="mt-3"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="tab-pane fade" id="comparativo" role="tabpanel">
                            <div style="position: relative; height: 400px;">
                                <canvas id="chartComparativo"></canvas>
                            </div>
                        </div>
                        
                        <div class="tab-pane fade" id="evolucao" role="tabpanel">
                            <div style="position: relative; height: 400px;">
                                <canvas id="chartEvolucao"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Processa os dados do relatório para os gráficos
     */
    processarDados(dadosRelatorio) {
        const dados = dadosRelatorio.dados;
        const resultado = {
            categorias: [],
            origens: [],
            comparativo: {
                labels: [],
                atual: [],
                anterior: []
            },
            evolucao: {
                previsaoInicial: [],
                previsaoAtualizada: [],
                realizado: []
            }
        };

        // Processar conforme o filtro ativo
        if (this.filtroAtivo === 'todas') {
            // Processar todas as categorias
            dados.forEach(item => {
                if (item.nivel === 0 && item.receita_atual > 0) {
                    resultado.categorias.push({
                        nome: item.descricao,
                        valor: item.receita_atual,
                        codigo: item.codigo
                    });
                    
                    // Dados para comparativo
                    resultado.comparativo.labels.push(item.descricao);
                    resultado.comparativo.atual.push(item.receita_atual);
                    resultado.comparativo.anterior.push(item.receita_anterior);
                    
                    // Dados para evolução
                    resultado.evolucao.previsaoInicial.push(item.previsao_inicial);
                    resultado.evolucao.previsaoAtualizada.push(item.previsao_atualizada);
                    resultado.evolucao.realizado.push(item.receita_atual);
                }
                
                // Origens (fontes)
                if (item.nivel === 1 && item.receita_atual > 0) {
                    resultado.origens.push({
                        nome: item.descricao,
                        valor: item.receita_atual,
                        codigo: item.codigo,
                        categoria: item.categoria_pai
                    });
                }
            });
        } else {
            // Aplicar filtro específico
            const fontesPermitidas = this.obterFontesDoFiltro(this.filtroAtivo);
            const categoriasProcessadas = new Set();
            const totaisPorCategoria = {};
            
            dados.forEach(item => {
                if (item.nivel === 1 && fontesPermitidas.includes(item.codigo)) {
                    // Adicionar origem
                    if (item.receita_atual > 0) {
                        resultado.origens.push({
                            nome: item.descricao,
                            valor: item.receita_atual,
                            codigo: item.codigo,
                            categoria: item.categoria_pai
                        });
                        
                        // Acumular totais por categoria
                        const catId = item.categoria_pai;
                        if (!totaisPorCategoria[catId]) {
                            totaisPorCategoria[catId] = {
                                nome: '',
                                receita_atual: 0,
                                receita_anterior: 0,
                                previsao_inicial: 0,
                                previsao_atualizada: 0
                            };
                        }
                        
                        totaisPorCategoria[catId].receita_atual += item.receita_atual;
                        totaisPorCategoria[catId].receita_anterior += item.receita_anterior;
                        totaisPorCategoria[catId].previsao_inicial += item.previsao_inicial;
                        totaisPorCategoria[catId].previsao_atualizada += item.previsao_atualizada;
                        
                        categoriasProcessadas.add(catId);
                    }
                }
            });
            
            // Preencher nomes das categorias
            dados.forEach(item => {
                if (item.nivel === 0 && totaisPorCategoria[item.codigo]) {
                    totaisPorCategoria[item.codigo].nome = item.descricao;
                }
            });
            
            // Converter para array
            Object.keys(totaisPorCategoria).forEach(catId => {
                const cat = totaisPorCategoria[catId];
                if (cat.receita_atual > 0) {
                    resultado.categorias.push({
                        nome: cat.nome,
                        valor: cat.receita_atual,
                        codigo: catId
                    });
                    
                    resultado.comparativo.labels.push(cat.nome);
                    resultado.comparativo.atual.push(cat.receita_atual);
                    resultado.comparativo.anterior.push(cat.receita_anterior);
                    
                    resultado.evolucao.previsaoInicial.push(cat.previsao_inicial);
                    resultado.evolucao.previsaoAtualizada.push(cat.previsao_atualizada);
                    resultado.evolucao.realizado.push(cat.receita_atual);
                }
            });
        }
        
        return resultado;
    }

    /**
     * Obtém as fontes permitidas para um filtro específico
     */
    obterFontesDoFiltro(filtro) {
        const mapeamento = {
            '11': ['11', '71'],
            '12': ['12', '72'],
            '13': ['13', '73'],
            '14': ['14', '74'],
            '15': ['15', '75'],
            '16': ['16', '76'],
            '17': ['17', '77'],
            '19': ['19', '79'],
            '21': ['21'],
            '22': ['22'],
            '23': ['23'],
            '24': ['24']
        };
        
        return mapeamento[filtro] || [];
    }

    /**
     * Cria gráfico de pizza por categorias
     */
    criarGraficoCategorias(dados) {
        const ctx = document.getElementById('chartCategorias');
        if (!ctx) return;
        
        // Destruir gráfico anterior se existir
        if (this.charts.categorias) {
            this.charts.categorias.destroy();
        }
        
        const categoriasData = dados.categorias;
        
        this.charts.categorias = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: categoriasData.map(c => c.nome),
                datasets: [{
                    data: categoriasData.map(c => c.valor),
                    backgroundColor: this.cores.categorias.slice(0, categoriasData.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(2);
                                return `${context.label}: R$ ${this.formatarValor(value)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Criar legenda customizada
        this.criarLegendaCustomizada('legendaCategorias', categoriasData, 'categorias');
    }

    /**
     * Cria gráfico de pizza por origens
     */
    criarGraficoOrigens(dados) {
        const ctx = document.getElementById('chartOrigens');
        if (!ctx) return;
        
        // Destruir gráfico anterior se existir
        if (this.charts.origens) {
            this.charts.origens.destroy();
        }
        
        const origensData = dados.origens
            .sort((a, b) => b.valor - a.valor)
            .slice(0, 15); // Top 15 origens
        
        this.charts.origens = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: origensData.map(o => o.nome),
                datasets: [{
                    data: origensData.map(o => o.valor),
                    backgroundColor: this.cores.origens.slice(0, origensData.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(2);
                                return `${context.label}: R$ ${this.formatarValor(value)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Criar legenda customizada
        this.criarLegendaCustomizada('legendaOrigens', origensData, 'origens');
    }

    /**
     * Cria gráfico comparativo entre exercícios
     */
    criarGraficoComparativo(dados) {
        const ctx = document.getElementById('chartComparativo');
        if (!ctx) return;
        
        // Destruir gráfico anterior se existir
        if (this.charts.comparativo) {
            this.charts.comparativo.destroy();
        }
        
        this.charts.comparativo = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dados.comparativo.labels,
                datasets: [
                    {
                        label: `${this.dadosOriginais.periodo.ano}`,
                        data: dados.comparativo.atual,
                        backgroundColor: '#1e3c72',
                        borderColor: '#1e3c72',
                        borderWidth: 1
                    },
                    {
                        label: `${this.dadosOriginais.periodo.ano - 1}`,
                        data: dados.comparativo.anterior,
                        backgroundColor: '#4d7ea8',
                        borderColor: '#4d7ea8',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => 'R$ ' + this.formatarValor(value)
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `${context.dataset.label}: R$ ${this.formatarValor(context.parsed.y)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Cria gráfico de evolução da realização
     */
    criarGraficoEvolucao(dados) {
        const ctx = document.getElementById('chartEvolucao');
        if (!ctx) return;
        
        // Destruir gráfico anterior se existir
        if (this.charts.evolucao) {
            this.charts.evolucao.destroy();
        }
        
        this.charts.evolucao = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dados.comparativo.labels,
                datasets: [
                    {
                        label: 'Previsão Inicial',
                        data: dados.evolucao.previsaoInicial,
                        borderColor: '#ff9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.1)',
                        tension: 0.3
                    },
                    {
                        label: 'Previsão Atualizada',
                        data: dados.evolucao.previsaoAtualizada,
                        borderColor: '#4caf50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.3
                    },
                    {
                        label: 'Realizado',
                        data: dados.evolucao.realizado,
                        borderColor: '#2196f3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => 'R$ ' + this.formatarValor(value)
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `${context.dataset.label}: R$ ${this.formatarValor(context.parsed.y)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    /**
     * Cria legenda customizada para os gráficos de pizza
     */
    criarLegendaCustomizada(containerId, dados, tipo) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const total = dados.reduce((sum, item) => sum + item.valor, 0);
        let html = '<div class="custom-legend">';
        
        dados.forEach((item, index) => {
            const percentual = ((item.valor / total) * 100).toFixed(2);
            const cor = this.cores[tipo][index];
            
            html += `
                <div class="legend-item mb-2">
                    <div class="d-flex align-items-center">
                        <div class="legend-color" style="background-color: ${cor}; width: 20px; height: 20px; margin-right: 10px; border-radius: 3px;"></div>
                        <div class="flex-grow-1">
                            <div class="fw-bold">${item.nome}</div>
                            <small class="text-muted">R$ ${this.formatarValor(item.valor)} (${percentual}%)</small>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    /**
     * Formata valor monetário
     */
    formatarValor(valor) {
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(valor);
    }

    /**
     * Atualiza os gráficos quando o filtro muda
     */
    atualizarGraficos(dadosRelatorio) {
        this.filtroAtivo = $('#selectTipoReceita').val() || 'todas';
        const dadosProcessados = this.processarDados(dadosRelatorio);
        
        this.criarGraficoCategorias(dadosProcessados);
        this.criarGraficoOrigens(dadosProcessados);
        this.criarGraficoComparativo(dadosProcessados);
        this.criarGraficoEvolucao(dadosProcessados);
    }

    /**
     * Exporta todos os gráficos como imagens
     */
    exportarGraficos() {
        const graficos = ['categorias', 'origens', 'comparativo', 'evolucao'];
        
        graficos.forEach(nome => {
            if (this.charts[nome]) {
                const canvas = this.charts[nome].canvas;
                const url = canvas.toDataURL('image/png');
                const link = document.createElement('a');
                link.download = `grafico_${nome}_${new Date().getTime()}.png`;
                link.href = url;
                link.click();
            }
        });
        
        mostrarAlerta('Gráficos exportados com sucesso!', 'success');
    }

    /**
     * Destrói todos os gráficos
     */
    destruir() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = {};
    }
}

// Instanciar globalmente
const analiseVisual = new AnaliseVisualReceitas();