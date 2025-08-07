/**
 * Módulo de Renderização
 * Responsável por toda a renderização de UI e tabelas
 */

class RenderizadorBalancoReceita {
    constructor() {
        this.config = window.ConfiguracoesBalancoReceita;
        this.formatadores = window.FormatadoresBalancoReceita;
        this.seletores = this.config.SELETORES;
    }
    
    /**
     * Renderiza tela de loading
     */
    renderizarLoading() {
        const html = `
            <div class="loading-container">
                <i class="bi bi-hourglass-split"></i>
                <h4 class="mt-3">Gerando relatório...</h4>
                <p class="text-muted">Consultando dados no DuckDB</p>
            </div>
        `;
        
        $(this.seletores.MENSAGEM_INICIAL).hide();
        $(this.seletores.CONTAINER_RELATORIO).html(html).show();
    }
    
    /**
     * Renderiza mensagem de erro
     * @param {string} mensagem - Mensagem de erro
     */
    renderizarErro(mensagem) {
        const html = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i> ${mensagem}
            </div>
        `;
        $(this.seletores.CONTAINER_RELATORIO).html(html);
    }
    
    /**
     * Renderiza o relatório completo
     * @param {Object} dados - Dados do relatório
     */
    renderizarRelatorio(dados) {
        const html = this._construirRelatorio(dados);
        $(this.seletores.CONTAINER_RELATORIO).html(html);
    }
    
    /**
     * Constrói o HTML do relatório
     * @private
     */
    _construirRelatorio(dados) {
        let html = `
            <div class="card">
                ${this._construirCabecalho(dados)}
                <div class="card-body">
        `;
        
        if (!dados.dados || dados.dados.length === 0) {
            html += this._construirMensagemVazia();
        } else {
            html += this._construirTabela(dados);
        }
        
        html += `
                </div>
                ${this._construirRodape(dados)}
            </div>
        `;
        
        return html;
    }
    
    /**
     * Constrói o cabeçalho do relatório
     * @private
     */
    _construirCabecalho(dados) {
        return `
            <div class="card-header bg-light">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h5 class="mb-0">
                            <i class="bi bi-file-earmark-bar-graph"></i> 
                            Balanço Orçamentário - ${dados.periodo.nome_mes}/${dados.periodo.ano}
                        </h5>
                        <small class="text-muted">UG: ${dados.filtros.nome_coug}</small>
                    </div>
                    <div class="col-md-4 text-end">
                        <button id="btnExportar" class="btn btn-success btn-sm">
                            <i class="bi bi-file-earmark-excel"></i> Excel
                        </button>
                        <button id="btnExportarCompleto" class="btn btn-primary btn-sm">
                            <i class="bi bi-file-earmark-spreadsheet"></i> Completo
                        </button>
                        <button id="btnDownloadImagem" class="btn btn-warning btn-sm">
                            <i class="bi bi-image"></i> Imagem HD
                        </button>
                        <button id="btnImprimir" class="btn btn-secondary btn-sm">
                            <i class="bi bi-printer"></i> Imprimir
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    /**
     * Constrói mensagem quando não há dados
     * @private
     */
    _construirMensagemVazia() {
        return `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle"></i> 
                Nenhum dado encontrado para os filtros selecionados.
            </div>
        `;
    }
    
    /**
     * Constrói a tabela principal
     * @private
     */
    _construirTabela(dados) {
        let html = `
            <div class="table-responsive">
                <table class="table table-bordered table-hover" id="tabelaBalanco">
                    ${this._construirCabecalhoTabela(dados)}
                    <tbody>
        `;
        
        // Adicionar linhas de dados
        dados.dados.forEach(item => {
            html += this._construirLinhaTabela(item);
        });
        
        // Adicionar linha de total
        html += this._construirLinhaTotais(dados.totais);
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        return html;
    }
    
    /**
     * Constrói o cabeçalho da tabela
     * @private
     */
    _construirCabecalhoTabela(dados) {
        return `
            <thead class="table-primary">
                <tr>
                    <th class="text-center align-middle" style="min-width: 400px;">RECEITAS</th>
                    <th class="text-center">PREVISÃO INICIAL<br>${dados.periodo.ano}</th>
                    <th class="text-center">PREVISÃO ATUALIZADA<br>${dados.periodo.ano}</th>
                    <th class="text-center">REALIZADA<br>${dados.periodo.mes}/${dados.periodo.ano}</th>
                    <th class="text-center">REALIZADA<br>${dados.periodo.mes}/${dados.periodo.ano_anterior}</th>
                    <th class="text-center">VARIAÇÃO<br>ABSOLUTA</th>
                    <th class="text-center">VARIAÇÃO<br>%</th>
                </tr>
            </thead>
        `;
    }
    
    /**
     * Constrói uma linha da tabela
     * @private
     */
    _construirLinhaTabela(item) {
        const classeNivel = `nivel-${item.nivel}`;
        const classeLinha = this._obterClasseLinha(item);
        const paddingLeft = this._calcularPadding(item);
        const estiloLinha = this._obterEstiloVisibilidade(item);
        const classesHierarquia = this._obterClassesHierarquia(item);
        
        let html = `
            <tr class="${classeLinha} ${classesHierarquia}" 
                data-id="${item.id}" 
                data-nivel="${item.nivel}"
                ${estiloLinha}>
                <td style="padding-left: ${paddingLeft}px;">
        `;
        
        // Adicionar botão de expansão se necessário
        html += this._construirBotaoExpansao(item);
        
        // Adicionar ícone especial para UGs
        if (item.nivel === 4) {
            html += `<i class="bi bi-building text-primary me-2"></i>`;
        }
        
        html += `<span>${item.descricao}</span>`;
        
        // Adicionar botão de lançamentos para UGs (nível 4)
        if (item.nivel === 4) {
            html += `
                <button class="btn btn-sm btn-outline-primary ms-2 btn-lancamentos" 
                        data-ug="${item.codigo}"
                        data-fonte="${item.fonte_pai}"
                        data-subfonte="${item.subfonte_pai}"
                        data-alinea="${item.alinea_pai}"
                        title="Ver lançamentos">
                    <i class="bi bi-list-ul"></i> Lançamentos
                </button>
            `;
        }
        
        html += `</td>
                <td class="text-end">${this.formatadores.formatarValor(item.previsao_inicial)}</td>
                <td class="text-end">${this.formatadores.formatarValor(item.previsao_atualizada)}</td>
                <td class="text-end">${this.formatadores.formatarValor(item.receita_atual)}</td>
                <td class="text-end">${this.formatadores.formatarValor(item.receita_anterior)}</td>
                <td class="text-end ${this.formatadores.obterClasseVariacao(item.variacao_absoluta)}">
                    ${this.formatadores.formatarValor(item.variacao_absoluta)}
                </td>
                <td class="text-center ${this.formatadores.obterClasseVariacao(item.variacao_percentual)}">
                    ${this.formatadores.formatarPercentual(item.variacao_percentual)}
                </td>
            </tr>
        `;
        
        return html;
    }
    
    /**
     * Constrói linha de totais
     * @private
     */
    _construirLinhaTotais(totais) {
        return `
            <tr class="table-dark fw-bold">
                <td>TOTAL GERAL</td>
                <td class="text-end">${this.formatadores.formatarValor(totais.previsao_inicial)}</td>
                <td class="text-end">${this.formatadores.formatarValor(totais.previsao_atualizada)}</td>
                <td class="text-end">${this.formatadores.formatarValor(totais.receita_atual)}</td>
                <td class="text-end">${this.formatadores.formatarValor(totais.receita_anterior)}</td>
                <td class="text-end ${this.formatadores.obterClasseVariacao(totais.variacao_absoluta)}">
                    ${this.formatadores.formatarValor(totais.variacao_absoluta)}
                </td>
                <td class="text-center ${this.formatadores.obterClasseVariacao(totais.variacao_percentual)}">
                    ${this.formatadores.formatarPercentual(totais.variacao_percentual)}
                </td>
            </tr>
        `;
    }
    
    /**
     * Constrói o rodapé do relatório
     * @private
     */
    _construirRodape(dados) {
        return `
            <div class="card-footer text-muted text-center">
                <small>Gerado em: ${dados.data_geracao}</small>
            </div>
        `;
    }
    
    /**
     * Obtém classe CSS para a linha baseada no nível
     * @private
     */
    _obterClasseLinha(item) {
        const classes = this.config.CLASSES.NIVEIS;
        return `nivel-${item.nivel} ${classes[item.nivel] || ''}`;
    }
    
    /**
     * Calcula padding da célula baseado no nível
     * @private
     */
    _calcularPadding(item) {
        let padding = item.nivel * this.config.RENDERIZACAO.PADDING_POR_NIVEL;
        if (item.nivel === 4) {
            padding += this.config.RENDERIZACAO.PADDING_EXTRA_UG;
        }
        return padding;
    }
    
    /**
     * Obtém estilo de visibilidade inicial
     * @private
     */
    _obterEstiloVisibilidade(item) {
        if (item.nivel === 0 || item.nivel === 1) {
            return '';
        }
        return 'style="display: none;"';
    }
    
    /**
     * Obtém classes de hierarquia para a linha
     * @private
     */
    _obterClassesHierarquia(item) {
        let classes = `nivel-${item.nivel}`;
        
        if (item.nivel === 1) {
            classes += ` filho-de-cat-${item.categoria_pai}`;
        } else if (item.nivel === 2) {
            classes += ` filho-de-fonte-${item.categoria_pai}-${item.fonte_pai}`;
        } else if (item.nivel === 3) {
            classes += ` filho-de-subfonte-${item.categoria_pai}-${item.fonte_pai}-${item.subfonte_pai}`;
        } else if (item.nivel === 4) {
            classes += ` filho-de-alinea-${item.categoria_pai}-${item.fonte_pai}-${item.subfonte_pai}-${item.alinea_pai}`;
        }
        
        return classes;
    }
    
    /**
     * Constrói botão de expansão se necessário
     * @private
     */
    _construirBotaoExpansao(item) {
        if ((item.nivel === 1 || item.nivel === 2 || item.nivel === 3) && item.tem_filhos) {
            return `<button class="btn btn-sm btn-link toggle-btn" data-nivel="${item.nivel}" data-id="${item.id}">+</button> `;
        } else if (item.nivel > 0) {
            return `<span style="display: inline-block; width: 30px;"></span>`;
        }
        return '';
    }
    
    /**
     * Mostra alerta na tela
     * @param {string} mensagem - Mensagem do alerta
     * @param {string} tipo - Tipo do alerta (success, warning, danger, info)
     */
    mostrarAlerta(mensagem, tipo = 'info') {
        const alertHtml = `
            <div class="alert alert-${tipo} alert-dismissible fade show" role="alert">
                ${mensagem}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('.container-fluid').prepend(alertHtml);
        
        // Auto-remover após 5 segundos
        setTimeout(() => {
            $('.alert').fadeOut('slow', function() {
                $(this).remove();
            });
        }, this.config.RENDERIZACAO.TEMPO_ALERTA);
    }
}

// Exportar instância única
window.RenderizadorBalancoReceita = new RenderizadorBalancoReceita();