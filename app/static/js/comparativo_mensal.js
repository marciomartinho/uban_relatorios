/**
 * Módulo de Comparativo Mensal Acumulado de Receitas
 * Responsável pela criação e atualização do gráfico comparativo
 */

class ComparativoMensalAcumulado {
    constructor() {
        this.charts = {};
        this.chartVariacao = null;
        this.dadosOriginais = null;
        this.containerCreated = false;
    }

    /**
     * Inicializa o módulo com os dados do relatório
     */
    inicializar(dadosRelatorio) {
        console.log('📊 Inicializando Comparativo Mensal Acumulado');
        
        // Criar container se não existir
        if (!this.containerCreated) {
            this.criarContainer();
            this.containerCreated = true;
        }
        
        // Carregar dados do comparativo
        this.carregarDados(dadosRelatorio);
    }

    /**
     * Cria o container HTML para o comparativo
     */
    criarContainer() {
        const html = `
            <div id="comparativoMensalContainer" class="mt-4">
                <div class="card shadow">
                    <div class="card-header bg-info text-white">
                        <div class="row align-items-center">
                            <div class="col-md-8">
                                <h5 class="mb-0">
                                    <i class="bi bi-calendar-check"></i> Comparativo Mensal Acumulado
                                </h5>
                                <small>Evolução acumulada das receitas mês a mês</small>
                            </div>
                            <div class="col-md-4 text-end">
                                <button class="btn btn-light btn-sm" onclick="comparativoMensal.alternarVisualizacao()">
                                    <i class="bi bi-table"></i> Ver Tabela
                                </button>
                                <button class="btn btn-light btn-sm" onclick="comparativoMensal.exportarDados()">
                                    <i class="bi bi-download"></i> Exportar
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <!-- Abas para alternar entre gráfico e tabela -->
                        <ul class="nav nav-tabs" id="comparativoTab" role="tablist">
                            <li class="nav-item" role="presentation">
                                <button class="nav-link active" id="tabela-tab" data-bs-toggle="tab" 
                                        data-bs-target="#tabela-content" type="button" role="tab">
                                    <i class="bi bi-table"></i> Tabela Detalhada
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="analise-tab" data-bs-toggle="tab" 
                                        data-bs-target="#analise-content" type="button" role="tab">
                                    <i class="bi bi-bar-chart"></i> Análise de Variação
                                </button>
                            </li>
                            <li class="nav-item" role="presentation">
                                <button class="nav-link" id="grafico-tab" data-bs-toggle="tab" 
                                        data-bs-target="#grafico-content" type="button" role="tab">
                                    <i class="bi bi-graph-up"></i> Gráfico
                                </button>
                            </li>
                        </ul>
                        
                        <div class="tab-content mt-3" id="comparativoTabContent">
                            <!-- Aba da Tabela -->
                            <div class="tab-pane fade show active" id="tabela-content" role="tabpanel">
                                <div class="table-responsive">
                                    <table class="table table-hover" id="tabelaComparativo">
                                        <thead class="table-light">
                                            <tr>
                                                <th>Mês</th>
                                                <th class="text-end">Receita <span class="ano-anterior"></span></th>
                                                <th class="text-end">Receita <span class="ano-atual"></span></th>
                                                <th class="text-end">Variação R$</th>
                                                <th class="text-center">Variação %</th>
                                            </tr>
                                        </thead>
                                        <tbody id="tabelaComparativoBody">
                                            <!-- Dados serão inseridos aqui -->
                                        </tbody>
                                        <tfoot class="table-light fw-bold">
                                            <tr id="totalRow">
                                                <!-- Totais serão inseridos aqui -->
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>
                            </div>
                            
                            <!-- Aba de Análise -->
                            <div class="tab-pane fade" id="analise-content" role="tabpanel">
                                <div class="row">
                                    <div class="col-md-6">
                                        <canvas id="chartVariacaoMensal"></canvas>
                                    </div>
                                    <div class="col-md-6">
                                        <div id="analiseDetalhada">
                                            <!-- Análise detalhada será inserida aqui -->
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Aba do Gráfico -->
                            <div class="tab-pane fade" id="grafico-content" role="tabpanel">
                                <div id="graficoLoading" class="text-center py-5">
                                    <div class="spinner-border text-info" role="status">
                                        <span class="visually-hidden">Carregando...</span>
                                    </div>
                                </div>
                                <div style="position: relative; height: 400px;">
                                    <canvas id="chartComparativoMensal" style="display: none;"></canvas>
                                </div>
                                <div id="legendaComparativo" class="mt-3"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Inserir após o container de análise visual (se existir) ou após o relatório
        if ($('#analiseVisualContainer').length > 0) {
            $('#analiseVisualContainer').after(html);
        } else {
            $('#relatorioContainer').after(html);
        }
    }

    /**
     * Carrega os dados do comparativo mensal
     */
    async carregarDados(dadosRelatorio) {
        try {
            // Obter filtros do relatório atual
            const filtros = {
                ano: dadosRelatorio.periodo.ano,
                coug: dadosRelatorio.filtros.coug || '',
                tipo_receita: $('#selectTipoReceita').val() || 'todas'
            };
            
            // Fazer requisição para API
            const response = await fetch(`/comparativo-mensal/api/comparativo-mensal?ano=${filtros.ano}&coug=${filtros.coug}&tipo_receita=${filtros.tipo_receita}`);
            
            if (!response.ok) {
                throw new Error('Erro ao carregar dados do comparativo');
            }
            
            const data = await response.json();
            this.dadosOriginais = data;
            
            // Renderizar visualizações
            this.renderizarGrafico(data.dados_grafico);
            this.renderizarTabela(data.dados_html);
            this.renderizarAnalise(data.dados_brutos);
            
            // Ocultar loading
            $('#graficoLoading').hide();
            $('#chartComparativoMensal').show();
            
        } catch (error) {
            console.error('Erro ao carregar comparativo mensal:', error);
            this.mostrarErro('Erro ao carregar dados do comparativo mensal');
        }
    }

    /**
     * Renderiza o gráfico principal
     */
    renderizarGrafico(dadosGrafico) {
        const ctx = document.getElementById('chartComparativoMensal');
        if (!ctx) return;
        
        // Destruir gráfico anterior se existir
        if (this.charts.principal) {
            this.charts.principal.destroy();
        }
        
        // Verificar se há dados
        if (!dadosGrafico.labels || dadosGrafico.labels.length === 0) {
            $('#graficoLoading').html(`
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i> 
                    Sem dados para exibir o gráfico
                </div>
            `);
            return;
        }
        
        // Configuração do gráfico
        this.charts.principal = new Chart(ctx, {
            type: 'line',
            data: dadosGrafico,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Evolução Acumulada das Receitas',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const label = context.dataset.label || '';
                                const value = this.formatarMoeda(context.parsed.y);
                                
                                // Adicionar variação percentual se for o ano atual
                                if (context.datasetIndex === 1 && dadosGrafico.variacoes) {
                                    const variacao = dadosGrafico.variacoes[context.dataIndex];
                                    const sinal = variacao >= 0 ? '+' : '';
                                    return `${label}: ${value} (${sinal}${variacao.toFixed(2)}%)`;
                                }
                                
                                return `${label}: ${value}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => this.formatarMoedaCurto(value)
                        }
                    }
                }
            }
        });
        
        // Ocultar loading e mostrar gráfico
        $('#graficoLoading').hide();
        $('#chartComparativoMensal').show();
        
        // Criar legenda informativa
        this.criarLegendaInformativa();
    }

    /**
     * Renderiza a tabela detalhada
     */
    renderizarTabela(dadosHtml) {
        if (!dadosHtml.tem_dados) {
            $('#tabelaComparativoBody').html('<tr><td colspan="5" class="text-center">Sem dados para exibir</td></tr>');
            return;
        }
        
        const tbody = $('#tabelaComparativoBody');
        tbody.empty();
        
        // Preencher anos nos cabeçalhos
        if (dadosHtml.meses.length > 0) {
            $('.ano-anterior').text(dadosHtml.meses[0].ano_anterior);
            $('.ano-atual').text(dadosHtml.meses[0].ano_atual);
        }
        
        // Variáveis para totais
        let totalAnterior = 0;
        let totalAtual = 0;
        
        // Adicionar linhas
        dadosHtml.meses.forEach((mes, index) => {
            const variacaoIcone = mes.variacao_percentual >= 0 ? '↑' : '↓';
            const row = `
                <tr>
                    <td>${mes.label_ate}</td>
                    <td class="text-end">${mes.receita_anterior_formatada}</td>
                    <td class="text-end">${mes.receita_atual_formatada}</td>
                    <td class="text-end">${mes.variacao_absoluta_formatada}</td>
                    <td class="text-center">
                        <span class="${mes.variacao_classe}">
                            ${mes.variacao_formatada}
                        </span>
                    </td>
                </tr>
            `;
            tbody.append(row);
            
            // Acumular totais (pegar o último mês que já é acumulado)
            if (index === dadosHtml.meses.length - 1) {
                totalAnterior = this.dadosOriginais.dados_brutos[index].receita_anterior;
                totalAtual = this.dadosOriginais.dados_brutos[index].receita_atual;
            }
        });
        
        // Adicionar linha de total
        const variacaoTotal = totalAnterior !== 0 
            ? ((totalAtual - totalAnterior) / Math.abs(totalAnterior) * 100).toFixed(2)
            : (totalAtual !== 0 ? 100 : 0);
        
        const totalRow = `
            <td>TOTAL ACUMULADO</td>
            <td class="text-end">${this.formatarMoeda(totalAnterior)}</td>
            <td class="text-end">${this.formatarMoeda(totalAtual)}</td>
            <td class="text-end">${this.formatarMoeda(Math.abs(totalAtual - totalAnterior))}</td>
            <td class="text-center ${variacaoTotal >= 0 ? 'text-success' : 'text-danger'}">
                ${variacaoTotal >= 0 ? '↑' : '↓'} ${Math.abs(variacaoTotal)}%
            </td>
        `;
        $('#totalRow').html(totalRow);
    }

    /**
     * Renderiza a análise de variação
     */
    renderizarAnalise(dadosBrutos) {
        if (!dadosBrutos || dadosBrutos.length === 0) return;
        
        // Criar gráfico de barras com variações mensais
        this.criarGraficoVariacao(dadosBrutos);
        
        // Criar análise detalhada
        this.criarAnaliseDetalhada(dadosBrutos);
    }

    /**
     * Cria gráfico de variação mensal
     */
    criarGraficoVariacao(dados) {
        const ctx = document.getElementById('chartVariacaoMensal');
        if (!ctx) return;
        
        // Destruir gráfico anterior se existir
        if (this.chartVariacao) {
            this.chartVariacao.destroy();
        }
        
        const labels = dados.map(d => d.nome_mes);
        const variacoes = dados.map(d => d.variacao_percentual);
        const cores = variacoes.map(v => v >= 0 ? 'rgba(40, 167, 69, 0.8)' : 'rgba(220, 53, 69, 0.8)');
        
        this.chartVariacao = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Variação %',
                    data: variacoes,
                    backgroundColor: cores,
                    borderColor: cores,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Variação Percentual Mensal'
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => value + '%'
                        }
                    }
                }
            }
        });
    }

    /**
     * Cria análise detalhada
     */
    criarAnaliseDetalhada(dados) {
        const container = $('#analiseDetalhada');
        
        // Calcular estatísticas
        const variacoes = dados.map(d => d.variacao_percentual);
        const mediaVariacao = variacoes.reduce((a, b) => a + b, 0) / variacoes.length;
        const maxVariacao = Math.max(...variacoes);
        const minVariacao = Math.min(...variacoes);
        const mesesPositivos = variacoes.filter(v => v > 0).length;
        const mesesNegativos = variacoes.filter(v => v < 0).length;
        const mesesNeutros = variacoes.filter(v => v === 0).length;
        
        // Encontrar meses com maior/menor variação
        const mesMaxVariacao = dados.find(d => d.variacao_percentual === maxVariacao);
        const mesMinVariacao = dados.find(d => d.variacao_percentual === minVariacao);
        
        // Determinar os labels corretos
        let labelMaior = 'Mês de Maior Crescimento:';
        let labelMenor = 'Mês de Menor Crescimento:';
        
        // Se o menor valor for negativo, ajustar o label
        if (minVariacao < 0) {
            labelMenor = 'Mês de Maior Redução:';
        }
        
        const html = `
            <div class="card">
                <div class="card-header bg-light">
                    <h6 class="mb-0">Análise Estatística</h6>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <strong>Variação Média:</strong> 
                        <span class="${mediaVariacao >= 0 ? 'text-success' : 'text-danger'}">
                            ${mediaVariacao >= 0 ? '↑' : '↓'} ${Math.abs(mediaVariacao).toFixed(2)}%
                        </span>
                    </div>
                    
                    <div class="mb-3">
                        <strong>${labelMaior}</strong><br>
                        ${mesMaxVariacao.nome_mes}: 
                        <span class="text-success">↑ ${maxVariacao.toFixed(2)}%</span>
                    </div>
                    
                    <div class="mb-3">
                        <strong>${labelMenor}</strong><br>
                        ${mesMinVariacao.nome_mes}: 
                        <span class="${minVariacao >= 0 ? 'text-success' : 'text-danger'}">
                            ${minVariacao >= 0 ? '↑' : '↓'} ${Math.abs(minVariacao).toFixed(2)}%
                        </span>
                    </div>
                    
                    <div class="progress mb-3" style="height: 25px;">
                        ${mesesPositivos > 0 ? `
                        <div class="progress-bar bg-success" role="progressbar" 
                             style="width: ${(mesesPositivos / dados.length * 100)}%">
                            ${mesesPositivos} ${mesesPositivos === 1 ? 'mês' : 'meses'} ↑
                        </div>` : ''}
                        ${mesesNegativos > 0 ? `
                        <div class="progress-bar bg-danger" role="progressbar" 
                             style="width: ${(mesesNegativos / dados.length * 100)}%">
                            ${mesesNegativos} ${mesesNegativos === 1 ? 'mês' : 'meses'} ↓
                        </div>` : ''}
                        ${mesesNeutros > 0 ? `
                        <div class="progress-bar bg-secondary" role="progressbar" 
                             style="width: ${(mesesNeutros / dados.length * 100)}%">
                            ${mesesNeutros} ${mesesNeutros === 1 ? 'mês' : 'meses'} →
                        </div>` : ''}
                    </div>
                    
                    <div class="alert alert-info mb-0">
                        <small>
                            <i class="bi bi-info-circle"></i> 
                            Análise baseada em ${dados.length} meses de dados acumulados
                        </small>
                    </div>
                </div>
            </div>
        `;
        
        container.html(html);
    }

    /**
     * Cria legenda informativa abaixo do gráfico
     */
    criarLegendaInformativa() {
        if (!this.dadosOriginais) return;
        
        const container = $('#legendaComparativo');
        const ultimoMes = this.dadosOriginais.dados_brutos[this.dadosOriginais.dados_brutos.length - 1];
        
        if (ultimoMes) {
            const html = `
                <div class="row mt-3">
                    <div class="col-md-4 text-center">
                        <div class="card bg-light">
                            <div class="card-body py-2">
                                <h6 class="mb-1">Total ${ultimoMes.ano_anterior}</h6>
                                <p class="mb-0 fw-bold">${this.formatarMoeda(ultimoMes.receita_anterior)}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="card bg-light">
                            <div class="card-body py-2">
                                <h6 class="mb-1">Total ${ultimoMes.ano_atual}</h6>
                                <p class="mb-0 fw-bold">${this.formatarMoeda(ultimoMes.receita_atual)}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 text-center">
                        <div class="card ${ultimoMes.variacao_percentual >= 0 ? 'bg-success' : 'bg-danger'} text-white">
                            <div class="card-body py-2">
                                <h6 class="mb-1">Variação Total</h6>
                                <p class="mb-0 fw-bold">
                                    ${ultimoMes.variacao_percentual >= 0 ? '↑' : '↓'} 
                                    ${Math.abs(ultimoMes.variacao_percentual).toFixed(2)}%
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            container.html(html);
        }
    }

    /**
     * Alterna entre visualização de gráfico e tabela
     */
    alternarVisualizacao() {
        const tabelaTab = document.getElementById('tabela-tab');
        if (tabelaTab) {
            tabelaTab.click();
        }
    }

    /**
     * Exporta os dados do comparativo
     */
    async exportarDados() {
        try {
            // Criar dados para exportação
            const dadosExport = this.dadosOriginais.dados_brutos.map(item => ({
                'Mês': item.nome_mes,
                [`Receita ${item.ano_anterior}`]: item.receita_anterior,
                [`Receita ${item.ano_atual}`]: item.receita_atual,
                'Variação R$': item.variacao_absoluta,
                'Variação %': item.variacao_percentual.toFixed(2) + '%'
            }));
            
            // Criar worksheet
            const ws = XLSX.utils.json_to_sheet(dadosExport);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'Comparativo Mensal');
            
            // Baixar arquivo
            XLSX.writeFile(wb, `comparativo_mensal_${new Date().getTime()}.xlsx`);
            
            mostrarAlerta('Dados exportados com sucesso!', 'success');
        } catch (error) {
            console.error('Erro ao exportar dados:', error);
            mostrarAlerta('Erro ao exportar dados', 'danger');
        }
    }

    /**
     * Formata valor monetário
     */
    formatarMoeda(valor) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    }

    /**
     * Formata valor monetário de forma curta (K, M, B)
     */
    formatarMoedaCurto(valor) {
        if (valor >= 1e9) {
            return 'R$ ' + (valor / 1e9).toFixed(1) + 'B';
        } else if (valor >= 1e6) {
            return 'R$ ' + (valor / 1e6).toFixed(1) + 'M';
        } else if (valor >= 1e3) {
            return 'R$ ' + (valor / 1e3).toFixed(1) + 'K';
        }
        return this.formatarMoeda(valor);
    }

    /**
     * Mostra mensagem de erro
     */
    mostrarErro(mensagem) {
        const html = `
            <div class="alert alert-danger text-center">
                <i class="bi bi-exclamation-triangle"></i> ${mensagem}
            </div>
        `;
        $('#graficoLoading').html(html);
    }

    /**
     * Atualiza o comparativo quando o relatório é atualizado
     */
    atualizar(dadosRelatorio) {
        this.carregarDados(dadosRelatorio);
    }

    /**
     * Destrói os gráficos
     */
    destruir() {
        if (this.charts.principal) {
            this.charts.principal.destroy();
            this.charts.principal = null;
        }
        if (this.chartVariacao) {
            this.chartVariacao.destroy();
            this.chartVariacao = null;
        }
    }
}

// Instanciar globalmente
const comparativoMensal = new ComparativoMensalAcumulado();