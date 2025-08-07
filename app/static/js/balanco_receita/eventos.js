/**
 * Módulo de Eventos
 * Gerencia todos os event listeners e interações do usuário
 */

class EventosBalancoReceita {
    constructor() {
        this.config = window.ConfiguracoesBalancoReceita;
        this.seletores = this.config.SELETORES;
        this.formatadores = window.FormatadoresBalancoReceita;
    }
    
    /**
     * Configura todos os eventos da aplicação
     */
    configurarTodos() {
        this._configurarEventosFiltros();
        this._configurarEventosBotoes();
        this._configurarEventosToggle();
        this._configurarEventosLancamentos();
    }
    
    /**
     * Configura eventos dos filtros
     * @private
     */
    _configurarEventosFiltros() {
        // Mudança de ano
        $(this.seletores.SELECT_ANO).on('change', (e) => {
            const ano = $(e.target).val();
            window.FiltrosBalancoReceita.carregarMeses(ano);
        });
        
        // Submit do formulário
        $(this.seletores.FORM_FILTROS).on('submit', (e) => {
            e.preventDefault();
            window.ControladorPrincipal.gerarRelatorio();
        });
        
        // Mudança no tipo de receita
        $(document).on('change', this.seletores.SELECT_TIPO_RECEITA, (e) => {
            if (window.dadosRelatorio) {
                const tipoFiltro = $(e.target).val();
                window.FiltrosBalancoReceita.aplicarFiltroReceita(tipoFiltro, window.dadosOriginais);
                
                // Atualizar módulos integrados se disponíveis
                if (window.ultimoRelatorioGerado) {
                    this._atualizarModulosIntegrados();
                }
            }
        });
    }
    
    /**
     * Configura eventos dos botões de ação
     * @private
     */
    _configurarEventosBotoes() {
        // Botão limpar
        $(this.seletores.BTN_LIMPAR).on('click', () => {
            window.ControladorPrincipal.limparTudo();
        });
        
        // Botão exportar Excel
        $(document).on('click', this.seletores.BTN_EXPORTAR, () => {
            window.ExportadorBalancoReceita.exportarExcel(window.dadosRelatorio);
        });
        
        // Botão exportar completo
        $(document).on('click', this.seletores.BTN_EXPORTAR_COMPLETO, () => {
            window.ExportadorBalancoReceita.exportarRelatorioCompleto();
        });
        
        // Botão download imagem
        $(document).on('click', this.seletores.BTN_DOWNLOAD_IMAGEM, () => {
            window.ExportadorBalancoReceita.downloadImagem(window.dadosRelatorio);
        });
        
        // Botão imprimir
        $(document).on('click', this.seletores.BTN_IMPRIMIR, () => {
            window.print();
        });
    }
    
    /**
     * Configura eventos de toggle (expansão/colapso)
     * @private
     */
    _configurarEventosToggle() {
        $(document).on('click', '.toggle-btn', (e) => {
            const $btn = $(e.currentTarget);
            const nivel = parseInt($btn.data('nivel'));
            const id = $btn.data('id');
            const isExpanded = $btn.hasClass('expanded');
            
            switch(nivel) {
                case 1:
                    this._toggleFonte($btn, id, isExpanded);
                    break;
                case 2:
                    this._toggleSubfonte($btn, id, isExpanded);
                    break;
                case 3:
                    this._toggleAlinea($btn, id, isExpanded);
                    break;
            }
        });
    }
    
    /**
     * Toggle de fonte (nível 1)
     * @private
     */
    _toggleFonte($btn, id, isExpanded) {
        const partes = id.split('-');
        const catId = partes[1];
        const fonteId = partes[2];
        
        if (isExpanded) {
            // Colapsar
            $btn.removeClass('expanded').text('+');
            $(`.filho-de-fonte-${catId}-${fonteId}`).hide();
            
            // Colapsar filhos recursivamente
            this._colapsarFilhosFonte(catId, fonteId);
        } else {
            // Expandir
            $btn.addClass('expanded').text('−');
            $(`.filho-de-fonte-${catId}-${fonteId}`).show();
        }
    }
    
    /**
     * Toggle de subfonte (nível 2)
     * @private
     */
    _toggleSubfonte($btn, id, isExpanded) {
        const partes = id.split('-');
        const catId = partes[1];
        const fonteId = partes[2];
        const subfonteId = partes[3];
        
        if (isExpanded) {
            // Colapsar
            $btn.removeClass('expanded').text('+');
            $(`.filho-de-subfonte-${catId}-${fonteId}-${subfonteId}`).hide();
            
            // Colapsar filhos recursivamente
            this._colapsarFilhosSubfonte(catId, fonteId, subfonteId);
        } else {
            // Expandir
            $btn.addClass('expanded').text('−');
            $(`.filho-de-subfonte-${catId}-${fonteId}-${subfonteId}`).show();
        }
    }
    
    /**
     * Toggle de alínea (nível 3)
     * @private
     */
    _toggleAlinea($btn, id, isExpanded) {
        const partes = id.split('-');
        const catId = partes[1];
        const fonteId = partes[2];
        const subfonteId = partes[3];
        const alineaId = partes[4];
        
        if (isExpanded) {
            // Colapsar
            $btn.removeClass('expanded').text('+');
            $(`.filho-de-alinea-${catId}-${fonteId}-${subfonteId}-${alineaId}`).hide();
        } else {
            // Expandir
            $btn.addClass('expanded').text('−');
            $(`.filho-de-alinea-${catId}-${fonteId}-${subfonteId}-${alineaId}`).show();
        }
    }
    
    /**
     * Colapsa filhos de fonte recursivamente
     * @private
     */
    _colapsarFilhosFonte(catId, fonteId) {
        $(`.filho-de-fonte-${catId}-${fonteId}`).each((index, element) => {
            const $subfonte = $(element);
            const subfonteId = $subfonte.data('id');
            
            if (subfonteId) {
                const subPartes = subfonteId.split('-');
                if (subPartes.length >= 4) {
                    const subId = subPartes[3];
                    
                    // Ocultar alíneas da subfonte
                    $(`.filho-de-subfonte-${catId}-${fonteId}-${subId}`).hide();
                    
                    // Ocultar UGs das alíneas
                    $(`.filho-de-subfonte-${catId}-${fonteId}-${subId}`).each((idx, el) => {
                        const $alinea = $(el);
                        const alineaId = $alinea.data('id');
                        
                        if (alineaId) {
                            const alineaPartes = alineaId.split('-');
                            if (alineaPartes.length >= 5) {
                                const aliId = alineaPartes[4];
                                $(`.filho-de-alinea-${catId}-${fonteId}-${subId}-${aliId}`).hide();
                            }
                        }
                    });
                    
                    // Resetar botão da subfonte
                    $subfonte.find('.toggle-btn').removeClass('expanded').text('+');
                }
            }
        });
    }
    
    /**
     * Colapsa filhos de subfonte recursivamente
     * @private
     */
    _colapsarFilhosSubfonte(catId, fonteId, subfonteId) {
        $(`.filho-de-subfonte-${catId}-${fonteId}-${subfonteId}`).each((index, element) => {
            const $alinea = $(element);
            const alineaId = $alinea.data('id');
            
            if (alineaId) {
                const alineaPartes = alineaId.split('-');
                if (alineaPartes.length >= 5) {
                    const aliId = alineaPartes[4];
                    
                    // Ocultar UGs da alínea
                    $(`.filho-de-alinea-${catId}-${fonteId}-${subfonteId}-${aliId}`).hide();
                    
                    // Resetar botão da alínea
                    $alinea.find('.toggle-btn').removeClass('expanded').text('+');
                }
            }
        });
    }
    
    /**
     * Atualiza módulos integrados após mudança de filtro
     * @private
     */
    _atualizarModulosIntegrados() {
        // Análise Visual
        if (typeof analiseVisual !== 'undefined') {
            analiseVisual.atualizarGraficos(window.ultimoRelatorioGerado);
        }
        
        // Comparativo Mensal
        if (typeof comparativoMensal !== 'undefined') {
            comparativoMensal.atualizar(window.ultimoRelatorioGerado);
        }
    }
    
    /**
     * Configura eventos dos lançamentos
     * @private
     */
    _configurarEventosLancamentos() {
        // Clique no botão de lançamentos
        $(document).on('click', '.btn-lancamentos', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const $btn = $(e.currentTarget);
            const $linha = $btn.closest('tr');
            
            // Obter descrição da alínea da linha
            const textoLinha = $linha.find('td:first').text().trim();
            
            const dadosUG = {
                coug: $btn.data('ug'),
                cofontereceita: $btn.data('fonte'),
                cosubfontereceita: $btn.data('subfonte'),
                coalinea: $btn.data('alinea'),
                descricao_alinea: textoLinha // Adicionar descrição da alínea
            };
            
            // Obter período do relatório atual
            const filtros = window.FiltrosBalancoReceita.obterFiltrosSelecionados();
            
            // Criar e mostrar modal
            this._mostrarModalLancamentos(dadosUG, filtros);
        });
    }
    
    /**
     * Mostra modal com lançamentos
     * @private
     */
    _mostrarModalLancamentos(dadosUG, filtros) {
        // Verificar se modal já existe, senão criar
        if ($('#modalLancamentos').length === 0) {
            this._criarModalLancamentos();
        }
        
        // Buscar informação da alínea pai (3 níveis acima da UG)
        let descricaoAlinea = '';
        const $linhaUG = $(`.btn-lancamentos[data-ug="${dadosUG.coug}"][data-alinea="${dadosUG.coalinea}"]`).closest('tr');
        if ($linhaUG.length > 0) {
            // Procurar a linha da alínea (nível 3)
            let $linhaAtual = $linhaUG;
            while ($linhaAtual.length > 0) {
                $linhaAtual = $linhaAtual.prev();
                if ($linhaAtual.attr('data-nivel') === '3' && $linhaAtual.data('id').includes(dadosUG.coalinea)) {
                    descricaoAlinea = $linhaAtual.find('td:first').text().trim();
                    break;
                }
            }
        }
        
        // Atualizar título do modal com duas linhas
        $('#modalLancamentos .modal-title').html(
            `<div>
                <i class="bi bi-list-ul"></i> Lançamentos - UG ${dadosUG.coug}
                <br>
                <small class="text-muted">${dadosUG.coalinea} - ${descricaoAlinea}</small>
            </div>`
        );
        
        // Mostrar loading
        $('#modalLancamentosBody').html(`
            <div class="loading-lancamentos">
                <i class="bi bi-hourglass-split fa-spin" style="font-size: 2rem;"></i>
                <p class="mt-3">Carregando lançamentos...</p>
            </div>
        `);
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('modalLancamentos'));
        modal.show();
        
        // Carregar lançamentos
        this._carregarLancamentos(dadosUG, filtros);
    }
    
    /**
     * Cria estrutura do modal
     * @private
     */
    _criarModalLancamentos() {
        const modalHtml = `
            <div class="modal fade" id="modalLancamentos" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Lançamentos</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="modalLancamentosBody">
                            <!-- Conteúdo será inserido dinamicamente -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                            <button type="button" class="btn btn-success" id="btnExportarLancamentos">
                                <i class="bi bi-file-earmark-excel"></i> Exportar Excel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('body').append(modalHtml);
        
        // Evento de exportar
        $('#btnExportarLancamentos').on('click', () => {
            this._exportarLancamentosExcel();
        });
    }
    
    /**
     * Carrega lançamentos via API
     * @private
     */
    async _carregarLancamentos(dadosUG, filtros) {
        try {
            const parametros = {
                ano: filtros.ano,
                mes: filtros.mes,
                coug: dadosUG.coug,
                cofontereceita: dadosUG.cofontereceita,
                cosubfontereceita: dadosUG.cosubfontereceita,
                coalinea: dadosUG.coalinea
            };
            
            // Armazenar parâmetros para uso posterior no Excel
            window.ultimosParametrosLancamentos = parametros;
            
            const response = await window.ApiBalancoReceita.carregarLancamentos(parametros);
            
            // Renderizar tabela de lançamentos
            this._renderizarTabelaLancamentos(response);
            
            // Armazenar dados para exportação
            window.ultimosLancamentosCarregados = response;
            
        } catch (error) {
            console.error('Erro ao carregar lançamentos:', error);
            $('#modalLancamentosBody').html(`
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> 
                    Erro ao carregar lançamentos: ${error.message}
                </div>
            `);
        }
    }
    
    /**
     * Renderiza tabela de lançamentos
     * @private
     */
    _renderizarTabelaLancamentos(dados) {
        let html = `
            <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                <table class="table table-striped table-hover table-lancamentos">
                    <thead>
                        <tr>
                            <th>Conta Contábil</th>
                            <th>UG Emitente</th>
                            <th>Nº Documento</th>
                            <th>Evento</th>
                            <th class="text-center">D/C</th>
                            <th>Data</th>
                            <th class="text-end">Valor</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        if (dados.lancamentos && dados.lancamentos.length > 0) {
            dados.lancamentos.forEach(lanc => {
                const classDC = lanc.dc === 'C' ? 'text-success' : 'text-danger';
                html += `
                    <tr>
                        <td>${lanc.conta_contabil}</td>
                        <td>${lanc.ug_emitente}</td>
                        <td>${lanc.documento}</td>
                        <td>${lanc.evento}</td>
                        <td class="text-center ${classDC}">${lanc.dc}</td>
                        <td>${lanc.data}</td>
                        <td class="text-end">${this.formatadores.formatarValor(lanc.valor)}</td>
                    </tr>
                `;
            });
        } else {
            html += `
                <tr>
                    <td colspan="7" class="text-center text-muted">
                        Nenhum lançamento encontrado para os filtros selecionados.
                    </td>
                </tr>
            `;
        }
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        // Adicionar totais
        if (dados.totais) {
            html += `
                <div class="totais-lancamentos">
                    <div class="row">
                        <div class="col-md-3">
                            <strong>Total de Registros:</strong> ${dados.total_registros}
                        </div>
                        <div class="col-md-3">
                            <strong>Total Débito:</strong> 
                            <span class="text-danger">${this.formatadores.formatarValor(dados.totais.debito)}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Total Crédito:</strong> 
                            <span class="text-success">${this.formatadores.formatarValor(dados.totais.credito)}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Saldo (C - D):</strong> 
                            <span class="${dados.totais.saldo >= 0 ? 'text-success' : 'text-danger'}">
                                ${this.formatadores.formatarValor(dados.totais.saldo)}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Adicionar aviso se houver mais de 1000 registros
        if (dados.tem_mais_registros) {
            html += `
                <div class="alert alert-info mt-3">
                    <i class="bi bi-info-circle"></i> 
                    <strong>Atenção:</strong> Existem mais de 1.000 lançamentos para este filtro. 
                    Apenas os 1.000 mais recentes estão sendo exibidos. 
                    Para visualizar todos os registros, faça o download do arquivo Excel.
                </div>
            `;
        }
        
        $('#modalLancamentosBody').html(html);
    }
    
    /**
     * Exporta lançamentos para Excel
     * @private
     */
    async _exportarLancamentosExcel() {
        if (!window.ultimosLancamentosCarregados) {
            alert('Nenhum dado para exportar!');
            return;
        }
        
        try {
            // Mostrar loading no botão
            const $btnExportar = $('#btnExportarLancamentos');
            const textoOriginal = $btnExportar.html();
            $btnExportar.prop('disabled', true).html('<i class="bi bi-hourglass-split"></i> Carregando...');
            
            // Buscar TODOS os registros se houver mais de 1000
            let dadosParaExcel = window.ultimosLancamentosCarregados;
            
            if (dadosParaExcel.tem_mais_registros) {
                // Buscar dados completos via API
                const parametros = window.ultimosParametrosLancamentos;
                const response = await $.ajax({
                    url: this.config.API.LANCAMENTOS_EXCEL,
                    method: 'GET',
                    data: parametros
                });
                dadosParaExcel = response;
            }
            
            // Preparar dados para Excel
            const wsData = [
                ['RELATÓRIO DE LANÇAMENTOS'],
                [`Total de Registros: ${dadosParaExcel.total_registros}`],
                [],
                ['Conta Contábil', 'UG Emitente', 'Nº Documento', 'Evento', 'D/C', 'Data', 'Valor']
            ];
            
            dadosParaExcel.lancamentos.forEach(lanc => {
                wsData.push([
                    lanc.conta_contabil,
                    lanc.ug_emitente,
                    lanc.documento,
                    lanc.evento,
                    lanc.dc,
                    lanc.data,
                    lanc.valor
                ]);
            });
            
            // Adicionar totais
            wsData.push([]);
            wsData.push(['TOTAIS']);
            wsData.push(['Total Débito:', '', '', '', '', '', dadosParaExcel.totais.debito]);
            wsData.push(['Total Crédito:', '', '', '', '', '', dadosParaExcel.totais.credito]);
            wsData.push(['Saldo (C - D):', '', '', '', '', '', dadosParaExcel.totais.saldo]);
            
            // Criar workbook
            const ws = XLSX.utils.aoa_to_sheet(wsData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'Lançamentos');
            
            // Download
            const filename = `lancamentos_ug_${new Date().getTime()}.xlsx`;
            XLSX.writeFile(wb, filename);
            
            // Restaurar botão
            $btnExportar.prop('disabled', false).html(textoOriginal);
            
            // Mostrar mensagem de sucesso se foram muitos registros
            if (dadosParaExcel.total_registros > 1000) {
                window.RenderizadorBalancoReceita.mostrarAlerta(
                    `Arquivo Excel gerado com sucesso! Total de ${dadosParaExcel.total_registros.toLocaleString('pt-BR')} registros exportados.`,
                    'success'
                );
            }
            
        } catch (error) {
            console.error('Erro ao exportar Excel:', error);
            alert('Erro ao gerar arquivo Excel. Por favor, tente novamente.');
            
            // Restaurar botão em caso de erro
            $('#btnExportarLancamentos').prop('disabled', false).html(
                '<i class="bi bi-file-earmark-excel"></i> Exportar Excel'
            );
        }
    }
}

// Exportar instância única
window.EventosBalancoReceita = new EventosBalancoReceita();