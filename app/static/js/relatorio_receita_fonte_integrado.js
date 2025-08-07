/**
 * Módulo de Relatório Receita/Fonte Integrado ao Balanço de Receitas
 * Versão completa com suporte a lançamentos
 */

class RelatorioReceitaFonteIntegrado {
    constructor() {
        this.containerCreated = false;
        this.dadosOriginais = null;
        this.tipoAtual = 'fonte';
        this.dadosRelatorioFonte = null;
        this.dadosRelatorioReceita = null;
        this.filtroAtivo = 'todas';
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
            this.configurarEventos();
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
                                            <th class="text-center">Ações</th>
                                        </tr>
                                    </thead>
                                    <tbody id="tbodyRelatorioRF">
                                    </tbody>
                                    <tfoot>
                                        <tr class="table-secondary fw-bold">
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
                        
                        <div id="emptyStateRF" class="text-center py-5" style="display: none;">
                            <i class="bi bi-inbox display-4 text-muted"></i>
                            <h5 class="mt-3 text-muted">Nenhum dado encontrado</h5>
                            <p class="text-muted">Não há dados para os filtros selecionados</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Modal de Lançamentos -->
            <div class="modal fade" id="modalLancamentosRF" tabindex="-1">
                <div class="modal-dialog modal-xl">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="modalLancamentosRFTitle">
                                <i class="bi bi-list-ul"></i> Lançamentos
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="modalLancamentosRFBody">
                            <!-- Conteúdo será inserido dinamicamente -->
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                            <button type="button" class="btn btn-success" id="btnExportarLancamentosRF">
                                <i class="bi bi-file-earmark-excel"></i> Exportar Excel
                            </button>
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
     * Configura eventos do módulo
     */
    configurarEventos() {
        // Evento de clique nos botões de lançamentos
        $(document).on('click', '.btn-lancamentos-rf', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const $btn = $(e.currentTarget);
            const dados = {
                codigo: $btn.data('codigo'),
                descricao: $btn.data('descricao'),
                tipo: $btn.data('tipo')
            };
            
            this.mostrarModalLancamentos(dados);
        });

        // Evento de exportar lançamentos
        $('#btnExportarLancamentosRF').on('click', () => {
            this.exportarLancamentosExcel();
        });
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
            // Limpar cache ao mudar de tipo
            if (tipo === 'fonte') {
                this.dadosRelatorioFonte = null;
            } else {
                this.dadosRelatorioReceita = null;
            }
            
            // Buscar dados na API
            const params = new URLSearchParams({
                tipo: tipo,
                ano: this.dadosOriginais.periodo.ano,
                mes: this.dadosOriginais.periodo.mes,
                coug: this.dadosOriginais.filtros.coug || '',
                tipo_receita: this.filtroAtivo
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
            const tr = this.criarLinhaTabela(item, dados.tipo);
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
    criarLinhaTabela(item, tipoRelatorio) {
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
        
        // Botão de lançamentos apenas para itens de nível 1 (secundários)
        let btnLancamentos = '';
        if (item.nivel === 1 && item.receita_atual > 0) {
            btnLancamentos = `
                <button class="btn btn-sm btn-outline-primary btn-lancamentos-rf" 
                        data-codigo="${item.codigo}"
                        data-descricao="${item.descricao}"
                        data-tipo="${tipoRelatorio}"
                        title="Ver lançamentos">
                    <i class="bi bi-list-ul"></i>
                </button>
            `;
        }
        
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
                <td class="text-center">
                    ${btnLancamentos}
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
     * Mostra modal com lançamentos
     */
    async mostrarModalLancamentos(dados) {
        // Atualizar título do modal
        const titulo = dados.tipo === 'fonte' 
            ? `Lançamentos - Fonte: ${dados.codigo} - ${dados.descricao}`
            : `Lançamentos - Alínea: ${dados.codigo} - ${dados.descricao}`;
        
        $('#modalLancamentosRFTitle').html(`<i class="bi bi-list-ul"></i> ${titulo}`);
        
        // Mostrar loading
        $('#modalLancamentosRFBody').html(`
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p class="mt-2 text-muted">Carregando lançamentos...</p>
            </div>
        `);
        
        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('modalLancamentosRF'));
        modal.show();
        
        // Carregar lançamentos
        await this.carregarLancamentos(dados);
    }

    /**
     * Carrega lançamentos via API
     */
    async carregarLancamentos(dados) {
        try {
            const params = {
                ano: this.dadosOriginais.periodo.ano,
                mes: this.dadosOriginais.periodo.mes
            };

            // Adicionar parâmetros específicos baseado no tipo
            if (dados.tipo === 'fonte') {
                params.cofonte = dados.codigo;
            } else {
                params.coalinea = dados.codigo;
            }

            // Armazenar parâmetros para uso posterior
            this.ultimosParametrosLancamentos = params;
            this.ultimoTipoLancamento = dados.tipo;
            
            // Fazer requisição
            const queryString = new URLSearchParams(params).toString();
            const response = await fetch(`/balanco-receita/api/lancamentos-fonte-alinea?${queryString}`);
            
            if (!response.ok) {
                throw new Error('Erro ao carregar lançamentos');
            }
            
            const resultado = await response.json();
            
            // Renderizar lançamentos
            this.renderizarLancamentos(resultado);
            
            // Armazenar dados para exportação
            this.ultimosLancamentosCarregados = resultado;
            
        } catch (error) {
            console.error('Erro ao carregar lançamentos:', error);
            $('#modalLancamentosRFBody').html(`
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> 
                    Erro ao carregar lançamentos: ${error.message}
                </div>
            `);
        }
    }

    /**
     * Renderiza tabela de lançamentos
     */
    renderizarLancamentos(dados) {
        let html = `
            <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                <table class="table table-striped table-hover table-sm">
                    <thead class="sticky-top bg-white">
                        <tr>
                            <th>Conta Contábil</th>
                            <th>UG Emitente</th>
                            <th>UG Contábil</th>
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
                        <td>${lanc.conta_contabil || ''}</td>
                        <td>${lanc.ug_emitente || ''}</td>
                        <td>${lanc.ug_contabil || ''}</td>
                        <td>${lanc.documento || ''}</td>
                        <td>${lanc.evento || ''}</td>
                        <td class="text-center ${classDC}">${lanc.dc || ''}</td>
                        <td>${lanc.data || ''}</td>
                        <td class="text-end">${this.formatarMoeda(lanc.valor)}</td>
                    </tr>
                `;
            });
        } else {
            html += `
                <tr>
                    <td colspan="8" class="text-center text-muted">
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
                <div class="mt-3 p-3 bg-light rounded">
                    <div class="row">
                        <div class="col-md-3">
                            <strong>Total de Registros:</strong> ${dados.total_registros}
                        </div>
                        <div class="col-md-3">
                            <strong>Total Débito:</strong> 
                            <span class="text-danger">${this.formatarMoeda(dados.totais.debito)}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Total Crédito:</strong> 
                            <span class="text-success">${this.formatarMoeda(dados.totais.credito)}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>Saldo (C - D):</strong> 
                            <span class="${dados.totais.saldo >= 0 ? 'text-success' : 'text-danger'}">
                                ${this.formatarMoeda(dados.totais.saldo)}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        $('#modalLancamentosRFBody').html(html);
    }

    /**
     * Exporta lançamentos para Excel
     */
    async exportarLancamentosExcel() {
        if (!this.ultimosLancamentosCarregados) {
            alert('Nenhum dado para exportar!');
            return;
        }
        
        try {
            const dados = this.ultimosLancamentosCarregados;
            
            // Preparar dados para Excel
            const wsData = [
                ['RELATÓRIO DE LANÇAMENTOS'],
                [`Total de Registros: ${dados.total_registros}`],
                [],
                ['Conta Contábil', 'UG Emitente', 'UG Contábil', 'Nº Documento', 'Evento', 'D/C', 'Data', 'Valor']
            ];
            
            dados.lancamentos.forEach(lanc => {
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
            wsData.push([]);
            wsData.push(['TOTAIS']);
            wsData.push(['Total Débito:', '', '', '', '', '', '', dados.totais.debito || 0]);
            wsData.push(['Total Crédito:', '', '', '', '', '', '', dados.totais.credito || 0]);
            wsData.push(['Saldo (C - D):', '', '', '', '', '', '', dados.totais.saldo || 0]);
            
            // Criar workbook
            const ws = XLSX.utils.aoa_to_sheet(wsData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, 'Lançamentos');
            
            // Download
            const filename = `lancamentos_${this.ultimoTipoLancamento}_${new Date().getTime()}.xlsx`;
            XLSX.writeFile(wb, filename);
            
            this.mostrarMensagem('Arquivo Excel gerado com sucesso!', 'success');
            
        } catch (error) {
            console.error('Erro ao exportar Excel:', error);
            alert('Erro ao gerar arquivo Excel. Por favor, tente novamente.');
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
        
        // Limpar cache do tipo oposto
        if (tipo === 'fonte') {
            this.dadosRelatorioReceita = null;
        } else {
            this.dadosRelatorioFonte = null;
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
        if (!valor && valor !== 0) return '0,00';
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
    atualizar(dadosRelatorio, tipoReceitaFiltro) {
        console.log('📋 Atualizando Relatório Receita/Fonte com novos dados e filtro:', tipoReceitaFiltro);
        this.dadosOriginais = dadosRelatorio;
        this.dadosRelatorioFonte = null;
        this.dadosRelatorioReceita = null;

        // Armazena o filtro ativo para a próxima chamada de API
        this.filtroAtivo = tipoReceitaFiltro || 'todas';
        
        // Recarregar dados com os novos filtros
        this.carregarDados(this.tipoAtual);
    }

    /**
     * Destrói o módulo
     */
    destruir() {
        $('#relatorioReceitaFonteContainer').remove();
        $('#modalLancamentosRF').remove();
        this.containerCreated = false;
        this.dadosRelatorioFonte = null;
        this.dadosRelatorioReceita = null;
        this.ultimosLancamentosCarregados = null;
    }
}

// Instanciar globalmente
const relatorioReceitaFonte = new RelatorioReceitaFonteIntegrado();