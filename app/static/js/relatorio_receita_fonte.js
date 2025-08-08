// JavaScript para Relatório Detalhado por Fonte/Receita
// PARTE 1 - CORRIGIDA
//
console.log('Arquivo relatorio_receita_fonte.js carregado');

// ========================================
// VARIÁVEIS GLOBAIS
// ========================================
let dadosAtuais = [];
let totaisGerais = {};
let modoAtual = 'fonte';
let tabelaDados = null;
let dadosLancamentosCompletos = [];
let dadosInconsistencias = [];
let ultimaVerificacao = null;

// ========================================
// INICIALIZAÇÃO
// ========================================
$(document).ready(function() {
    console.log('Document ready - iniciando carregamento dos dados');
    configurarEventos();
    configurarEventosInconsistencias();
    carregarListaUGs();
    carregarEstatisticasInconsistencias();
});

// ========================================
// CONFIGURAÇÃO DE EVENTOS
// ========================================
function configurarEventos() {
    // Mudança de UG
    $('#filtroUG').on('change', function() {
        const ugSelecionada = $(this).val();
        const textoUG = ugSelecionada ? $('#filtroUG option:selected').text() : 'Consolidado';
        $('#badgeUGSelecionada').text(textoUG);
        console.log('UG alterada para:', ugSelecionada || 'Consolidado');
        carregarDados();
    });
    
    // Mudança de modo de visualização
    $('input[name="modoVisualizacao"]').on('change', function() {
        modoAtual = $(this).val();
        console.log('Modo alterado para:', modoAtual);
        carregarDados();
    });
    
    // Mudança de tipo de exibição
    $('#tipoExibicao').on('change', function() {
        atualizarExibicao();
    });
    
    // Toggle nomes completos
    $('#mostrarNomesCompletos').on('change', function() {
        const mostrarCompleto = $(this).is(':checked');
        if (mostrarCompleto) {
            $('#tabelaDados td:first-child, #tabelaDados th:first-child').css({
                'white-space': 'normal',
                'word-break': 'break-word',
                'max-width': 'none'
            });
        } else {
            $('#tabelaDados td:first-child, #tabelaDados th:first-child').css({
                'white-space': 'nowrap',
                'word-break': 'normal',
                'max-width': '500px'
            });
        }
    });
    
    // Botões de ação
    $('#btnExpandirTodos').on('click', expandirTodos);
    $('#btnRecolherTodos').on('click', recolherTodos);
    $('#btnAtualizar').on('click', carregarDados);
    $('#btnExportar').on('click', exportarExcel);
    
    // Fechar modal
    $('#btnFecharModal').on('click', function() {
        $('#modalDetalhes').modal('hide');
    });
    
    // Exportar detalhes do modal
    $('#btnExportarDetalhes').on('click', exportarDetalhesExcel);
}

function configurarEventosInconsistencias() {
    // Botão principal de verificação
    $('#btnVerificarInconsistencias').on('click', function() {
        $('#modalInconsistencias').modal('show');
        verificarInconsistencias();
    });
    
    // Botão atualizar dentro da modal
    $('#btnAtualizarInconsistencias').on('click', verificarInconsistencias);
    
    // Exportar inconsistências
    $('#btnExportarInconsistencias').on('click', exportarInconsistencias);
}

// ========================================
// FUNÇÕES DE CARREGAMENTO DE DADOS
// ========================================
function carregarListaUGs() {
    console.log('Carregando lista de UGs...');
    
    $.ajax({
        url: '/relatorio-receita-fonte/api/lista-ugs',
        method: 'GET',
        success: function(response) {
            console.log('✅ Lista de UGs carregada:', response.total, 'UGs');
            
            $('#filtroUG').html('<option value="">Consolidado (Todas as UGs)</option>');
            
            response.ugs.forEach(function(ug) {
                const option = $('<option></option>')
                    .attr('value', ug.coug)
                    .text(ug.coug + ' - ' + ug.noug);
                $('#filtroUG').append(option);
            });
            
            const label = $('label[for="filtroUG"]');
            label.html('Unidade Gestora (UG): <span class="badge bg-secondary">' + response.total + ' UGs disponíveis</span>');
            
            carregarDados();
        },
        error: function(xhr) {
            console.error('❌ Erro ao carregar lista de UGs:', xhr);
            carregarDados();
        }
    });
}

function carregarDados() {
    console.log('Carregando dados - Modo:', modoAtual);
    
    const ugSelecionada = $('#filtroUG').val();
    console.log('UG selecionada:', ugSelecionada || 'Consolidado');
    
    $('#divTabela').html('<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div></div>');
    
    const url = modoAtual === 'fonte' 
        ? '/relatorio-receita-fonte/api/dados-por-fonte'
        : '/relatorio-receita-fonte/api/dados-por-receita';
    
    const params = ugSelecionada ? { coug: ugSelecionada } : {};
    
    $.ajax({
        url: url,
        method: 'GET',
        data: params,
        success: function(response) {
            console.log('✅ Dados carregados:', response);
            
            dadosAtuais = response.dados;
            totaisGerais = response.totais;
            
            $('#anoAtual').text(response.ano_atual);
            
            atualizarCards();
            construirTabela();
            
            $('#tituloModo').text(modoAtual === 'fonte' ? 'por Fonte' : 'por Receita');
            $('#badgeRegistros').text(dadosAtuais.length + ' registros principais');
        },
        error: function(xhr) {
            console.error('❌ Erro ao carregar dados:', xhr);
            
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            $('#divTabela').html('<div class="alert alert-danger" role="alert"><i class="bi bi-exclamation-triangle"></i> Erro ao carregar dados: ' + erro + '</div>');
        }
    });
}

function atualizarCards() {
    $('#totalPrevisaoInicial').text(formatarMoeda(totaisGerais.previsao_inicial));
    $('#totalPrevisaoAtualizada').text(formatarMoeda(totaisGerais.previsao_atualizada));
    $('#totalRealizadaAtual').text(formatarMoeda(totaisGerais.realizada_atual));
    
    const variacao = totaisGerais.variacao_percentual || 0;
    const variacaoFormatada = Math.abs(variacao).toFixed(2) + '%';
    
    let htmlVariacao = '';
    if (variacao > 0) {
        htmlVariacao = '<span class="text-success">↑ ' + variacaoFormatada + '</span>';
    } else if (variacao < 0) {
        htmlVariacao = '<span class="text-danger">↓ ' + variacaoFormatada + '</span>';
    } else {
        htmlVariacao = '<span class="text-muted">→ ' + variacaoFormatada + '</span>';
    }
    
    $('#totalVariacao').html(htmlVariacao);
}

// ========================================
// FUNÇÕES DE CONSTRUÇÃO DE TABELA
// ========================================
function construirTabela() {
    if (!dadosAtuais || dadosAtuais.length === 0) {
        $('#divTabela').html('<p class="text-center text-muted py-3">Nenhum dado encontrado.</p>');
        return;
    }
    
    if (tabelaDados) {
        tabelaDados.destroy();
        $('#divTabela').empty();
    }
    
    let html = '<table id="tabelaDados" class="table table-hover">';
    
    html += '<thead class="table-light">';
    html += '<tr>';
    html += '<th style="width: 30%">' + (modoAtual === 'fonte' ? 'Fonte / Alínea' : 'Alínea / Fonte') + '</th>';
    html += '<th class="text-end">Previsão Inicial</th>';
    html += '<th class="text-end">Previsão Atualizada</th>';
    html += '<th class="text-end">Realizada ' + $('#anoAtual').text() + '</th>';
    html += '<th class="text-end">Realizada ' + (parseInt($('#anoAtual').text()) - 1) + '</th>';
    html += '<th class="text-end">Variação R$</th>';
    html += '<th class="text-end">Variação %</th>';
    html += '<th class="text-center">Ações</th>';
    html += '</tr>';
    html += '</thead>';
    
    html += '<tbody>';
    
    dadosAtuais.forEach(function(item, index) {
        const itemId = modoAtual === 'fonte' ? item.cofonte : item.coalinea;
        const itemNome = modoAtual === 'fonte' ? item.nome_fonte : item.nome_alinea;
        const subitens = modoAtual === 'fonte' ? item.alineas : item.fontes;
        
        if (subitens && subitens.length > 0) {
            subitens.sort((a, b) => b.realizada_atual - a.realizada_atual);
        }
        
        html += '<tr class="linha-principal" data-id="' + itemId + '">';
        html += '<td class="text-nowrap">';
        html += '<button class="btn btn-sm btn-link btn-expandir" data-target="' + itemId + '">';
        html += '<i class="bi bi-chevron-right"></i>';
        html += '</button> ';
        html += '<strong>' + formatarCodigoDescricao(itemId, itemNome) + '</strong>';
        html += ' <span class="badge bg-secondary">' + (subitens ? subitens.length : 0) + '</span>';
        html += '</td>';
        html += '<td class="text-end">' + formatarMoeda(item.previsao_inicial) + '</td>';
        html += '<td class="text-end">' + formatarMoeda(item.previsao_atualizada) + '</td>';
        html += '<td class="text-end">' + formatarMoeda(item.realizada_atual) + '</td>';
        html += '<td class="text-end">' + formatarMoeda(item.realizada_anterior) + '</td>';
        html += '<td class="text-end ' + getClasseVariacao(item.variacao_absoluta) + '">';
        html += formatarMoeda(item.variacao_absoluta);
        html += '</td>';
        html += '<td class="text-end ' + getClasseVariacao(item.variacao_percentual) + '">';
        html += formatarVariacaoPercentual(item.variacao_percentual);
        html += '</td>';
        html += '<td></td>';
        html += '</tr>';
        
        if (subitens && subitens.length > 0) {
            subitens.forEach(function(subitem) {
                const subitemId = modoAtual === 'fonte' ? subitem.coalinea : subitem.cofonte;
                const subitemNome = modoAtual === 'fonte' ? subitem.nome_alinea : subitem.nome_fonte;
                
                html += '<tr class="linha-filha collapse-' + itemId + '" style="display: none;">';
                html += '<td class="ps-5 text-nowrap">';
                html += '<span class="text-muted">└─</span> ' + formatarCodigoDescricao(subitemId, subitemNome);
                html += '</td>';
                html += '<td class="text-end">' + formatarMoeda(subitem.previsao_inicial) + '</td>';
                html += '<td class="text-end">' + formatarMoeda(subitem.previsao_atualizada) + '</td>';
                html += '<td class="text-end">' + formatarMoeda(subitem.realizada_atual) + '</td>';
                html += '<td class="text-end">' + formatarMoeda(subitem.realizada_anterior) + '</td>';
                html += '<td class="text-end ' + getClasseVariacao(subitem.variacao_absoluta) + '">';
                html += formatarMoeda(subitem.variacao_absoluta);
                html += '</td>';
                html += '<td class="text-end ' + getClasseVariacao(subitem.variacao_percentual) + '">';
                html += formatarVariacaoPercentual(subitem.variacao_percentual);
                html += '</td>';
                html += '<td class="text-center">';
                
                if (modoAtual === 'fonte') {
                    html += '<button class="btn btn-sm btn-outline-primary btn-detalhes" ';
                    html += 'data-cofonte="' + itemId + '" ';
                    html += 'data-coalinea="' + subitemId + '" ';
                    html += 'data-nome-fonte="' + (itemNome || '') + '" ';
                    html += 'data-nome-alinea="' + (subitemNome || '') + '">';
                } else {
                    html += '<button class="btn btn-sm btn-outline-primary btn-detalhes" ';
                    html += 'data-cofonte="' + subitemId + '" ';
                    html += 'data-coalinea="' + itemId + '" ';
                    html += 'data-nome-fonte="' + (subitemNome || '') + '" ';
                    html += 'data-nome-alinea="' + (itemNome || '') + '">';
                }
                html += '<i class="bi bi-eye"></i> Detalhes';
                html += '</button>';
                html += '</td>';
                html += '</tr>';
            });
        }
    });
    
    html += '</tbody>';
    
    html += '<tfoot class="table-light">';
    html += '<tr class="fw-bold">';
    html += '<td>TOTAL GERAL</td>';
    html += '<td class="text-end">' + formatarMoeda(totaisGerais.previsao_inicial) + '</td>';
    html += '<td class="text-end">' + formatarMoeda(totaisGerais.previsao_atualizada) + '</td>';
    html += '<td class="text-end">' + formatarMoeda(totaisGerais.realizada_atual) + '</td>';
    html += '<td class="text-end">' + formatarMoeda(totaisGerais.realizada_anterior) + '</td>';
    html += '<td class="text-end ' + getClasseVariacao(totaisGerais.variacao_absoluta) + '">';
    html += formatarMoeda(totaisGerais.variacao_absoluta);
    html += '</td>';
    html += '<td class="text-end ' + getClasseVariacao(totaisGerais.variacao_percentual) + '">';
    html += formatarVariacaoPercentual(totaisGerais.variacao_percentual);
    html += '</td>';
    html += '<td></td>';
    html += '</tr>';
    html += '</tfoot>';
    
    html += '</table>';
    
    $('#divTabela').html(html);
    
    $('.btn-expandir').on('click', function() {
        const target = $(this).data('target');
        const icon = $(this).find('i');
        const linhasFilhas = $('.collapse-' + target);
        
        if (linhasFilhas.is(':visible')) {
            linhasFilhas.hide();
            icon.removeClass('bi-chevron-down').addClass('bi-chevron-right');
        } else {
            linhasFilhas.show();
            icon.removeClass('bi-chevron-right').addClass('bi-chevron-down');
        }
    });
    
    $('.btn-detalhes').on('click', function() {
        const cofonte = $(this).data('cofonte');
        const coalinea = $(this).data('coalinea');
        const nomeFonte = $(this).data('nome-fonte');
        const nomeAlinea = $(this).data('nome-alinea');
        
        console.log('Ver detalhes - Fonte:', cofonte, 'Alínea:', coalinea);
        abrirModalDetalhes(cofonte, coalinea, nomeFonte, nomeAlinea);
    });
}

// ========================================
// FUNÇÕES DE MODAL DE DETALHES
// ========================================
function abrirModalDetalhes(cofonte, coalinea, nomeFonte, nomeAlinea) {
    $('#tabelaDetalhes tbody').html('<tr><td colspan="7" class="text-center"><div class="spinner-border spinner-border-sm"></div> Carregando...</td></tr>');
    $('#alertaLimite').hide();
    
    const titulo = `Detalhes dos Lançamentos<br>
                   <small class="text-muted">
                   Fonte: ${cofonte} - ${nomeFonte || 'Sem descrição'}<br>
                   Alínea: ${coalinea} - ${nomeAlinea || 'Sem descrição'}
                   </small>`;
    $('#modalDetalhesLabel').html(titulo);
    
    $('#modalDetalhes').modal('show');
    
    const ano = $('#anoAtual').text();
    const coug = $('#filtroUG').val();
    
    const params = {
        cofonte: cofonte,
        coalinea: coalinea,
        ano: ano
    };
    
    if (coug) {
        params.coug = coug;
    }
    
    $.ajax({
        url: '/relatorio-receita-fonte/api/detalhes-lancamentos',
        method: 'GET',
        data: params,
        success: function(response) {
            console.log('✅ Detalhes carregados:', response);
            
            dadosLancamentosCompletos = response;
            
            $('#resumoTotalDebito').text(formatarMoeda(response.total_debito));
            $('#resumoTotalCredito').text(formatarMoeda(response.total_credito));
            $('#resumoSaldo').text(formatarMoeda(response.saldo));
            $('#resumoTotalRegistros').text(response.total_registros.toLocaleString('pt-BR'));
            
            if (response.limitado) {
                $('#alertaLimite').show();
                $('#textoLimite').html(`
                    <i class="bi bi-info-circle"></i> 
                    Exibindo apenas os primeiros 1.000 registros de um total de ${response.total_registros.toLocaleString('pt-BR')}.
                    <br>Para obter todos os registros, use o botão "Exportar Excel" abaixo.
                `);
            }
            
            construirTabelaDetalhes(response.dados);
        },
        error: function(xhr) {
            console.error('❌ Erro ao carregar detalhes:', xhr);
            
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            $('#tabelaDetalhes tbody').html(
                '<tr><td colspan="7" class="text-center text-danger">' +
                '<i class="bi bi-exclamation-triangle"></i> Erro ao carregar dados: ' + erro +
                '</td></tr>'
            );
        }
    });
}

function construirTabelaDetalhes(dados) {
    if (!dados || dados.length === 0) {
        $('#tabelaDetalhes tbody').html('<tr><td colspan="7" class="text-center text-muted">Nenhum lançamento encontrado.</td></tr>');
        return;
    }
    
    let html = '';
    
    dados.forEach(function(item, index) {
        html += '<tr>';
        html += '<td class="text-nowrap">' + item.cocontacontabil + 
                (item.nocontacontabil ? '<br><small class="text-muted">' + item.nocontacontabil + '</small>' : '') + '</td>';
        html += '<td class="text-nowrap">' + item.coug + 
                (item.noug ? '<br><small class="text-muted">' + item.noug + '</small>' : '') + '</td>';
        html += '<td>' + item.nudocumento + '</td>';
        html += '<td class="text-nowrap">' + item.coevento + 
                (item.noevento ? '<br><small class="text-muted">' + item.noevento + '</small>' : '') + '</td>';
        html += '<td class="text-center">' + (item.cogrupo || '-') + '</td>';
        html += '<td class="text-center">';
        if (item.indebitocredito === 'D') {
            html += '<span class="badge bg-danger">D</span>';
        } else {
            html += '<span class="badge bg-success">C</span>';
        }
        html += '</td>';
        html += '<td class="text-end">' + formatarMoeda(item.valancamento) + '</td>';
        html += '</tr>';
    });
    
    $('#tabelaDetalhes tbody').html(html);
}

// ========================================
// FUNÇÕES DE INCONSISTÊNCIAS
// ========================================
function carregarEstatisticasInconsistencias() {
    $.ajax({
        url: '/relatorio-receita-fonte/api/estatisticas-inconsistencias',
        method: 'GET',
        success: function(response) {
            if (response.total > 0) {
                $('#badgeInconsistencias').text(response.total).show();
                $('#btnVerificarInconsistencias').removeClass('btn-warning').addClass('btn-danger');
            } else {
                $('#badgeInconsistencias').hide();
            }
        },
        error: function(xhr) {
            console.error('Erro ao carregar estatísticas de inconsistências:', xhr);
        }
    });
}

function verificarInconsistencias() {
    $('#loadingInconsistencias').show();
    $('#tabelaInconsistencias tbody').empty();
    $('#statusVerificacao').html('<span class="badge bg-info">Verificando...</span>');
    
    $.ajax({
        url: '/relatorio-receita-fonte/api/verificar-inconsistencias',
        method: 'GET',
        data: {
            exportar: 'false'
        },
        success: function(response) {
            console.log('✅ Inconsistências verificadas:', response);
            
            dadosInconsistencias = response.documentos;
            ultimaVerificacao = new Date();
            
            // Atualizar cards
            $('#totalDocumentos').text(response.totais.total_documentos.toLocaleString('pt-BR'));
            $('#totalCombinacoes').text(response.totais.total_combinacoes);
            $('#valorTotalInconsistente').text(formatarMoeda(response.totais.valor_total));
            
            // Atualizar badge na tab
            $('#badgeFonteAlinea').text(response.totais.total_documentos);
            
            // Atualizar status
            if (response.totais.total_documentos === 0) {
                $('#statusVerificacao').html('<span class="badge bg-success">✓ Nenhuma inconsistência</span>');
            } else {
                $('#statusVerificacao').html('<span class="badge bg-danger">⚠ ' + response.totais.total_documentos + ' documentos com problemas</span>');
            }
            
            // Construir tabela
            construirTabelaInconsistencias(dadosInconsistencias);
            
            // Atualizar texto de última verificação
            $('#textoUltimaVerificacao').text('Última verificação: ' + ultimaVerificacao.toLocaleString('pt-BR'));
            
            // Mostrar alerta se dados foram limitados
            if (response.filtros.limitado) {
                mostrarAlerta('info', 
                    `Exibindo apenas os primeiros ${response.totais.total_exibido} documentos de um total de ${response.totais.total_documentos}. 
                     Para ver todos, use o botão "Exportar".`
                );
            }
            
            $('#loadingInconsistencias').hide();
        },
        error: function(xhr) {
            console.error('❌ Erro ao verificar inconsistências:', xhr);
            
            $('#loadingInconsistencias').hide();
            $('#statusVerificacao').html('<span class="badge bg-danger">Erro na verificação</span>');
            
            mostrarAlerta('danger', 'Erro ao verificar inconsistências: ' + (xhr.responseJSON?.erro || 'Erro desconhecido'));
        }
    });
}

function construirTabelaInconsistencias(dados) {
    const tbody = $('#tabelaInconsistencias tbody');
    tbody.empty();
    
    if (!dados || dados.length === 0) {
        tbody.html(`
            <tr>
                <td colspan="9" class="text-center text-success">
                    <i class="bi bi-check-circle"></i> Nenhuma inconsistência encontrada
                </td>
            </tr>
        `);
        return;
    }
    
    dados.forEach(function(item, index) {
        // Determinar cor baseado no valor
        let classeSeveridade = '';
        const valor = Math.abs(item.valancamento);
        if (valor > 100000) {
            classeSeveridade = 'table-warning';
        }
        
        const row = $('<tr>').addClass(classeSeveridade);
        
        row.html(`
            <td><strong>${item.nudocumento}</strong></td>
            <td>
                ${item.cougcontab}
                ${item.noug ? '<br><small class="text-muted">' + item.noug + '</small>' : ''}
            </td>
            <td>
                ${item.coevento || ''}
                ${item.noevento ? '<br><small class="text-muted">' + item.noevento.substring(0, 20) + '...</small>' : ''}
            </td>
            <td>
                ${item.cofonte}
                ${item.nofonte ? '<br><small class="text-muted">' + item.nofonte.substring(0, 20) + '...</small>' : ''}
            </td>
            <td>
                ${item.coalinea}
                ${item.noalinea ? '<br><small class="text-muted">' + item.noalinea.substring(0, 20) + '...</small>' : ''}
            </td>
            <td>${item.dalancamento ? new Date(item.dalancamento).toLocaleDateString('pt-BR') : ''}</td>
            <td class="text-center">
                <span class="badge ${item.indebitocredito === 'D' ? 'bg-danger' : 'bg-success'}">
                    ${item.indebitocredito}
                </span>
            </td>
            <td class="text-end">
                <strong class="${item.indebitocredito === 'D' ? 'text-danger' : 'text-success'}">
                    ${item.indebitocredito === 'D' ? '-' : '+'} ${formatarMoeda(Math.abs(item.valancamento))}
                </strong>
            </td>
            <td class="text-center">
                <button class="btn btn-sm btn-outline-primary" 
                        onclick="verDetalhesInconsistencia('${item.cofonte}', '${item.coalinea}')"
                        title="Ver todos desta combinação">
                    <i class="bi bi-search"></i>
                </button>
            </td>
        `);
        
        tbody.append(row);
    });
}

// ========================================
// CONTINUAÇÃO - PARTE 2 CORRIGIDA
// ========================================

function verDetalhesInconsistencia(cofonte, coalinea) {
    $('#modalInconsistencias').modal('hide');
    
    const item = dadosInconsistencias.find(i => i.cofonte === cofonte && i.coalinea === coalinea);
    
    if (item) {
        abrirModalDetalhes(cofonte, coalinea, item.nofonte, item.noalinea);
    }
}

function exportarInconsistencias() {
    console.log('📊 Exportando inconsistências...');
    
    const btnOriginal = $('#btnExportarInconsistencias').html();
    $('#btnExportarInconsistencias').html('<span class="spinner-border spinner-border-sm"></span> Exportando...');
    $('#btnExportarInconsistencias').prop('disabled', true);
    
    $.ajax({
        url: '/relatorio-receita-fonte/api/verificar-inconsistencias',
        method: 'GET',
        data: {
            exportar: 'true'
        },
        success: function(response) {
            console.log('✅ Dados completos para exportação');
            
            let csv = [];
            
            csv.push(['RELATÓRIO DE INCONSISTÊNCIAS - FONTE/ALÍNEA NÃO CADASTRADAS'].join(';'));
            csv.push(['Data da verificação: ' + new Date().toLocaleString('pt-BR')].join(';'));
            csv.push(['Exercício: ' + new Date().getFullYear()].join(';'));
            csv.push('');
            
            csv.push(['RESUMO'].join(';'));
            csv.push(['Total de Documentos Inconsistentes;' + response.totais.total_documentos].join(''));
            csv.push(['Total de Combinações Inválidas;' + response.totais.total_combinacoes].join(''));
            csv.push(['Valor Total Envolvido;' + response.totais.valor_total.toFixed(2).replace('.', ',')].join(''));
            csv.push('');
            
            const headers = [
                'Documento',
                'UG Contábil',
                'Nome UG',
                'Código Fonte',
                'Nome Fonte',
                'Código Alínea',
                'Nome Alínea',
                'Data Lançamento',
                'D/C',
                'Valor'
            ];
            csv.push(headers.join(';'));
            
            response.documentos.forEach(function(item) {
                let linha = [
                    item.nudocumento,
                    item.cougcontab || '',
                    item.noug || '',
                    item.cofonte,
                    item.nofonte || '',
                    item.coalinea,
                    item.noalinea || '',
                    item.dalancamento ? new Date(item.dalancamento).toLocaleDateString('pt-BR') : '',
                    item.indebitocredito || '',
                    Math.abs(item.valancamento).toFixed(2).replace('.', ',')
                ];
                csv.push(linha.join(';'));
            });
            
            let csvContent = '\ufeff' + csv.join('\n');
            let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            let link = document.createElement('a');
            let url = URL.createObjectURL(blob);
            
            const filename = 'inconsistencias_fonte_alinea_' + new Date().getTime() + '.csv';
            
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log('✅ Exportação concluída:', filename);
            
            $('#btnExportarInconsistencias').html(btnOriginal);
            $('#btnExportarInconsistencias').prop('disabled', false);
        },
        error: function(xhr) {
            console.error('❌ Erro ao exportar:', xhr);
            alert('Erro ao exportar dados. Tente novamente.');
            
            $('#btnExportarInconsistencias').html(btnOriginal);
            $('#btnExportarInconsistencias').prop('disabled', false);
        }
    });
}

// ========================================
// FUNÇÕES DE EXPORTAÇÃO
// ========================================
function exportarDetalhesExcel() {
    if (!dadosLancamentosCompletos || !dadosLancamentosCompletos.cofonte) {
        alert('Não há dados para exportar!');
        return;
    }
    
    console.log('📊 Exportando detalhes completos...');
    
    const btnOriginal = $('#btnExportarDetalhes').html();
    $('#btnExportarDetalhes').html('<span class="spinner-border spinner-border-sm"></span> Baixando todos os dados...');
    $('#btnExportarDetalhes').prop('disabled', true);
    
    const coug = $('#filtroUG').val();
    
    const params = {
        cofonte: dadosLancamentosCompletos.cofonte,
        coalinea: dadosLancamentosCompletos.coalinea,
        ano: dadosLancamentosCompletos.ano,
        exportar: 'true'
    };
    
    if (coug) {
        params.coug = coug;
    }
    
    $.ajax({
        url: '/relatorio-receita-fonte/api/detalhes-lancamentos',
        method: 'GET',
        data: params,
        success: function(response) {
            console.log('✅ Dados completos carregados para exportação');
            
            let csv = [];
            
            csv.push(['RELATÓRIO DE DETALHES DE LANÇAMENTOS'].join(';'));
            csv.push(['Fonte: ' + response.cofonte + ' - ' + response.nome_fonte].join(';'));
            csv.push(['Alínea: ' + response.coalinea + ' - ' + response.nome_alinea].join(';'));
            csv.push(['Ano: ' + response.ano].join(';'));
            csv.push(['Total de Registros: ' + response.total_registros].join(';'));
            csv.push('');
            
            csv.push(['RESUMO'].join(';'));
            csv.push(['Total Débito;' + response.total_debito.toFixed(2).replace('.', ',')].join(''));
            csv.push(['Total Crédito;' + response.total_credito.toFixed(2).replace('.', ',')].join(''));
            csv.push(['Saldo;' + response.saldo.toFixed(2).replace('.', ',')].join(''));
            csv.push('');
            
            const headers = [
                'Conta Contábil',
                'Descrição Conta',
                'UG Emitente',
                'Nome UG',
                'Documento',
                'Evento',
                'Descrição Evento',
                'Data Lançamento',
                'D/C',
                'Valor',
                'Grupo'
            ];
            csv.push(headers.join(';'));
            
            response.dados.forEach(function(item) {
                let linha = [
                    item.cocontacontabil,
                    item.nocontacontabil || '',
                    item.coug,
                    item.noug || '',
                    item.nudocumento,
                    item.coevento,
                    item.noevento || '',
                    item.dalancamento || '',
                    item.indebitocredito,
                    item.valancamento.toFixed(2).replace('.', ','),
                    item.cogrupo || ''
                ];
                csv.push(linha.join(';'));
            });
            
            csv.push('');
            csv.push(['Data da exportação: ' + new Date().toLocaleString('pt-BR')].join(';'));
            
            let csvContent = '\ufeff' + csv.join('\n');
            let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            let link = document.createElement('a');
            let url = URL.createObjectURL(blob);
            
            const filename = 'detalhes_lancamentos_' + response.cofonte + '_' + response.coalinea + '_' + new Date().getTime() + '.csv';
            
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log('✅ Exportação concluída:', filename);
            
            $('#btnExportarDetalhes').html(btnOriginal);
            $('#btnExportarDetalhes').prop('disabled', false);
        },
        error: function(xhr) {
            console.error('❌ Erro ao exportar:', xhr);
            alert('Erro ao exportar dados. Tente novamente.');
            
            $('#btnExportarDetalhes').html(btnOriginal);
            $('#btnExportarDetalhes').prop('disabled', false);
        }
    });
}

function exportarExcel() {
    if (!dadosAtuais || dadosAtuais.length === 0) {
        alert('Não há dados para exportar!');
        return;
    }
    
    console.log('📊 Exportando dados...');
    
    let csv = [];
    const tipoExibicao = $('#tipoExibicao').val();
    const ugSelecionada = $('#filtroUG').val();
    const textoUG = ugSelecionada ? $('#filtroUG option:selected').text() : 'Consolidado (Todas as UGs)';
    
    csv.push(['RELATÓRIO DETALHADO POR ' + (modoAtual === 'fonte' ? 'FONTE' : 'RECEITA')].join(';'));
    csv.push(['UG: ' + textoUG].join(';'));
    csv.push('');
    
    const headers = [
        modoAtual === 'fonte' ? 'Fonte' : 'Alínea',
        modoAtual === 'fonte' ? 'Alínea' : 'Fonte',
        'Previsão Inicial',
        'Previsão Atualizada',
        'Realizada ' + $('#anoAtual').text(),
        'Realizada ' + (parseInt($('#anoAtual').text()) - 1),
        'Variação R$',
        'Variação %'
    ];
    csv.push(headers.join(';'));
    
    dadosAtuais.forEach(function(item) {
        const itemId = modoAtual === 'fonte' ? item.cofonte : item.coalinea;
        const itemNome = modoAtual === 'fonte' ? item.nome_fonte : item.nome_alinea;
        const subitens = modoAtual === 'fonte' ? item.alineas : item.fontes;
        
        let linha = [
            formatarParaExport(itemId, itemNome, tipoExibicao),
            'TOTAL',
            item.previsao_inicial.toFixed(2).replace('.', ','),
            item.previsao_atualizada.toFixed(2).replace('.', ','),
            item.realizada_atual.toFixed(2).replace('.', ','),
            item.realizada_anterior.toFixed(2).replace('.', ','),
            item.variacao_absoluta.toFixed(2).replace('.', ','),
            item.variacao_percentual.toFixed(2).replace('.', ',')
        ];
        csv.push(linha.join(';'));
        
        if (subitens && subitens.length > 0) {
            subitens.forEach(function(subitem) {
                const subitemId = modoAtual === 'fonte' ? subitem.coalinea : subitem.cofonte;
                const subitemNome = modoAtual === 'fonte' ? subitem.nome_alinea : subitem.nome_fonte;
                
                let subLinha = [
                    '',
                    formatarParaExport(subitemId, subitemNome, tipoExibicao),
                    subitem.previsao_inicial.toFixed(2).replace('.', ','),
                    subitem.previsao_atualizada.toFixed(2).replace('.', ','),
                    subitem.realizada_atual.toFixed(2).replace('.', ','),
                    subitem.realizada_anterior.toFixed(2).replace('.', ','),
                    subitem.variacao_absoluta.toFixed(2).replace('.', ','),
                    subitem.variacao_percentual.toFixed(2).replace('.', ',')
                ];
                csv.push(subLinha.join(';'));
            });
        }
    });
    
    csv.push('');
    let linhaTotal = [
        'TOTAL GERAL',
        '',
        totaisGerais.previsao_inicial.toFixed(2).replace('.', ','),
        totaisGerais.previsao_atualizada.toFixed(2).replace('.', ','),
        totaisGerais.realizada_atual.toFixed(2).replace('.', ','),
        totaisGerais.realizada_anterior.toFixed(2).replace('.', ','),
        (totaisGerais.variacao_absoluta || 0).toFixed(2).replace('.', ','),
        (totaisGerais.variacao_percentual || 0).toFixed(2).replace('.', ',')
    ];
    csv.push(linhaTotal.join(';'));
    
    csv.push('');
    csv.push(['Relatório Detalhado por ' + (modoAtual === 'fonte' ? 'Fonte' : 'Receita')].join(';'));
    csv.push(['Data da exportação: ' + new Date().toLocaleString('pt-BR')].join(';'));
    
    let csvContent = '\ufeff' + csv.join('\n');
    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    
    const filename = 'relatorio_' + modoAtual + '_' + new Date().getTime() + '.csv';
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('✅ Exportação concluída:', filename);
}

// ========================================
// FUNÇÕES AUXILIARES
// ========================================
function expandirTodos() {
    $('.linha-filha').show();
    $('.btn-expandir i').removeClass('bi-chevron-right').addClass('bi-chevron-down');
}

function recolherTodos() {
    $('.linha-filha').hide();
    $('.btn-expandir i').removeClass('bi-chevron-down').addClass('bi-chevron-right');
}

function atualizarExibicao() {
    construirTabela();
}

function formatarMoeda(valor) {
    if (valor === null || valor === undefined) return 'R$ 0,00';
    
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
}

function formatarCodigoDescricao(codigo, descricao) {
    const tipo = $('#tipoExibicao').val();
    const maxLength = 50;
    
    let descricaoTruncada = descricao || 'Sem descrição';
    if (descricaoTruncada.length > maxLength) {
        descricaoTruncada = descricaoTruncada.substring(0, maxLength) + '...';
    }
    
    if (tipo === 'codigo') {
        return codigo;
    } else if (tipo === 'descricao') {
        return `<span title="${descricao || codigo}">${descricaoTruncada}</span>`;
    } else {
        return `<span title="${descricao || ''}">${codigo} - ${descricaoTruncada}</span>`;
    }
}

function formatarParaExport(codigo, descricao, tipo) {
    if (tipo === 'codigo') {
        return codigo;
    } else if (tipo === 'descricao') {
        return descricao || codigo;
    } else {
        return codigo + ' - ' + (descricao || 'Sem descrição');
    }
}

function getClasseVariacao(valor) {
    if (valor > 0) return 'text-success';
    if (valor < 0) return 'text-danger';
    return 'text-muted';
}

function formatarVariacaoPercentual(valor) {
    const sinal = valor > 0 ? '↑' : valor < 0 ? '↓' : '→';
    return sinal + ' ' + Math.abs(valor).toFixed(2) + '%';
}

function mostrarAlerta(tipo, mensagem) {
    const alertHtml = `
        <div class="alert alert-${tipo} alert-dismissible fade show" role="alert">
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('#modalInconsistencias .modal-body').prepend(alertHtml);
    
    setTimeout(() => {
        $('.alert').fadeOut(() => $('.alert').remove());
    }, 5000);
}

// FIM DO ARQUIVO