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
        this.filtroAtivo = 'todas'; // Adicionado para guardar o estado do filtro
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
        
        // Pegar o filtro de tipo de receita atual
        this.filtroAtivo = $('#selectTipoReceita').val() || 'todas';
        
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
        
        // Configurar evento de clique para lançamentos
        this.configurarEventosLancamentos();
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
            // Limpar cache se mudou o filtro
            this.dadosRelatorioFonte = null;
            this.dadosRelatorioReceita = null;
            
            // Buscar dados na API
            const params = new URLSearchParams({
                tipo: tipo,
                ano: this.dadosOriginais.periodo.ano,
                mes: this.dadosOriginais.periodo.mes,
                coug: this.dadosOriginais.filtros.coug || '',
                tipo_receita: this.filtroAtivo // MODIFICADO: Enviar o filtro ativo
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
        
        // Botão de lançamentos para itens nível 1 (secundários)
        let btnLancamentos = '';
        if (item.nivel === 1 && item.tipo === 'secundario') {
            // Determinar se é fonte ou alínea baseado no tipo do relatório
            if (this.tipoAtual === 'fonte') {
                // Item principal é fonte, secundário é alínea
                btnLancamentos = `
                    <button class="btn btn-sm btn-outline-primary ms-2 btn-lancamentos-rf" 
                            data-fonte="${item.pai_id.split('-')[1]}"
                            data-alinea="${item.codigo}"
                            title="Ver lançamentos">
                        <i class="bi bi-list-ul"></i> Lançamentos
                    </button>
                `;
            } else {
                // Item principal é alínea, secundário é fonte
                btnLancamentos = `
                    <button class="btn btn-sm btn-outline-primary ms-2 btn-lancamentos-rf" 
                            data-fonte="${item.codigo}"
                            data-alinea="${item.pai_id.split('-')[1]}"
                            title="Ver lançamentos">
                        <i class="bi bi-list-ul"></i> Lançamentos
                    </button>
                `;
            }
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
                    ${btnLancamentos}
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
    atualizar(dadosRelatorio, tipoReceitaFiltro) { // MODIFICADO: Recebe o filtro
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
        this.containerCreated = false;
        this.dadosRelatorioFonte = null;
        this.dadosRelatorioReceita = null;
    }

    /**
     * Configura eventos de lançamentos
     */
    configurarEventosLancamentos() {
        $(document).on('click', '.btn-lancamentos-rf', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const $btn = $(e.currentTarget);
            const cofonte = $btn.data('fonte');
            const coalinea = $btn.data('alinea');
            
            // Obter período do relatório
            const filtros = {
                ano: this.dadosOriginais.periodo.ano,
                mes: this.dadosOriginais.periodo.mes,
                coug: this.dadosOriginais.filtros.coug || ''
            };
            
            // Dados para lançamentos (sem UG específica)
            const dadosLancamento = {
                cofontereceita: cofonte,
                coalinea: coalinea
            };
            
            // Mostrar modal de lançamentos
            this.mostrarModalLancamentos(dadosLancamento, filtros);
        });
    }

    /**
     * Mostra modal de lançamentos
     */
    mostrarModalLancamentos(dadosLancamento, filtros) {
        // Usar o mesmo modal do balanço receita
        if ($('#modalLancamentos').length === 0) {
            // Se o modal não existe, precisamos criá-lo
            this.criarModalLancamentosRF();
        }
        
        // Atualizar título do modal
        $('#modalLancamentos .modal-title').html(
            `<div>
                <i class="bi bi-list-ul"></i> Lançamentos - Fonte/Receita
                <br>
                <small class="text-muted">Fonte: ${dadosLancamento.cofontereceita} | Alínea: ${dadosLancamento.coalinea}</small>
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
        this.carregarLancamentosFonteAlinea(dadosLancamento, filtros);
    }

    /**
     * Cria modal de lançamentos (se não existir)
     */
    criarModalLancamentosRF() {
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
    }

    /**
     * Carrega lançamentos por fonte e alínea
     */
    async carregarLancamentosFonteAlinea(dadosLancamento, filtros) {
        try {
            const parametros = {
                ano: filtros.ano,
                mes: filtros.mes,
                cofontereceita: dadosLancamento.cofontereceita,
                coalinea: dadosLancamento.coalinea
            };
            
            const response = await $.ajax({
                url: '/balanco-receita/api/lancamentos-fonte-alinea',
                method: 'GET',
                data: parametros
            });
            
            // Renderizar tabela adaptada
            this.renderizarTabelaLancamentosRF(response);
            
            // Armazenar dados para exportação
            window.ultimosLancamentosCarregados = response;
            
        } catch (error) {
            console.error('Erro ao carregar lançamentos:', error);
            $('#modalLancamentosBody').html(`
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> 
                    Erro ao carregar lançamentos: ${error.message || 'Erro desconhecido'}
                </div>
            `);
        }
    }

    /**
     * Renderiza tabela de lançamentos adaptada para fonte/alínea
     */
    renderizarTabelaLancamentosRF(dados) {
        let html = `
            <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                <table class="table table-striped table-hover table-lancamentos">
                    <thead>
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
                        <td>${lanc.conta_contabil}</td>
                        <td>${lanc.ug_emitente}</td>
                        <td>${lanc.ug_contabil}</td>
                        <td>${lanc.documento}</td>
                        <td>${lanc.evento}</td>
                        <td class="text-center ${classDC}">${lanc.dc}</td>
                        <td>${lanc.data}</td>
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
                <div class="totais-lancamentos">
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
}

// Instanciar globalmente
const relatorioReceitaFonte = new RelatorioReceitaFonteIntegrado();