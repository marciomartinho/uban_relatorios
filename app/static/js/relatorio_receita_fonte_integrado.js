/**
 * Módulo de Relatório Receita/Fonte Integrado
 * Versão 2.0 - Reescrita completa
 * 
 * @author Sistema de Balanço de Receitas
 * @version 2.0.0
 * @description Gerencia relatórios detalhados por código de fonte ou receita com suporte a lançamentos
 */

class RelatorioReceitaFonteIntegrado {
    constructor() {
        // Configuração do estado inicial
        this.state = {
            isInitialized: false,
            currentType: 'fonte', // 'fonte' ou 'receita'
            currentFilter: 'todas',
            isLoading: false,
            expandedRows: new Set(),
            currentModal: null
        };

        // Cache de dados
        this.dataCache = {
            originalData: null,
            fonteReport: null,
            receitaReport: null,
            lastLancamentos: null,
            lastLancamentosParams: null
        };

        // Configurações da API
        this.apiConfig = {
            baseUrl: '/balanco-receita/api',
            endpoints: {
                report: '/relatorio-receita-fonte',
                lancamentos: '/lancamentos-fonte-alinea',
                lancamentosExcel: '/lancamentos-fonte-alinea-excel'
            },
            timeout: 30000 // 30 segundos
        };

        // Seletores DOM
        this.selectors = {
            container: '#relatorioReceitaFonteContainer',
            modal: '#modalLancamentosRF',
            loading: '#loadingRelatorioRF',
            tableContainer: '#tabelaRelatorioRFContainer',
            tableBody: '#tbodyRelatorioRF',
            emptyState: '#emptyStateRF',
            btnFonte: '#btnPorFonte',
            btnReceita: '#btnPorReceita',
            modalBody: '#modalLancamentosRFBody',
            modalTitle: '#modalLancamentosRFTitle',
            btnExportLancamentos: '#btnExportarLancamentosRF'
        };

        // Configurações de formatação
        this.formatting = {
            locale: 'pt-BR',
            currency: {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        };
    }

    // ================== INICIALIZAÇÃO ==================

    /**
     * Inicializa o módulo com dados do relatório principal
     */
    inicializar(dadosRelatorio) {
        console.log('🚀 Inicializando Relatório Receita/Fonte v2.0');
        
        try {
            // Validar dados de entrada
            if (!this.validarDadosEntrada(dadosRelatorio)) {
                throw new Error('Dados de entrada inválidos');
            }

            // Armazenar dados originais
            this.dataCache.originalData = dadosRelatorio;

            // Criar interface se necessário
            if (!this.state.isInitialized) {
                this.criarInterface();
                this.configurarEventos();
                this.state.isInitialized = true;
            }

            // Carregar dados iniciais
            this.carregarRelatorio(this.state.currentType);

            console.log('✅ Módulo inicializado com sucesso');

        } catch (error) {
            console.error('❌ Erro ao inicializar módulo:', error);
            this.mostrarErro('Erro ao inicializar o módulo. Por favor, recarregue a página.');
        }
    }

    /**
     * Valida dados de entrada
     */
    validarDadosEntrada(dados) {
        if (!dados) return false;
        if (!dados.periodo || !dados.periodo.ano || !dados.periodo.mes) return false;
        return true;
    }

    // ================== INTERFACE ==================

    /**
     * Cria a interface HTML do módulo
     */
    criarInterface() {
        const html = this.gerarHTMLInterface();
        
        // Determinar onde inserir
        const insertAfter = $('#comparativoMensalContainer').length 
            ? '#comparativoMensalContainer' 
            : $('#analiseVisualContainer').length 
                ? '#analiseVisualContainer' 
                : '#relatorioContainer';
        
        $(insertAfter).after(html);
        console.log('📋 Interface criada');
    }

    /**
     * Gera HTML da interface
     */
    gerarHTMLInterface() {
        return `
            <!-- Container Principal -->
            <div id="relatorioReceitaFonteContainer" class="mt-4">
                <div class="card shadow">
                    <!-- Header -->
                    <div class="card-header bg-primary text-white">
                        <div class="row align-items-center">
                            <div class="col-md-7">
                                <h5 class="mb-0">
                                    <i class="bi bi-table"></i> 
                                    Relatório Detalhado por Fonte/Receita
                                </h5>
                                <small class="opacity-75">
                                    Análise detalhada da receita por código de fonte ou natureza da receita
                                </small>
                            </div>
                            <div class="col-md-5 text-end">
                                <!-- Botões de Tipo -->
                                <div class="btn-group btn-group-sm" role="group">
                                    <button type="button" class="btn btn-light active" id="btnPorFonte">
                                        <i class="bi bi-folder"></i> Por Fonte
                                    </button>
                                    <button type="button" class="btn btn-light" id="btnPorReceita">
                                        <i class="bi bi-receipt"></i> Por Receita
                                    </button>
                                </div>
                                <!-- Botão Excel -->
                                <button class="btn btn-light btn-sm ms-2" id="btnExportarRelatorioRF">
                                    <i class="bi bi-file-excel"></i> Excel
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Body -->
                    <div class="card-body">
                        <!-- Loading State -->
                        <div id="loadingRelatorioRF" class="text-center py-5" style="display: none;">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Carregando...</span>
                            </div>
                            <p class="mt-3 text-muted">Processando dados do relatório...</p>
                        </div>

                        <!-- Tabela de Dados -->
                        <div id="tabelaRelatorioRFContainer" style="display: none;">
                            <!-- Filtros Rápidos -->
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <input type="text" 
                                           class="form-control form-control-sm" 
                                           id="filtroRapidoRF" 
                                           placeholder="🔍 Filtrar por código ou descrição...">
                                </div>
                                <div class="col-md-6 text-end">
                                    <button class="btn btn-sm btn-outline-secondary" id="btnExpandirTodos">
                                        <i class="bi bi-arrows-expand"></i> Expandir Todos
                                    </button>
                                    <button class="btn btn-sm btn-outline-secondary" id="btnRecolherTodos">
                                        <i class="bi bi-arrows-collapse"></i> Recolher Todos
                                    </button>
                                </div>
                            </div>

                            <!-- Tabela -->
                            <div class="table-responsive">
                                <table class="table table-hover table-sm" id="tabelaRelatorioRF">
                                    <thead class="table-light sticky-top">
                                        <tr>
                                            <th class="col-5">
                                                <span id="headerTipoRF">Código de Fonte</span>
                                            </th>
                                            <th class="text-end">Previsão Inicial</th>
                                            <th class="text-end">Previsão Atualizada</th>
                                            <th class="text-end">Realizada <span class="anoAtualRF"></span></th>
                                            <th class="text-end">Realizada <span class="anoAnteriorRF"></span></th>
                                            <th class="text-center">Variação</th>
                                            <th class="text-center" style="width: 120px;">Ações</th>
                                        </tr>
                                    </thead>
                                    <tbody id="tbodyRelatorioRF">
                                        <!-- Dados serão inseridos aqui -->
                                    </tbody>
                                    <tfoot class="table-secondary">
                                        <tr class="fw-bold">
                                            <td>TOTAL GERAL</td>
                                            <td class="text-end" id="totalPrevisaoInicialRF">0,00</td>
                                            <td class="text-end" id="totalPrevisaoAtualizadaRF">0,00</td>
                                            <td class="text-end" id="totalReceitaAtualRF">0,00</td>
                                            <td class="text-end" id="totalReceitaAnteriorRF">0,00</td>
                                            <td class="text-center" id="totalVariacaoRF">0,00%</td>
                                            <td></td>
                                        </tr>
                                    </tfoot>
                                </table>
                            </div>
                        </div>

                        <!-- Empty State -->
                        <div id="emptyStateRF" class="text-center py-5" style="display: none;">
                            <i class="bi bi-inbox display-4 text-muted"></i>
                            <h5 class="mt-3 text-muted">Nenhum dado encontrado</h5>
                            <p class="text-muted">
                                Não há dados para os filtros selecionados.<br>
                                Tente ajustar os filtros ou selecionar outro período.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Modal de Lançamentos -->
            <div class="modal fade" id="modalLancamentosRF" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header bg-light">
                            <h5 class="modal-title" id="modalLancamentosRFTitle">
                                <i class="bi bi-list-ul"></i> Lançamentos
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="modalLancamentosRFBody">
                            <!-- Conteúdo dinâmico -->
                        </div>
                        <div class="modal-footer">
                            <span class="me-auto text-muted" id="statusLancamentosRF"></span>
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                Fechar
                            </button>
                            <button type="button" class="btn btn-success" id="btnExportarLancamentosRF">
                                <i class="bi bi-file-excel"></i> Exportar Excel
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // ================== EVENTOS ==================

    /**
     * Configura todos os eventos do módulo
     */
    configurarEventos() {
        // Mudança de tipo de relatório
        $(this.selectors.btnFonte).on('click', () => this.mudarTipoRelatorio('fonte'));
        $(this.selectors.btnReceita).on('click', () => this.mudarTipoRelatorio('receita'));

        // Exportação
        $('#btnExportarRelatorioRF').on('click', () => this.exportarRelatorioExcel());
        $(this.selectors.btnExportLancamentos).on('click', () => this.exportarLancamentosExcel());

        // Expansão/Colapso
        $('#btnExpandirTodos').on('click', () => this.expandirTodos());
        $('#btnRecolherTodos').on('click', () => this.recolherTodos());

        // Filtro rápido
        $('#filtroRapidoRF').on('input', (e) => this.aplicarFiltroRapido(e.target.value));

        // Delegação de eventos para elementos dinâmicos
        $(document).on('click', '.btn-toggle-rf', (e) => {
            const id = $(e.currentTarget).data('id');
            this.toggleItem(id);
        });

        $(document).on('click', '.btn-lancamentos-rf', (e) => {
            e.preventDefault();
            const $btn = $(e.currentTarget);
            this.abrirModalLancamentos({
                codigo: $btn.data('codigo'),
                codigoPai: $btn.data('codigo-pai'),
                descricao: $btn.data('descricao'),
                tipo: $btn.data('tipo')
            });
        });

        console.log('⚡ Eventos configurados');
    }

    // ================== CARREGAMENTO DE DADOS ==================

    /**
     * Carrega dados do relatório
     */
    async carregarRelatorio(tipo) {
        // Validar tipo
        if (!['fonte', 'receita'].includes(tipo)) {
            console.error('Tipo de relatório inválido:', tipo);
            return;
        }

        // Verificar cache
        const cacheKey = tipo === 'fonte' ? 'fonteReport' : 'receitaReport';
        if (this.dataCache[cacheKey] && !this.shouldRefreshCache()) {
            console.log('📦 Usando dados do cache');
            this.renderizarRelatorio(this.dataCache[cacheKey]);
            return;
        }

        // Mostrar loading
        this.mostrarLoading(true);

        try {
            // Preparar parâmetros
            const params = this.prepararParametrosRelatorio(tipo);
            
            // Fazer requisição
            const response = await this.fazerRequisicao(
                `${this.apiConfig.baseUrl}${this.apiConfig.endpoints.report}`,
                params
            );

            // Armazenar em cache
            this.dataCache[cacheKey] = response;

            // Renderizar
            this.renderizarRelatorio(response);

            console.log('✅ Relatório carregado:', tipo);

        } catch (error) {
            console.error('❌ Erro ao carregar relatório:', error);
            this.mostrarErro('Erro ao carregar dados do relatório');
        } finally {
            this.mostrarLoading(false);
        }
    }

    /**
     * Prepara parâmetros para requisição do relatório
     */
    prepararParametrosRelatorio(tipo) {
        const dados = this.dataCache.originalData;
        
        const params = {
            tipo: tipo,
            ano: dados.periodo.ano,
            mes: dados.periodo.mes
        };

        // Adicionar filtros opcionais
        if (dados.filtros?.coug) {
            params.coug = dados.filtros.coug;
        }

        if (this.state.currentFilter && this.state.currentFilter !== 'todas') {
            params.tipo_receita = this.state.currentFilter;
        }

        return params;
    }

    /**
     * Carrega lançamentos
     */
    async carregarLancamentos(dados) {
        try {
            console.log('📊 Carregando lançamentos:', dados);

            // Preparar parâmetros
            const params = this.prepararParametrosLancamentos(dados);
            
            // Armazenar para uso posterior
            this.dataCache.lastLancamentosParams = params;

            // Fazer requisição
            const response = await this.fazerRequisicao(
                `${this.apiConfig.baseUrl}${this.apiConfig.endpoints.lancamentos}`,
                params
            );

            // Armazenar resposta
            this.dataCache.lastLancamentos = response;

            // Renderizar
            this.renderizarLancamentos(response);

            // Atualizar status
            this.atualizarStatusLancamentos(response);

        } catch (error) {
            console.error('❌ Erro ao carregar lançamentos:', error);
            this.mostrarErroModal(error.message);
        }
    }

    /**
     * Prepara parâmetros para requisição de lançamentos
     */
    prepararParametrosLancamentos(dados) {
        const params = {
            ano: this.dataCache.originalData.periodo.ano
            // Não enviar mês para buscar o ano todo
        };

        // Adicionar códigos baseado no tipo
        if (dados.tipo === 'fonte') {
            params.cofonte = dados.codigoPai;
            params.coalinea = dados.codigo;
        } else {
            params.coalinea = dados.codigoPai;
            params.cofonte = dados.codigo;
        }

        // Adicionar COUG se disponível
        if (this.dataCache.originalData.filtros?.coug) {
            params.coug = this.dataCache.originalData.filtros.coug;
        }

        console.log('📤 Parâmetros de lançamentos:', params);
        return params;
    }

    // ================== RENDERIZAÇÃO ==================

    /**
     * Renderiza o relatório na tabela
     */
    renderizarRelatorio(dados) {
        // Validar dados
        if (!dados || !dados.dados || dados.dados.length === 0) {
            this.mostrarEmptyState();
            return;
        }

        // Atualizar cabeçalhos
        this.atualizarCabecalhos(dados);

        // Limpar tabela
        const $tbody = $(this.selectors.tableBody);
        $tbody.empty();

        // Renderizar linhas
        dados.dados.forEach(item => {
            const $row = this.criarLinhaTabela(item, dados.tipo);
            $tbody.append($row);
        });

        // Atualizar totais
        this.atualizarTotais(dados.totais);

        // Mostrar tabela
        this.mostrarTabela();

        console.log('📊 Relatório renderizado');
    }

    /**
     * Cria uma linha da tabela
     */
    criarLinhaTabela(item, tipoRelatorio) {
        const isExpanded = this.state.expandedRows.has(item.id);
        const displayStyle = item.nivel === 1 && !isExpanded ? 'display: none;' : '';
        
        // Botão de expansão
        let btnExpand = '';
        if (item.tem_filhos) {
            const icon = isExpanded ? '▼' : '▶';
            btnExpand = `
                <button class="btn btn-sm btn-link p-0 me-2 btn-toggle-rf" 
                        data-id="${item.id}">
                    ${icon}
                </button>
            `;
        }

        // Botão de lançamentos (apenas para itens secundários com valor)
        let btnLancamentos = '';
        if (item.nivel === 1 && item.receita_atual > 0) {
            const codigoPai = item.pai_id ? item.pai_id.split('-')[1] : '';
            btnLancamentos = `
                <button class="btn btn-sm btn-outline-primary btn-lancamentos-rf" 
                        data-codigo="${item.codigo}"
                        data-codigo-pai="${codigoPai}"
                        data-descricao="${item.descricao}"
                        data-tipo="${tipoRelatorio}"
                        title="Ver lançamentos detalhados">
                    <i class="bi bi-list-ul"></i>
                </button>
            `;
        }

        // Classe de variação
        const variacaoClass = item.variacao_percentual >= 0 ? 'text-success' : 'text-danger';
        const variacaoIcon = item.variacao_percentual >= 0 ? '↑' : '↓';
        const variacaoText = `${variacaoIcon} ${Math.abs(item.variacao_percentual).toFixed(2)}%`;

        // Classes da linha
        const rowClasses = [
            item.nivel === 0 ? 'table-light fw-bold' : '',
            'linha-rf',
            `nivel-${item.nivel}`
        ].filter(Boolean).join(' ');

        // Padding para hierarquia
        const paddingLeft = item.nivel * 25;

        return `
            <tr class="${rowClasses}" 
                data-id="${item.id}"
                data-nivel="${item.nivel}"
                data-pai-id="${item.pai_id || ''}"
                data-codigo="${item.codigo}"
                style="${displayStyle}">
                <td style="padding-left: ${paddingLeft}px;">
                    ${btnExpand}
                    <span class="codigo-rf">${item.codigo}</span> - 
                    <span class="descricao-rf">${item.descricao}</span>
                </td>
                <td class="text-end">${this.formatarMoeda(item.previsao_inicial)}</td>
                <td class="text-end">${this.formatarMoeda(item.previsao_atualizada)}</td>
                <td class="text-end">${this.formatarMoeda(item.receita_atual)}</td>
                <td class="text-end">${this.formatarMoeda(item.receita_anterior)}</td>
                <td class="text-center">
                    <span class="${variacaoClass}">${variacaoText}</span>
                </td>
                <td class="text-center">
                    ${btnLancamentos}
                </td>
            </tr>
        `;
    }

    /**
     * Renderiza lançamentos no modal
     */
    renderizarLancamentos(dados) {
        let html = `
            <div class="container-fluid">
                <!-- Resumo -->
                <div class="row mb-3">
                    <div class="col-12">
                        <div class="alert alert-info">
                            <i class="bi bi-info-circle"></i>
                            <strong>Total de Registros:</strong> ${dados.total_registros || 0}
                            ${dados.tem_mais_registros ? '<span class="badge bg-warning ms-2">Limitado a 1000</span>' : ''}
                        </div>
                    </div>
                </div>

                <!-- Tabela de Lançamentos -->
                <div class="row">
                    <div class="col-12">
                        <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                            <table class="table table-striped table-hover table-sm">
                                <thead class="sticky-top bg-white">
                                    <tr>
                                        <th>Conta Contábil</th>
                                        <th>UG Emitente</th>
                                        <th>UG Contábil</th>
                                        <th>Documento</th>
                                        <th>Evento</th>
                                        <th class="text-center">D/C</th>
                                        <th>Data</th>
                                        <th class="text-end">Valor</th>
                                    </tr>
                                </thead>
                                <tbody>
        `;

        // Adicionar linhas
        if (dados.lancamentos && dados.lancamentos.length > 0) {
            dados.lancamentos.forEach(lanc => {
                const dcClass = lanc.dc === 'C' ? 'text-success' : 'text-danger';
                const dcIcon = lanc.dc === 'C' ? '↑' : '↓';
                
                html += `
                    <tr>
                        <td><small>${lanc.conta_contabil || '-'}</small></td>
                        <td><small>${lanc.ug_emitente || '-'}</small></td>
                        <td><small>${lanc.ug_contabil || '-'}</small></td>
                        <td><small>${lanc.documento || '-'}</small></td>
                        <td><small>${lanc.evento || '-'}</small></td>
                        <td class="text-center ${dcClass}">
                            <strong>${dcIcon} ${lanc.dc || '-'}</strong>
                        </td>
                        <td><small>${this.formatarData(lanc.data)}</small></td>
                        <td class="text-end">
                            <strong>${this.formatarMoeda(lanc.valor)}</strong>
                        </td>
                    </tr>
                `;
            });
        } else {
            html += `
                <tr>
                    <td colspan="8" class="text-center text-muted py-4">
                        <i class="bi bi-inbox display-6"></i><br>
                        Nenhum lançamento encontrado para os filtros selecionados
                    </td>
                </tr>
            `;
        }

        html += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
        `;

        // Adicionar totais se existirem
        if (dados.totais) {
            const saldoClass = dados.totais.saldo >= 0 ? 'text-success' : 'text-danger';
            
            html += `
                <div class="row mt-3">
                    <div class="col-12">
                        <div class="card bg-light">
                            <div class="card-body">
                                <div class="row text-center">
                                    <div class="col-md-4">
                                        <h6>Total Débito</h6>
                                        <h4 class="text-danger">${this.formatarMoeda(dados.totais.debito)}</h4>
                                    </div>
                                    <div class="col-md-4">
                                        <h6>Total Crédito</h6>
                                        <h4 class="text-success">${this.formatarMoeda(dados.totais.credito)}</h4>
                                    </div>
                                    <div class="col-md-4">
                                        <h6>Saldo (C - D)</h6>
                                        <h4 class="${saldoClass}">${this.formatarMoeda(dados.totais.saldo)}</h4>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        html += `</div>`;

        // Inserir no modal
        $(this.selectors.modalBody).html(html);
    }

    // ================== EXPORTAÇÃO ==================

    /**
     * Exporta relatório para Excel
     */
    async exportarRelatorioExcel() {
        try {
            // Obter dados atuais
            const tipo = this.state.currentType;
            const dados = tipo === 'fonte' 
                ? this.dataCache.fonteReport 
                : this.dataCache.receitaReport;

            if (!dados || !dados.dados) {
                this.mostrarMensagem('Nenhum dado para exportar', 'warning');
                return;
            }

            // Preparar dados para Excel
            const wsData = [
                [`RELATÓRIO POR ${tipo.toUpperCase()}`],
                [`Período: ${dados.periodo.mes}/${dados.periodo.ano}`],
                [],
                [
                    'Código',
                    'Descrição',
                    'Previsão Inicial',
                    'Previsão Atualizada',
                    `Realizada ${dados.periodo.ano}`,
                    `Realizada ${dados.periodo.ano - 1}`,
                    'Variação %',
                    'Variação R$'
                ]
            ];

            // Adicionar dados
            dados.dados.forEach(item => {
                const indent = '  '.repeat(item.nivel);
                wsData.push([
                    item.codigo,
                    indent + item.descricao,
                    item.previsao_inicial,
                    item.previsao_atualizada,
                    item.receita_atual,
                    item.receita_anterior,
                    item.variacao_percentual.toFixed(2),
                    item.variacao_absoluta || 0
                ]);
            });

            // Adicionar totais
            if (dados.totais) {
                wsData.push([]);
                wsData.push([
                    'TOTAL',
                    '',
                    dados.totais.previsao_inicial,
                    dados.totais.previsao_atualizada,
                    dados.totais.receita_atual,
                    dados.totais.receita_anterior,
                    dados.totais.variacao_percentual.toFixed(2),
                    dados.totais.variacao_absoluta
                ]);
            }

            // Criar workbook
            const ws = XLSX.utils.aoa_to_sheet(wsData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, `Relatório ${tipo}`);

            // Download
            const filename = `relatorio_${tipo}_${dados.periodo.ano}_${dados.periodo.mes}.xlsx`;
            XLSX.writeFile(wb, filename);

            this.mostrarMensagem('Excel gerado com sucesso!', 'success');

        } catch (error) {
            console.error('Erro ao exportar:', error);
            this.mostrarMensagem('Erro ao gerar Excel', 'danger');
        }
    }

    /**
     * Exporta lançamentos para Excel
     */
    async exportarLancamentosExcel() {
        try {
            if (!this.dataCache.lastLancamentos) {
                this.mostrarMensagem('Nenhum lançamento para exportar', 'warning');
                return;
            }

            const $btn = $(this.selectors.btnExportLancamentos);
            const textoOriginal = $btn.html();
            
            // Mostrar loading
            $btn.prop('disabled', true)
                .html('<i class="spinner-border spinner-border-sm"></i> Gerando...');

            let dadosExcel = this.dataCache.lastLancamentos;

            // Se tem mais registros, buscar todos
            if (dadosExcel.tem_mais_registros) {
                const params = {
                    ...this.dataCache.lastLancamentosParams,
                    exportar_excel: 'true'
                };

                dadosExcel = await this.fazerRequisicao(
                    `${this.apiConfig.baseUrl}${this.apiConfig.endpoints.lancamentosExcel}`,
                    params
                );
            }

            // Preparar dados
            const wsData = [
                ['RELATÓRIO DE LANÇAMENTOS'],
                [`Total de Registros: ${dadosExcel.total_registros}`],
                [],
                ['Conta Contábil', 'UG Emitente', 'UG Contábil', 'Documento', 
                 'Evento', 'D/C', 'Data', 'Valor']
            ];

            // Adicionar lançamentos
            dadosExcel.lancamentos.forEach(lanc => {
                wsData.push([
                    lanc.conta_contabil || '',
                    lanc.ug_emitente || '',
                    lanc.ug_contabil || '',
                    lanc.documento || '',
                    lanc.evento || '',
                    lanc.dc || '',
                    lanc.data || '',
                    lanc.valor || 0
                ]);
            });

            // Adicionar totais
            if (dadosExcel.totais) {
                wsData.push([]);
                wsData.push(['TOTAIS']);
                wsData.push(['Total Débito:', '', '', '', '', '', '', dadosExcel.totais.debito]);
                wsData.push(['Total Crédito:', '', '', '', '', '', '', dadosExcel.totais.credito]);
                wsData.push(['Saldo:', '', '', '', '', '', '', dadosExcel.totais.saldo]);
            }

            // Criar e baixar Excel
            const ws = XLSX.utils.aoa_to_sheet(wsData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'Lançamentos');
            
            const filename = `lancamentos_${new Date().getTime()}.xlsx`;
            XLSX.writeFile(wb, filename);

            this.mostrarMensagem('Excel de lançamentos gerado!', 'success');

        } catch (error) {
            console.error('Erro ao exportar lançamentos:', error);
            this.mostrarMensagem('Erro ao gerar Excel', 'danger');
        } finally {
            // Restaurar botão
            $(this.selectors.btnExportLancamentos)
                .prop('disabled', false)
                .html('<i class="bi bi-file-excel"></i> Exportar Excel');
        }
    }

    // ================== AÇÕES DE INTERFACE ==================

    /**
     * Muda o tipo de relatório
     */
    mudarTipoRelatorio(tipo) {
        if (tipo === this.state.currentType) return;

        this.state.currentType = tipo;

        // Atualizar botões
        if (tipo === 'fonte') {
            $(this.selectors.btnFonte).addClass('active');
            $(this.selectors.btnReceita).removeClass('active');
        } else {
            $(this.selectors.btnFonte).removeClass('active');
            $(this.selectors.btnReceita).addClass('active');
        }

        // Limpar estados
        this.state.expandedRows.clear();

        // Carregar novo relatório
        this.carregarRelatorio(tipo);
    }

    /**
     * Alterna expansão de item
     */
    toggleItem(id) {
        const $btn = $(`.btn-toggle-rf[data-id="${id}"]`);
        const isExpanded = this.state.expandedRows.has(id);

        if (isExpanded) {
            // Recolher
            this.state.expandedRows.delete(id);
            $btn.text('▶');
            $(`tr[data-pai-id="${id}"]`).hide();
        } else {
            // Expandir
            this.state.expandedRows.add(id);
            $btn.text('▼');
            $(`tr[data-pai-id="${id}"]`).show();
        }
    }

    /**
     * Expande todos os itens
     */
    expandirTodos() {
        $('.btn-toggle-rf').each((i, btn) => {
            const id = $(btn).data('id');
            this.state.expandedRows.add(id);
            $(btn).text('▼');
        });
        $('tr[data-nivel="1"]').show();
    }

    /**
     * Recolhe todos os itens
     */
    recolherTodos() {
        this.state.expandedRows.clear();
        $('.btn-toggle-rf').text('▶');
        $('tr[data-nivel="1"]').hide();
    }

    /**
     * Aplica filtro rápido
     */
    aplicarFiltroRapido(termo) {
        const termoLower = termo.toLowerCase();
        
        $('.linha-rf').each((i, row) => {
            const $row = $(row);
            const codigo = $row.find('.codigo-rf').text().toLowerCase();
            const descricao = $row.find('.descricao-rf').text().toLowerCase();
            
            if (codigo.includes(termoLower) || descricao.includes(termoLower)) {
                $row.show();
            } else {
                $row.hide();
            }
        });
    }

    /**
     * Abre modal de lançamentos
     */
    async abrirModalLancamentos(dados) {
        // Preparar título
        const titulo = dados.tipo === 'fonte'
            ? `Lançamentos - Alínea: ${dados.codigo} - ${dados.descricao}`
            : `Lançamentos - Fonte: ${dados.codigo} - ${dados.descricao}`;

        $(this.selectors.modalTitle).html(`<i class="bi bi-list-ul"></i> ${titulo}`);

        // Mostrar loading no modal
        $(this.selectors.modalBody).html(`
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p class="mt-3 text-muted">Carregando lançamentos...</p>
            </div>
        `);

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('modalLancamentosRF'));
        modal.show();
        this.state.currentModal = modal;

        // Carregar lançamentos
        await this.carregarLancamentos(dados);
    }

    // ================== UTILITÁRIOS ==================

    /**
     * Faz requisição HTTP
     */
    async fazerRequisicao(url, params) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = `${url}?${queryString}`;

        console.log('🌐 Requisição:', fullUrl);

        const response = await fetch(fullUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(this.apiConfig.timeout)
        });

        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}`;
            
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorData.message || errorMessage;
            } catch {
                try {
                    errorMessage = await response.text() || errorMessage;
                } catch {
                    // Manter mensagem padrão
                }
            }
            
            throw new Error(errorMessage);
        }

        return await response.json();
    }

    /**
     * Formata valor monetário
     */
    formatarMoeda(valor) {
        if (valor === null || valor === undefined) return '0,00';
        
        return new Intl.NumberFormat(this.formatting.locale, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(valor);
    }

    /**
     * Formata data
     */
    formatarData(data) {
        if (!data) return '-';
        
        try {
            const [ano, mes, dia] = data.split('-');
            return `${dia}/${mes}/${ano}`;
        } catch {
            return data;
        }
    }

    /**
     * Atualiza cabeçalhos da tabela
     */
    atualizarCabecalhos(dados) {
        $('#headerTipoRF').text(
            dados.tipo === 'fonte' 
                ? 'Código de Fonte' 
                : 'Código de Receita (Alínea)'
        );
        $('.anoAtualRF').text(dados.periodo.ano);
        $('.anoAnteriorRF').text(dados.periodo.ano - 1);
    }

    /**
     * Atualiza totais da tabela
     */
    atualizarTotais(totais) {
        if (!totais) return;

        $('#totalPrevisaoInicialRF').text(this.formatarMoeda(totais.previsao_inicial));
        $('#totalPrevisaoAtualizadaRF').text(this.formatarMoeda(totais.previsao_atualizada));
        $('#totalReceitaAtualRF').text(this.formatarMoeda(totais.receita_atual));
        $('#totalReceitaAnteriorRF').text(this.formatarMoeda(totais.receita_anterior));

        const variacaoClass = totais.variacao_percentual >= 0 ? 'text-success' : 'text-danger';
        const variacaoIcon = totais.variacao_percentual >= 0 ? '↑' : '↓';
        const variacaoText = `${variacaoIcon} ${Math.abs(totais.variacao_percentual).toFixed(2)}%`;

        $('#totalVariacaoRF')
            .removeClass('text-success text-danger')
            .addClass(variacaoClass)
            .text(variacaoText);
    }

    /**
     * Atualiza status dos lançamentos
     */
    atualizarStatusLancamentos(dados) {
        let status = `${dados.total_registros} registros`;
        
        if (dados.tem_mais_registros) {
            status += ' (mostrando primeiros 1000)';
        }
        
        $('#statusLancamentosRF').text(status);
    }

    /**
     * Verifica se deve atualizar cache
     */
    shouldRefreshCache() {
        // Por enquanto, sempre usar cache se disponível
        // Pode implementar lógica de expiração aqui
        return false;
    }

    // ================== ESTADOS DE UI ==================

    /**
     * Mostra/oculta loading
     */
    mostrarLoading(show) {
        if (show) {
            $(this.selectors.loading).show();
            $(this.selectors.tableContainer).hide();
            $(this.selectors.emptyState).hide();
        } else {
            $(this.selectors.loading).hide();
        }
    }

    /**
     * Mostra tabela
     */
    mostrarTabela() {
        $(this.selectors.tableContainer).show();
        $(this.selectors.emptyState).hide();
    }

    /**
     * Mostra empty state
     */
    mostrarEmptyState() {
        $(this.selectors.tableContainer).hide();
        $(this.selectors.emptyState).show();
    }

    /**
     * Mostra mensagem de erro
     */
    mostrarErro(mensagem) {
        this.mostrarLoading(false);
        this.mostrarEmptyState();
        
        $('#emptyStateRF').html(`
            <i class="bi bi-exclamation-triangle display-4 text-danger"></i>
            <h5 class="mt-3 text-danger">Erro ao carregar dados</h5>
            <p class="text-muted">${mensagem}</p>
            <button class="btn btn-primary mt-2" onclick="location.reload()">
                <i class="bi bi-arrow-clockwise"></i> Recarregar Página
            </button>
        `);
    }

    /**
     * Mostra erro no modal
     */
    mostrarErroModal(mensagem) {
        $(this.selectors.modalBody).html(`
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle"></i>
                <strong>Erro ao carregar lançamentos</strong>
                <hr>
                ${mensagem}
                <br><br>
                <small class="text-muted">
                    Verifique os filtros e tente novamente.
                </small>
            </div>
        `);
    }

    /**
     * Mostra mensagem temporária
     */
    mostrarMensagem(texto, tipo = 'info') {
        const id = `alert-${Date.now()}`;
        const alert = `
            <div id="${id}" class="alert alert-${tipo} alert-dismissible fade show position-fixed top-0 end-0 m-3" 
                 style="z-index: 9999;" role="alert">
                ${texto}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        $('body').append(alert);

        // Auto remover após 3 segundos
        setTimeout(() => {
            $(`#${id}`).fadeOut(() => {
                $(`#${id}`).remove();
            });
        }, 3000);
    }

    // ================== MÉTODOS PÚBLICOS ==================

    /**
     * Atualiza o módulo com novos dados
     */
    atualizar(dadosRelatorio, tipoReceitaFiltro) {
        console.log('🔄 Atualizando relatório com novos filtros');
        
        // Limpar cache
        this.dataCache.fonteReport = null;
        this.dataCache.receitaReport = null;
        
        // Atualizar dados
        this.dataCache.originalData = dadosRelatorio;
        this.state.currentFilter = tipoReceitaFiltro || 'todas';
        
        // Recarregar
        this.carregarRelatorio(this.state.currentType);
    }

    /**
     * Destrói o módulo
     */
    destruir() {
        console.log('🗑️ Destruindo módulo');
        
        // Remover elementos DOM
        $(this.selectors.container).remove();
        $(this.selectors.modal).remove();
        
        // Limpar estado
        this.state = {
            isInitialized: false,
            currentType: 'fonte',
            currentFilter: 'todas',
            isLoading: false,
            expandedRows: new Set(),
            currentModal: null
        };
        
        // Limpar cache
        this.dataCache = {
            originalData: null,
            fonteReport: null,
            receitaReport: null,
            lastLancamentos: null,
            lastLancamentosParams: null
        };
    }
}

// ================== INICIALIZAÇÃO GLOBAL ==================

// Criar instância global
const relatorioReceitaFonte = new RelatorioReceitaFonteIntegrado();

// Log de inicialização
console.log('📦 Módulo RelatorioReceitaFonte v2.0 carregado');