/**
 * Módulo de Relatório Receita/Fonte Integrado ao Balanço de Receitas
 * Aparece automaticamente após o Comparativo Mensal
 */

class RelatorioReceitaFonteIntegrado {
    constructor() {
        this.containerCreated = false;
        this.dadosOriginais = null;
        this.tipoAtual = 'fonte';
        this.dadosRelatorioFonte = null;
        this.dadosRelatorioReceita = null;
    }

    /**
     * Inicializa o módulo com os dados do relatório principal
     */
    inicializar(dadosRelatorio) {
        console.log('📋 Inicializando Relatório Receita/Fonte Integrado');
        
        // Criar container se não existir
        if (!this.containerCreated) {
            this.criarContainer();
            this.containerCreated = true;
        }
        
        // Armazenar dados originais
        this.dadosOriginais = dadosRelatorio;
        
        // Carregar dados do relatório
        this.carregarDados('fonte');
    }

    /**
     * Cria o container HTML para o relatório
     */
    criarContainer() {
        const html = `
            <div id="relatorioReceitaFonteContainer" class="mt-4">
                <div class="card shadow">
                    <div class="card-header bg-primary text-white">
                        <div class="row align-items-center">
                            <div class="col-md-7">
                                <h5 class="mb-0">
                                    <i class="bi bi-table"></i> Relatório Detalhado por Fonte/Receita
                                </h5>
                                <small>Análise detalhada da receita por código de fonte ou natureza da receita</small>
                            </div>
                            <div class="col-md-5 text-end">
                                <div class="btn-group btn-group-sm" role="group">
                                    <button type="button" class="btn btn-light active" id="btnPorFonte" 
                                            onclick="relatorioReceitaFonte.mudarTipoRelatorio('fonte')">
                                        Por Fonte
                                    </button>
                                    <button type="button" class="btn btn-light" id="btnPorReceita" 
                                            onclick="relatorioReceitaFonte.mudarTipoRelatorio('receita')">
                                        Por Receita
                                    </button>
                                </div>
                                <button class="btn btn-light btn-sm ms-2" onclick="relatorioReceitaFonte.exportarExcel()">
                                    <i class="bi bi-file-excel"></i> Excel
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="loadingRelatorioRF" class="text-center py-5" style="display: none;">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Carregando...</span>
                            </div>
                            <p class="mt-2 text-muted">Processando dados...</p>
                        </div>
                        
                        <div id="tabelaRelatorioRFContainer" style="display: none;">
                            <div class="table-responsive">
                                <table class="table table-hover table-sm" id="tabelaRelatorioRF">
                                    <thead class="table-light">
                                        <tr>
                                            <th class="col-descricao-rf">
                                                <span id="headerTipoRF">Código de Fonte</span>
                                            </th>
                                            <th class="text-end">Previsão Inicial</th>
                                            <th class="text-end">Previsão Atualizada</th>
                                            <th class="text-end">Realizada <span class="anoAtualRF"></span></th>
                                            <th class="text-end">Realizada <span class="anoAnteriorRF"></span></th>
                                            <th class="text-center">Variação</th>
                                        </tr>
                                    </thead>
                                    <tbody id="tbodyRelatorioRF">
                                        <!-- Dados serão inseridos aqui -->
                                    </tbody>
                                    <tfoot>
                                        <tr class="table-secondary fw-bold">
                                            <td>TOTAL GERAL</td>
                                            <td class="text-end" id="totalPrevisaoInicialRF">0,00</td>
                                            <td class="text-end" id="totalPrevisaoAtualizadaRF">0,00</td>
                                            <td class="text-end" id="totalReceitaAtualRF">0,00</td>
                                            <td class="text-end" id="totalReceitaAnteriorRF">0,00</td>
                                            <td class="text-center" id="totalVariacaoRF">0,00%</td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>
                        
                        <div id="emptyStateRF" class="text-center py-5" style="display: none;">
                            <i class="bi bi-inbox display-4 text-muted"></i>
                            <h5 class="mt-3 text-muted">Nenhum dado encontrado</h5>
                            <p class="text-muted">Não há dados para os filtros selecionados</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Inserir após o comparativo mensal ou análise visual
        if ($('#comparativoMensalContainer').length > 0) {
            $('#comparativoMensalContainer').after(html);
        } else if ($('#analiseVisualContainer').length > 0) {
            $('#analiseVisualContainer').after(html);
        } else {
            $('#relatorioContainer').after(html);
        }
    }

    /**
     * Carrega os dados do relatório
     */
    async carregarDados(tipo) {
        // Mostrar loading
        $('#loadingRelatorioRF').show();
        $('#tabelaRelatorioRFContainer').hide();
        $('#emptyStateRF').hide();
        
        try {
            // Verificar se já temos os dados em cache
            if (tipo === 'fonte' && this.dadosRelatorioFonte) {
                this.renderizarRelatorio(this.dadosRelatorioFonte);
                return;
            }
            if (tipo === 'receita' && this.dadosRelatorioReceita) {
                this.renderizarRelatorio(this.dadosRelatorioReceita);
                return;
            }
            
            // Buscar dados na API
            const params = new URLSearchParams({
                tipo: tipo,
                ano: this.dadosOriginais.periodo.ano,
                mes: this.dadosOriginais.periodo.mes,
                coug: this.dadosOriginais.filtros.coug || ''
            });
            
            const response = await fetch(`/balanco-receita/api/relatorio-receita-fonte?${params}`);
            
            if (!response.ok) {
                throw new Error('Erro ao carregar dados');
            }
            
            const dados = await response.json();
            
            // Armazenar em cache
            if (tipo === 'fonte') {
                this.dadosRelatorioFonte = dados;
            } else {
                this.dadosRelatorioReceita = dados;
            }
            
            // Renderizar
            this.renderizarRelatorio(dados);
            
        } catch (error) {
            console.error('Erro ao carregar relatório receita/fonte:', error);
            this.mostrarErro();
        }
    }

    /**
     * Renderiza o relatório na tabela
     */
    renderizarRelatorio(dados) {
        // Ocultar loading
        $('#loadingRelatorioRF').hide();
        
        // Verificar se há dados
        if (!dados || !dados.dados || dados.dados.length === 0) {
            $('#emptyStateRF').show();
            $('#tabelaRelatorioRFContainer').hide();
            return;
        }
        
        // Atualizar cabeçalho
        $('#headerTipoRF').text(dados.tipo === 'fonte' ? 'Código de Fonte' : 'Código de Receita (Alínea)');
        $('.anoAtualRF').text(dados.periodo.ano);
        $('.anoAnteriorRF').text(dados.periodo.ano - 1);
        
        // Renderizar dados
        const tbody = $('#tbodyRelatorioRF');
        tbody.empty();
        
        dados.dados.forEach(item => {
            const tr = this.criarLinhaTabela(item);
            tbody.append(tr);
        });
        
        // Atualizar totais
        if (dados.totais) {
            $('#totalPrevisaoInicialRF').text(this.formatarMoeda(dados.totais.previsao_inicial));
            $('#totalPrevisaoAtualizadaRF').text(this.formatarMoeda(dados.totais.previsao_atualizada));
            $('#totalReceitaAtualRF').text(this.formatarMoeda(dados.totais.receita_atual));
            $('#totalReceitaAnteriorRF').text(this.formatarMoeda(dados.totais.receita_anterior));
            
            const variacaoText = dados.totais.variacao_percentual >= 0 
                ? `↑ ${Math.abs(dados.totais.variacao_percentual).toFixed(2)}%`
                : `↓ ${Math.abs(dados.totais.variacao_percentual).toFixed(2)}%`;
            
            const variacaoClass = dados.totais.variacao_percentual >= 0 
                ? 'text-success' 
                : 'text-danger';
            
            $('#totalVariacaoRF')
                .text(variacaoText)
                .removeClass('text-success text-danger')
                .addClass(variacaoClass);
        }
        
        // Mostrar tabela
        $('#tabelaRelatorioRFContainer').show();
        $('#emptyStateRF').hide();
    }

    /**
     * Cria uma linha da tabela
     */
    criarLinhaTabela(item) {
        const paddingLeft = item.nivel * 25;
        const fontWeight = item.nivel === 0 ? 'fw-bold' : '';
        const bgClass = item.nivel === 0 ? 'table-light' : '';
        
        // Botão de expansão para itens com filhos
        let btnExpandir = '';
        if (item.tem_filhos) {
            btnExpandir = `
                <button class="btn btn-sm btn-link p-0 me-2 toggle-btn-rf" 
                        data-id="${item.id}" 
                        onclick="relatorioReceitaFonte.toggleItem('${item.id}')">
                    ▶
                </button>
            `;
        }
        
        // Calcular variação
        const variacaoIcone = item.variacao_percentual >= 0 ? '↑' : '↓';
        const variacaoClass = item.variacao_percentual >= 0 ? 'text-success' : 'text-danger';
        const variacaoText = `${variacaoIcone} ${Math.abs(item.variacao_percentual).toFixed(2)}%`;
        
        // Estilo de exibição inicial
        const displayStyle = item.nivel === 1 ? 'style="display: none;"' : '';
        
        const tr = `
            <tr class="${bgClass} ${fontWeight}" 
                data-id="${item.id}" 
                data-nivel="${item.nivel}"
                data-pai-id="${item.pai_id || ''}"
                ${displayStyle}>
                <td style="padding-left: ${paddingLeft}px;">
                    ${btnExpandir}
                    <span>${item.codigo} - ${item.descricao}</span>
                </td>
                <td class="text-end">${this.formatarMoeda(item.previsao_inicial)}</td>
                <td class="text-end">${this.formatarMoeda(item.previsao_atualizada)}</td>
                <td class="text-end">${this.formatarMoeda(item.receita_atual)}</td>
                <td class="text-end">${this.formatarMoeda(item.receita_anterior)}</td>
                <td class="text-center">
                    <span class="${variacaoClass}">${variacaoText}</span>
                </td>
            </tr>
        `;
        
        return tr;
    }

    /**
     * Alterna expansão/colapso de item
     */
    toggleItem(id) {
        const btn = $(`.toggle-btn-rf[data-id="${id}"]`);
        const isExpanded = btn.text() === '▼';
        
        if (isExpanded) {
            // Recolher
            btn.text('▶');
            $(`tr[data-pai-id="${id}"]`).hide();
        } else {
            // Expandir
            btn.text('▼');
            $(`tr[data-pai-id="${id}"]`).show();
        }
    }

    /**
     * Muda o tipo do relatório
     */
    mudarTipoRelatorio(tipo) {
        this.tipoAtual = tipo;
        
        // Atualizar botões
        if (tipo === 'fonte') {
            $('#btnPorFonte').addClass('active');
            $('#btnPorReceita').removeClass('active');
        } else {
            $('#btnPorFonte').removeClass('active');
            $('#btnPorReceita').addClass('active');
        }
        
        // Carregar dados
        this.carregarDados(tipo);
    }

    /**
     * Exporta para Excel
     */
    async exportarExcel() {
        try {
            const dados = this.tipoAtual === 'fonte' ? this.dadosRelatorioFonte : this.dadosRelatorioReceita;
            
            if (!dados || !dados.dados) {
                alert('Nenhum dado para exportar');
                return;
            }
            
            // Preparar dados para Excel
            const dadosExcel = [];
            
            // Cabeçalho
            dadosExcel.push([
                'Código',
                'Descrição',
                'Previsão Inicial',
                'Previsão Atualizada',
                `Realizada ${dados.periodo.ano}`,
                `Realizada ${dados.periodo.ano - 1}`,
                'Variação %'
            ]);
            
            // Dados
            dados.dados.forEach(item => {
                const indent = '  '.repeat(item.nivel);
                dadosExcel.push([
                    item.codigo,
                    indent + item.descricao,
                    item.previsao_inicial,
                    item.previsao_atualizada,
                    item.receita_atual,
                    item.receita_anterior,
                    item.variacao_percentual.toFixed(2)
                ]);
            });
            
            // Total
            if (dados.totais) {
                dadosExcel.push([
                    '',
                    'TOTAL GERAL',
                    dados.totais.previsao_inicial,
                    dados.totais.previsao_atualizada,
                    dados.totais.receita_atual,
                    dados.totais.receita_anterior,
                    dados.totais.variacao_percentual.toFixed(2)
                ]);
            }
            
            // Criar workbook
            const ws = XLSX.utils.aoa_to_sheet(dadosExcel);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, `Relatório por ${this.tipoAtual}`);
            
            // Download
            const filename = `relatorio_${this.tipoAtual}_${dados.periodo.ano}_${dados.periodo.mes}.xlsx`;
            XLSX.writeFile(wb, filename);
            
            // Mostrar mensagem de sucesso
            this.mostrarMensagem('Arquivo Excel gerado com sucesso!', 'success');
            
        } catch (error) {
            console.error('Erro ao exportar:', error);
            this.mostrarMensagem('Erro ao exportar dados', 'danger');
        }
    }

    /**
     * Formata valor monetário
     */
    formatarMoeda(valor) {
        if (!valor) return '0,00';
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(valor);
    }

    /**
     * Mostra mensagem de erro
     */
    mostrarErro() {
        $('#loadingRelatorioRF').hide();
        $('#tabelaRelatorioRFContainer').hide();
        $('#emptyStateRF').show();
    }

    /**
     * Mostra mensagem temporária
     */
    mostrarMensagem(texto, tipo = 'info') {
        const alert = `
            <div class="alert alert-${tipo} alert-dismissible fade show position-fixed top-0 end-0 m-3" 
                 style="z-index: 9999;" role="alert">
                ${texto}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('body').append(alert);
        
        // Auto remover após 3 segundos
        setTimeout(() => {
            $('.alert').fadeOut(() => {
                $('.alert').remove();
            });
        }, 3000);
    }

    /**
     * Atualiza quando o relatório principal é atualizado
     */
    atualizar(dadosRelatorio) {
        this.dadosOriginais = dadosRelatorio;
        this.dadosRelatorioFonte = null;
        this.dadosRelatorioReceita = null;
        this.carregarDados(this.tipoAtual);
    }

    /**
     * Destrói o módulo
     */
    destruir() {
        $('#relatorioReceitaFonteContainer').remove();
        this.containerCreated = false;
        this.dadosRelatorioFonte = null;
        this.dadosRelatorioReceita = null;
    }
}

// Instanciar globalmente
const relatorioReceitaFonte = new RelatorioReceitaFonteIntegrado();