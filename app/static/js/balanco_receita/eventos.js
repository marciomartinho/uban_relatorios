/**
 * Módulo de Eventos
 * Gerencia todos os event listeners e interações do usuário
 */

class EventosBalancoReceita {
    constructor() {
        this.config = window.ConfiguracoesBalancoReceita;
        this.seletores = this.config.SELETORES;
    }
    
    /**
     * Configura todos os eventos da aplicação
     */
    configurarTodos() {
        this._configurarEventosFiltros();
        this._configurarEventosBotoes();
        this._configurarEventosToggle();
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
        // Obter o valor atual do filtro de tipo de receita
        const tipoReceitaFiltro = $(this.seletores.SELECT_TIPO_RECEITA).val() || 'todas';

        // Análise Visual
        if (typeof analiseVisual !== 'undefined') {
            analiseVisual.atualizarGraficos(window.ultimoRelatorioGerado);
        }
        
        // Comparativo Mensal
        if (typeof comparativoMensal !== 'undefined') {
            comparativoMensal.atualizar(window.ultimoRelatorioGerado);
        }
        
        // Relatório Receita/Fonte
        if (typeof relatorioReceitaFonte !== 'undefined') {
            // MODIFICADO: Passe o filtro para a função de atualização
            relatorioReceitaFonte.atualizar(window.ultimoRelatorioGerado, tipoReceitaFiltro);
        }
    }
}

// Exportar instância única
window.EventosBalancoReceita = new EventosBalancoReceita();