// JavaScript para Relatório Detalhado por Fonte/Receita
console.log('Arquivo relatorio_receita_fonte.js carregado');

let dadosAtuais = [];
let totaisGerais = {};
let modoAtual = 'fonte';
let tabelaDados = null;
let dadosLancamentosCompletos = [];

// Inicialização
$(document).ready(function() {
    console.log('Document ready - iniciando carregamento dos dados');
    configurarEventos();
    carregarListaUGs();  // Carregar lista de UGs primeiro
});

// Configurar eventos
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

// Carregar lista de UGs disponíveis
function carregarListaUGs() {
    console.log('Carregando lista de UGs...');
    
    $.ajax({
        url: '/relatorio-receita-fonte/api/lista-ugs',
        method: 'GET',
        success: function(response) {
            console.log('✅ Lista de UGs carregada:', response.total, 'UGs');
            
            // Limpar select mantendo apenas a opção consolidado
            $('#filtroUG').html('<option value="">Consolidado (Todas as UGs)</option>');
            
            // Adicionar UGs ao select
            response.ugs.forEach(function(ug) {
                const option = $('<option></option>')
                    .attr('value', ug.coug)
                    .text(ug.coug + ' - ' + ug.noug);
                $('#filtroUG').append(option);
            });
            
            // Atualizar contador no label
            const label = $('label[for="filtroUG"]');
            label.html('Unidade Gestora (UG): <span class="badge bg-secondary">' + response.total + ' UGs disponíveis</span>');
            
            // Após carregar as UGs, carregar os dados
            carregarDados();
        },
        error: function(xhr) {
            console.error('❌ Erro ao carregar lista de UGs:', xhr);
            // Mesmo com erro, tenta carregar os dados (modo consolidado)
            carregarDados();
        }
    });
}

// Carregar dados baseado no modo selecionado
function carregarDados() {
    console.log('Carregando dados - Modo:', modoAtual);
    
    const ugSelecionada = $('#filtroUG').val();
    console.log('UG selecionada:', ugSelecionada || 'Consolidado');
    
    // Adicionar indicador visual sutil de carregamento na tabela
    $('#divTabela').html('<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div></div>');
    
    const url = modoAtual === 'fonte' 
        ? '/relatorio-receita-fonte/api/dados-por-fonte'
        : '/relatorio-receita-fonte/api/dados-por-receita';
    
    // Adicionar parâmetro de UG se selecionada
    const params = ugSelecionada ? { coug: ugSelecionada } : {};
    
    $.ajax({
        url: url,
        method: 'GET',
        data: params,
        success: function(response) {
            console.log('✅ Dados carregados:', response);
            
            dadosAtuais = response.dados;
            totaisGerais = response.totais;
            
            // Atualizar anos nos cards
            $('#anoAtual').text(response.ano_atual);
            
            // Atualizar cards de totais
            atualizarCards();
            
            // Construir tabela
            construirTabela();
            
            // Atualizar título e contador
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

// Atualizar cards de totais
function atualizarCards() {
    $('#totalPrevisaoInicial').text(formatarMoeda(totaisGerais.previsao_inicial));
    $('#totalPrevisaoAtualizada').text(formatarMoeda(totaisGerais.previsao_atualizada));
    $('#totalRealizadaAtual').text(formatarMoeda(totaisGerais.realizada_atual));
    
    // Variação com indicador visual
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

// Construir tabela hierárquica
function construirTabela() {
    if (!dadosAtuais || dadosAtuais.length === 0) {
        $('#divTabela').html('<p class="text-center text-muted py-3">Nenhum dado encontrado.</p>');
        return;
    }
    
    // Destruir tabela anterior se existir
    if (tabelaDados) {
        tabelaDados.destroy();
        $('#divTabela').empty();
    }
    
    let html = '<table id="tabelaDados" class="table table-hover">';
    
    // Cabeçalho
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
    
    // Corpo
    html += '<tbody>';
    
    // Adicionar linhas hierárquicas
    dadosAtuais.forEach(function(item, index) {
        const itemId = modoAtual === 'fonte' ? item.cofonte : item.coalinea;
        const itemNome = modoAtual === 'fonte' ? item.nome_fonte : item.nome_alinea;
        const subitens = modoAtual === 'fonte' ? item.alineas : item.fontes;
        
        // Ordenar subitens por valor realizado atual (maior para menor)
        if (subitens && subitens.length > 0) {
            subitens.sort((a, b) => b.realizada_atual - a.realizada_atual);
        }
        
        // Linha principal (sem botão de ação agora)
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
        html += '<td></td>'; // Célula vazia para alinhar com as filhas
        html += '</tr>';
        
        // Linhas filhas (colapsáveis) - AGORA COM BOTÃO DE AÇÃO
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
                
                // Botão de ação na linha filha
                if (modoAtual === 'fonte') {
                    // Se estamos vendo por fonte, a linha mãe é cofonte e filha é coalinea
                    html += '<button class="btn btn-sm btn-outline-primary btn-detalhes" ';
                    html += 'data-cofonte="' + itemId + '" ';
                    html += 'data-coalinea="' + subitemId + '" ';
                    html += 'data-nome-fonte="' + (itemNome || '') + '" ';
                    html += 'data-nome-alinea="' + (subitemNome || '') + '">';
                } else {
                    // Se estamos vendo por receita, a linha mãe é coalinea e filha é cofonte
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
    
    // Rodapé com totais
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
    
    // Configurar eventos de expansão/colapso
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
    
    // Configurar eventos de detalhes
    $('.btn-detalhes').on('click', function() {
        const cofonte = $(this).data('cofonte');
        const coalinea = $(this).data('coalinea');
        const nomeFonte = $(this).data('nome-fonte');
        const nomeAlinea = $(this).data('nome-alinea');
        
        console.log('Ver detalhes - Fonte:', cofonte, 'Alínea:', coalinea);
        abrirModalDetalhes(cofonte, coalinea, nomeFonte, nomeAlinea);
    });
}

// Abrir modal de detalhes
function abrirModalDetalhes(cofonte, coalinea, nomeFonte, nomeAlinea) {
    // Limpar modal
    $('#tabelaDetalhes tbody').html('<tr><td colspan="6" class="text-center"><div class="spinner-border spinner-border-sm"></div> Carregando...</td></tr>');
    $('#alertaLimite').hide();
    
    // Atualizar título do modal
    const titulo = `Detalhes dos Lançamentos<br>
                   <small class="text-muted">
                   Fonte: ${cofonte} - ${nomeFonte || 'Sem descrição'}<br>
                   Alínea: ${coalinea} - ${nomeAlinea || 'Sem descrição'}
                   </small>`;
    $('#modalDetalhesLabel').html(titulo);
    
    // Abrir modal
    $('#modalDetalhes').modal('show');
    
    // Buscar dados
    const ano = $('#anoAtual').text();
    const coug = $('#filtroUG').val(); // Pegar a UG selecionada
    
    // Montar parâmetros da requisição
    const params = {
        cofonte: cofonte,
        coalinea: coalinea,
        ano: ano
    };
    
    // Adicionar coug se estiver filtrado
    if (coug) {
        params.coug = coug;
    }
    
    $.ajax({
        url: '/relatorio-receita-fonte/api/detalhes-lancamentos',
        method: 'GET',
        data: params,
        success: function(response) {
            console.log('✅ Detalhes carregados:', response);
            
            // Guardar dados completos para exportação
            dadosLancamentosCompletos = response;
            
            // Atualizar resumo
            $('#resumoTotalDebito').text(formatarMoeda(response.total_debito));
            $('#resumoTotalCredito').text(formatarMoeda(response.total_credito));
            $('#resumoSaldo').text(formatarMoeda(response.saldo));
            $('#resumoTotalRegistros').text(response.total_registros.toLocaleString('pt-BR'));
            
            // Mostrar alerta se dados foram limitados
            if (response.limitado) {
                $('#alertaLimite').show();
                $('#textoLimite').html(`
                    <i class="bi bi-info-circle"></i> 
                    Exibindo apenas os primeiros 1.000 registros de um total de ${response.total_registros.toLocaleString('pt-BR')}.
                    <br>Para obter todos os registros, use o botão "Exportar Excel" abaixo.
                `);
            }
            
            // Construir tabela
            construirTabelaDetalhes(response.dados);
        },
        error: function(xhr) {
            console.error('❌ Erro ao carregar detalhes:', xhr);
            
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            $('#tabelaDetalhes tbody').html(
                '<tr><td colspan="6" class="text-center text-danger">' +
                '<i class="bi bi-exclamation-triangle"></i> Erro ao carregar dados: ' + erro +
                '</td></tr>'
            );
        }
    });
}

// Construir tabela de detalhes no modal
function construirTabelaDetalhes(dados) {
    if (!dados || dados.length === 0) {
        $('#tabelaDetalhes tbody').html('<tr><td colspan="6" class="text-center text-muted">Nenhum lançamento encontrado.</td></tr>');
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

// Exportar detalhes para Excel
function exportarDetalhesExcel() {
    if (!dadosLancamentosCompletos || !dadosLancamentosCompletos.cofonte) {
        alert('Não há dados para exportar!');
        return;
    }
    
    console.log('📊 Exportando detalhes completos...');
    
    // Mostrar loading
    const btnOriginal = $('#btnExportarDetalhes').html();
    $('#btnExportarDetalhes').html('<span class="spinner-border spinner-border-sm"></span> Baixando todos os dados...');
    $('#btnExportarDetalhes').prop('disabled', true);
    
    // Buscar TODOS os dados (sem limite)
    const coug = $('#filtroUG').val(); // Pegar a UG selecionada
    
    const params = {
        cofonte: dadosLancamentosCompletos.cofonte,
        coalinea: dadosLancamentosCompletos.coalinea,
        ano: dadosLancamentosCompletos.ano,
        exportar: 'true'  // Flag para trazer todos os registros
    };
    
    // Adicionar coug se estiver filtrado
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
            
            // Cabeçalho do relatório
            csv.push(['RELATÓRIO DE DETALHES DE LANÇAMENTOS'].join(';'));
            csv.push(['Fonte: ' + response.cofonte + ' - ' + response.nome_fonte].join(';'));
            csv.push(['Alínea: ' + response.coalinea + ' - ' + response.nome_alinea].join(';'));
            csv.push(['Ano: ' + response.ano].join(';'));
            csv.push(['Total de Registros: ' + response.total_registros].join(';'));
            csv.push('');
            
            // Resumo
            csv.push(['RESUMO'].join(';'));
            csv.push(['Total Débito;' + response.total_debito.toFixed(2).replace('.', ',')].join(''));
            csv.push(['Total Crédito;' + response.total_credito.toFixed(2).replace('.', ',')].join(''));
            csv.push(['Saldo;' + response.saldo.toFixed(2).replace('.', ',')].join(''));
            csv.push('');
            
            // Cabeçalho da tabela
            const headers = [
                'Conta Contábil',
                'Descrição Conta',
                'UG Emitente',
                'Nome UG',
                'Documento',
                'Evento',
                'Descrição Evento',
                'D/C',
                'Valor',
                'Data Lançamento',
                'Grupo'
            ];
            csv.push(headers.join(';'));
            
            // Dados
            response.dados.forEach(function(item) {
                let linha = [
                    item.cocontacontabil,
                    item.nocontacontabil || '',
                    item.coug,
                    item.noug || '',
                    item.nudocumento,
                    item.coevento,
                    item.noevento || '',
                    item.indebitocredito,
                    item.valancamento.toFixed(2).replace('.', ','),
                    item.dtlancamento || '',
                    item.sigrupo || ''
                ];
                csv.push(linha.join(';'));
            });
            
            // Metadados
            csv.push('');
            csv.push(['Data da exportação: ' + new Date().toLocaleString('pt-BR')].join(';'));
            
            // Download
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
            
            // Restaurar botão
            $('#btnExportarDetalhes').html(btnOriginal);
            $('#btnExportarDetalhes').prop('disabled', false);
        },
        error: function(xhr) {
            console.error('❌ Erro ao exportar:', xhr);
            alert('Erro ao exportar dados. Tente novamente.');
            
            // Restaurar botão
            $('#btnExportarDetalhes').html(btnOriginal);
            $('#btnExportarDetalhes').prop('disabled', false);
        }
    });
}

// Formatar código e descrição baseado na seleção
function formatarCodigoDescricao(codigo, descricao) {
    const tipo = $('#tipoExibicao').val();
    const maxLength = 50; // Máximo de caracteres para o nome
    
    // Truncar descrição se muito longa
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

// Obter classe CSS para variação
function getClasseVariacao(valor) {
    if (valor > 0) return 'text-success';
    if (valor < 0) return 'text-danger';
    return 'text-muted';
}

// Formatar variação percentual
function formatarVariacaoPercentual(valor) {
    const sinal = valor > 0 ? '↑' : valor < 0 ? '↓' : '→';
    return sinal + ' ' + Math.abs(valor).toFixed(2) + '%';
}

// Expandir todos
function expandirTodos() {
    $('.linha-filha').show();
    $('.btn-expandir i').removeClass('bi-chevron-right').addClass('bi-chevron-down');
}

// Recolher todos
function recolherTodos() {
    $('.linha-filha').hide();
    $('.btn-expandir i').removeClass('bi-chevron-down').addClass('bi-chevron-right');
}

// Atualizar exibição quando mudar o tipo
function atualizarExibicao() {
    construirTabela();
}

// Formatar moeda
function formatarMoeda(valor) {
    if (valor === null || valor === undefined) return 'R$ 0,00';
    
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
}

// Exportar para Excel
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
    
    // Cabeçalho do relatório
    csv.push(['RELATÓRIO DETALHADO POR ' + (modoAtual === 'fonte' ? 'FONTE' : 'RECEITA')].join(';'));
    csv.push(['UG: ' + textoUG].join(';'));
    csv.push('');
    
    // Cabeçalho da tabela
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
    
    // Dados
    dadosAtuais.forEach(function(item) {
        const itemId = modoAtual === 'fonte' ? item.cofonte : item.coalinea;
        const itemNome = modoAtual === 'fonte' ? item.nome_fonte : item.nome_alinea;
        const subitens = modoAtual === 'fonte' ? item.alineas : item.fontes;
        
        // Linha principal
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
        
        // Subitens
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
    
    // Linha de total
    csv.push('');
    let linhaTotal = [
        'TOTAL GERAL',
        '',
        totaisGerais.previsao_inicial.toFixed(2).replace('.', ','),
        totaisGerais.previsao_atualizada.toFixed(2).replace('.', ','),
        totaisGerais.realizada_atual.toFixed(2).replace('.', ','),
        totaisGerais.realizada_anterior.toFixed(2).replace('.', ','),
        totaisGerais.variacao_absoluta.toFixed(2).replace('.', ','),
        totaisGerais.variacao_percentual.toFixed(2).replace('.', ',')
    ];
    csv.push(linhaTotal.join(';'));
    
    // Metadados
    csv.push('');
    csv.push(['Relatório Detalhado por ' + (modoAtual === 'fonte' ? 'Fonte' : 'Receita')].join(';'));
    csv.push(['Data da exportação: ' + new Date().toLocaleString('pt-BR')].join(';'));
    
    // Download
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

// Formatar para exportação
function formatarParaExport(codigo, descricao, tipo) {
    if (tipo === 'codigo') {
        return codigo;
    } else if (tipo === 'descricao') {
        return descricao || codigo;
    } else {
        return codigo + ' - ' + (descricao || 'Sem descrição');
    }
}