/**
 * Módulo de Filtros
 * Gerencia toda a lógica de filtros e recálculos
 */

class FiltrosBalancoReceita {
    constructor() {
        this.config = window.ConfiguracoesBalancoReceita;
        this.formatadores = window.FormatadoresBalancoReceita;
        this.seletores = this.config.SELETORES;
    }
    
    /**
     * Carrega filtros iniciais na interface
     * @param {Object} dados - Dados dos filtros vindos da API
     */
    carregarFiltrosInterface(dados) {
        console.log('✅ Filtros carregados:', dados);
        
        this._carregarAnos(dados);
        this._carregarUGs(dados);
        
        // Se tem ano atual, carregar meses e selecionar último mês
        if (dados.ano_atual) {
            this.carregarMeses(dados.ano_atual);
            
            if (dados.ultimo_mes) {
                setTimeout(() => {
                    $(this.seletores.SELECT_MES).val(dados.ultimo_mes);
                }, 100);
            }
        }
    }
    
    /**
     * Carrega anos no select
     * @private
     */
    _carregarAnos(dados) {
        const $selectAno = $(this.seletores.SELECT_ANO);
        $selectAno.empty().append('<option value="">Selecione...</option>');
        
        if (dados.anos && dados.anos.length > 0) {
            dados.anos.forEach(ano => {
                $selectAno.append(`<option value="${ano}">${ano}</option>`);
            });
            
            if (dados.ano_atual) {
                $selectAno.val(dados.ano_atual);
            }
        }
    }
    
    /**
     * Carrega UGs no select
     * @private
     */
    _carregarUGs(dados) {
        const $selectUG = $(this.seletores.SELECT_UG);
        $selectUG.empty().append('<option value="">📊 Dados Consolidados</option>');
        
        if (dados.ugs && dados.ugs.length > 0) {
            dados.ugs.forEach(ug => {
                $selectUG.append(`<option value="${ug.codigo}">🏛️ ${ug.descricao}</option>`);
            });
        }
    }
    
    /**
     * Carrega meses disponíveis para o ano selecionado
     * @param {string} ano - Ano selecionado
     */
    carregarMeses(ano) {
        const $selectMes = $(this.seletores.SELECT_MES);
        
        if (!ano) {
            $selectMes.empty().append('<option value="">Selecione o ano primeiro</option>');
            return;
        }
        
        $selectMes.empty().append('<option value="">Selecione...</option>');
        
        for (let i = 1; i <= 12; i++) {
            const nomeMes = this.formatadores.obterNomeMes(i);
            $selectMes.append(`<option value="${i}">${i} - ${nomeMes}</option>`);
        }
    }
    
    /**
     * Obtém valores dos filtros selecionados
     * @returns {Object} Objeto com valores dos filtros
     */
    obterFiltrosSelecionados() {
        return {
            ano: $(this.seletores.SELECT_ANO).val(),
            mes: $(this.seletores.SELECT_MES).val(),
            coug: $(this.seletores.SELECT_UG).val(),
            tipo_receita: $(this.seletores.SELECT_TIPO_RECEITA).val() || 'todas'
        };
    }
    
    /**
     * Valida se os filtros obrigatórios foram selecionados
     * @returns {boolean} true se válido, false caso contrário
     */
    validarFiltros() {
        const filtros = this.obterFiltrosSelecionados();
        return !(!filtros.ano || !filtros.mes);
    }
    
    /**
     * Limpa todos os filtros
     */
    limparFiltros() {
        $(this.seletores.FORM_FILTROS)[0].reset();
        $(this.seletores.SELECT_MES).empty().append('<option value="">Selecione o ano primeiro</option>');
        $(this.seletores.SELECT_TIPO_RECEITA).val('todas');
    }
    
    /**
     * Aplica filtro de tipo de receita na tabela
     * @param {string} tipoFiltro - Tipo de filtro a aplicar
     * @param {Object} dadosOriginais - Dados originais do relatório
     */
    aplicarFiltroReceita(tipoFiltro, dadosOriginais) {
        const filtroAtivo = tipoFiltro || $(this.seletores.SELECT_TIPO_RECEITA).val();
        console.log('Aplicando filtro:', filtroAtivo);
        
        // Resetar todas as linhas
        $('tr[data-nivel]').hide();
        
        if (filtroAtivo === 'todas') {
            this._mostrarTodasReceitas(dadosOriginais);
        } else {
            this._aplicarFiltroEspecifico(filtroAtivo, dadosOriginais);
        }
        
        // Recalcular totais
        this.recalcularTotais(filtroAtivo, dadosOriginais);
    }
    
    /**
     * Mostra todas as receitas
     * @private
     */
    _mostrarTodasReceitas(dadosOriginais) {
        // Mostrar categorias e fontes
        $('tr[data-nivel="0"]').show();
        $('tr[data-nivel="1"]').show();
        
        // Restaurar valores originais das categorias
        if (dadosOriginais) {
            this._restaurarValoresOriginais(dadosOriginais);
        }
        
        // Respeitar estado de expansão
        this._respeitarEstadoExpansao();
    }
    
    /**
     * Aplica filtro específico de receita
     * @private
     */
    _aplicarFiltroEspecifico(filtroAtivo, dadosOriginais) {
        const fontesParaMostrar = this.config.TIPOS_RECEITA[filtroAtivo] || [];
        const { categoriasComDados, totaisPorCategoria } = this._calcularTotaisFiltrados(fontesParaMostrar, dadosOriginais);
        
        console.log('Fontes para mostrar:', fontesParaMostrar);
        console.log('Categorias com dados:', Array.from(categoriasComDados));
        
        // Mostrar e atualizar categorias
        this._mostrarCategoriasComDados(categoriasComDados, totaisPorCategoria);
        
        // Mostrar elementos filtrados
        this._mostrarElementosFiltrados(fontesParaMostrar, categoriasComDados);
    }
    
    /**
     * Calcula totais para fontes filtradas
     * @private
     */
    _calcularTotaisFiltrados(fontesParaMostrar, dadosOriginais) {
        const categoriasComDados = new Set();
        const totaisPorCategoria = {};
        
        if (!dadosOriginais || !dadosOriginais.dados) return { categoriasComDados, totaisPorCategoria };
        
        dadosOriginais.dados.forEach(item => {
            if (item.nivel === 1 && item.id) {
                const match = item.id.match(/fonte-(\d+)-(\d+)/);
                if (match) {
                    const catId = match[1];
                    const fonteId = match[2];
                    
                    if (fontesParaMostrar.includes(fonteId)) {
                        categoriasComDados.add(catId);
                        
                        if (!totaisPorCategoria[catId]) {
                            totaisPorCategoria[catId] = {
                                previsao_inicial: 0,
                                previsao_atualizada: 0,
                                receita_atual: 0,
                                receita_anterior: 0,
                                variacao_absoluta: 0,
                                variacao_percentual: 0
                            };
                        }
                        
                        totaisPorCategoria[catId].previsao_inicial += item.previsao_inicial;
                        totaisPorCategoria[catId].previsao_atualizada += item.previsao_atualizada;
                        totaisPorCategoria[catId].receita_atual += item.receita_atual;
                        totaisPorCategoria[catId].receita_anterior += item.receita_anterior;
                    }
                }
            }
        });
        
        // Calcular variações
        Object.keys(totaisPorCategoria).forEach(catId => {
            const totais = totaisPorCategoria[catId];
            totais.variacao_absoluta = totais.receita_atual - totais.receita_anterior;
            if (totais.receita_anterior !== 0) {
                totais.variacao_percentual = (totais.variacao_absoluta / Math.abs(totais.receita_anterior)) * 100;
            } else {
                totais.variacao_percentual = totais.receita_atual !== 0 ? 100 : 0;
            }
        });
        
        return { categoriasComDados, totaisPorCategoria };
    }
    
    /**
     * Mostra categorias com dados e atualiza valores
     * @private
     */
    _mostrarCategoriasComDados(categoriasComDados, totaisPorCategoria) {
        $('tr[data-nivel="0"]').each((index, element) => {
            const $row = $(element);
            const id = $row.data('id');
            const match = id.match(/cat-(\d+)/);
            
            if (match) {
                const catId = match[1];
                if (categoriasComDados.has(catId)) {
                    $row.show();
                    
                    if (totaisPorCategoria[catId]) {
                        this._atualizarValoresLinha($row, totaisPorCategoria[catId]);
                    }
                }
            }
        });
    }
    
    /**
     * Atualiza valores de uma linha da tabela
     * @private
     */
    _atualizarValoresLinha($row, valores) {
        $row.find('td:eq(1)').text(this.formatadores.formatarValor(valores.previsao_inicial));
        $row.find('td:eq(2)').text(this.formatadores.formatarValor(valores.previsao_atualizada));
        $row.find('td:eq(3)').text(this.formatadores.formatarValor(valores.receita_atual));
        $row.find('td:eq(4)').text(this.formatadores.formatarValor(valores.receita_anterior));
        
        const $varAbsoluta = $row.find('td:eq(5)');
        $varAbsoluta.text(this.formatadores.formatarValor(valores.variacao_absoluta));
        $varAbsoluta.removeClass('text-success text-danger');
        $varAbsoluta.addClass(this.formatadores.obterClasseVariacao(valores.variacao_absoluta));
        
        const $varPercentual = $row.find('td:eq(6)');
        $varPercentual.text(this.formatadores.formatarPercentual(valores.variacao_percentual));
        $varPercentual.removeClass('text-success text-danger');
        $varPercentual.addClass(this.formatadores.obterClasseVariacao(valores.variacao_percentual));
    }
    
    /**
     * Restaura valores originais das categorias
     * @private
     */
    _restaurarValoresOriginais(dadosOriginais) {
        dadosOriginais.dados.forEach(item => {
            if (item.nivel === 0) {
                const $row = $(`tr[data-id="${item.id}"]`);
                if ($row.length) {
                    this._atualizarValoresLinha($row, item);
                }
            }
        });
    }
    
    /**
     * Respeita estado de expansão dos elementos
     * @private
     */
    _respeitarEstadoExpansao() {
        // Verificar subfontes
        $('tr[data-nivel="2"]').each((index, element) => {
            const $row = $(element);
            if (this._deveSerVisivel($row, 2)) {
                $row.show();
            }
        });
        
        // Verificar alíneas
        $('tr[data-nivel="3"]').each((index, element) => {
            const $row = $(element);
            if (this._deveSerVisivel($row, 3)) {
                $row.show();
            }
        });
        
        // Verificar UGs
        $('tr[data-nivel="4"]').each((index, element) => {
            const $row = $(element);
            if (this._deveSerVisivel($row, 4)) {
                $row.show();
            }
        });
    }
    
    /**
     * Verifica se elemento deve ser visível baseado no estado de expansão
     * @private
     */
    _deveSerVisivel($row, nivel) {
        const classes = $row.attr('class') || '';
        
        if (nivel === 2) {
            const match = classes.match(/filho-de-fonte-(\d+)-(\d+)/);
            if (match) {
                const fonteBtn = $(`.toggle-btn[data-id="fonte-${match[1]}-${match[2]}"]`);
                return fonteBtn.hasClass('expanded');
            }
        } else if (nivel === 3) {
            const match = classes.match(/filho-de-subfonte-(\d+)-(\d+)-(\d+)/);
            if (match) {
                const subfonteBtn = $(`.toggle-btn[data-id="subfonte-${match[1]}-${match[2]}-${match[3]}"]`);
                const fonteBtn = $(`.toggle-btn[data-id="fonte-${match[1]}-${match[2]}"]`);
                return fonteBtn.hasClass('expanded') && subfonteBtn.hasClass('expanded');
            }
        } else if (nivel === 4) {
            const match = classes.match(/filho-de-alinea-(\d+)-(\d+)-(\d+)-(\d+)/);
            if (match) {
                const alineaBtn = $(`.toggle-btn[data-id="alinea-${match[1]}-${match[2]}-${match[3]}-${match[4]}"]`);
                const subfonteBtn = $(`.toggle-btn[data-id="subfonte-${match[1]}-${match[2]}-${match[3]}"]`);
                const fonteBtn = $(`.toggle-btn[data-id="fonte-${match[1]}-${match[2]}"]`);
                return fonteBtn.hasClass('expanded') && subfonteBtn.hasClass('expanded') && alineaBtn.hasClass('expanded');
            }
        }
        
        return false;
    }
    
    /**
     * Mostra elementos filtrados respeitando hierarquia
     * @private
     */
    _mostrarElementosFiltrados(fontesParaMostrar, categoriasComDados) {
        $('tr[data-nivel]').each((index, element) => {
            const $row = $(element);
            const nivel = parseInt($row.data('nivel'));
            const id = $row.data('id') || '';
            
            if (nivel === 1) {
                this._verificarFonte($row, id, fontesParaMostrar, categoriasComDados);
            } else if (nivel === 2) {
                this._verificarSubfonte($row, fontesParaMostrar, categoriasComDados);
            } else if (nivel === 3) {
                this._verificarAlinea($row, fontesParaMostrar, categoriasComDados);
            } else if (nivel === 4) {
                this._verificarUG($row, fontesParaMostrar, categoriasComDados);
            }
        });
    }
    
    /**
     * Verifica se fonte deve ser mostrada
     * @private
     */
    _verificarFonte($row, id, fontesParaMostrar, categoriasComDados) {
        const match = id.match(/fonte-(\d+)-(\d+)/);
        if (match) {
            const catId = match[1];
            const fonteId = match[2];
            if (fontesParaMostrar.includes(fonteId) && categoriasComDados.has(catId)) {
                $row.show();
            }
        }
    }
    
    /**
     * Verifica se subfonte deve ser mostrada
     * @private
     */
    _verificarSubfonte($row, fontesParaMostrar, categoriasComDados) {
        const classes = $row.attr('class') || '';
        const match = classes.match(/filho-de-fonte-(\d+)-(\d+)/);
        
        if (match) {
            const catId = match[1];
            const fonteId = match[2];
            if (fontesParaMostrar.includes(fonteId) && categoriasComDados.has(catId)) {
                if (this._deveSerVisivel($row, 2)) {
                    $row.show();
                }
            }
        }
    }
    
    /**
     * Verifica se alínea deve ser mostrada
     * @private
     */
    _verificarAlinea($row, fontesParaMostrar, categoriasComDados) {
        const classes = $row.attr('class') || '';
        const match = classes.match(/filho-de-subfonte-(\d+)-(\d+)-(\d+)/);
        
        if (match) {
            const catId = match[1];
            const fonteId = match[2];
            if (fontesParaMostrar.includes(fonteId) && categoriasComDados.has(catId)) {
                if (this._deveSerVisivel($row, 3)) {
                    $row.show();
                }
            }
        }
    }
    
    /**
     * Verifica se UG deve ser mostrada
     * @private
     */
    _verificarUG($row, fontesParaMostrar, categoriasComDados) {
        const classes = $row.attr('class') || '';
        const match = classes.match(/filho-de-alinea-(\d+)-(\d+)-(\d+)-(\d+)/);
        
        if (match) {
            const catId = match[1];
            const fonteId = match[2];
            if (fontesParaMostrar.includes(fonteId) && categoriasComDados.has(catId)) {
                if (this._deveSerVisivel($row, 4)) {
                    $row.show();
                }
            }
        }
    }
    
    /**
     * Recalcula totais baseado no filtro selecionado
     * @param {string} filtroAtivo - Filtro ativo
     * @param {Object} dadosOriginais - Dados originais
     */
    recalcularTotais(filtroAtivo, dadosOriginais) {
        if (!dadosOriginais) {
            console.log('Dados não disponíveis para recalcular totais');
            return;
        }
        
        console.log('Recalculando totais para filtro:', filtroAtivo);
        
        let totais = {
            previsao_inicial: 0,
            previsao_atualizada: 0,
            receita_atual: 0,
            receita_anterior: 0,
            variacao_absoluta: 0,
            variacao_percentual: 0
        };
        
        if (filtroAtivo === 'todas') {
            // Usar totais originais
            totais = window.dadosRelatorio.totais;
        } else {
            // Calcular totais filtrados
            const fontesParaSomar = this.config.TIPOS_RECEITA[filtroAtivo] || [];
            
            dadosOriginais.dados.forEach(item => {
                if (item.nivel === 1 && item.id) {
                    const match = item.id.match(/fonte-\d+-(\d+)/);
                    if (match && fontesParaSomar.includes(match[1])) {
                        totais.previsao_inicial += item.previsao_inicial;
                        totais.previsao_atualizada += item.previsao_atualizada;
                        totais.receita_atual += item.receita_atual;
                        totais.receita_anterior += item.receita_anterior;
                    }
                }
            });
            
            // Calcular variações
            totais.variacao_absoluta = totais.receita_atual - totais.receita_anterior;
            if (totais.receita_anterior !== 0) {
                totais.variacao_percentual = (totais.variacao_absoluta / Math.abs(totais.receita_anterior)) * 100;
            } else {
                totais.variacao_percentual = totais.receita_atual !== 0 ? 100 : 0;
            }
        }
        
        // Atualizar linha de total na tabela
        const $totalRow = $('tr.table-dark');
        if ($totalRow.length) {
            this._atualizarValoresLinha($totalRow, totais);
        }
    }
}

// Exportar instância única
window.FiltrosBalancoReceita = new FiltrosBalancoReceita();