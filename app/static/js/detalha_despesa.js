// JavaScript para Detalha Conta Contábil Despesa
console.log('Arquivo detalha_despesa.js carregado');

let tabelaDados = null;
let dadosAtuais = [];
let totaisGlobais = null;
let temMaisRegistros = false;

// Mapeamento de nomes de colunas
const nomesColunas = {
    'mes': 'Mês',
    'nudocumento': 'Documento',
    'coevento': 'Evento',
    'cocontacorrente': 'Conta Corrente',
    'valancamento': 'Valor',
    'indebitocredito': 'D/C',
    'coug': 'UG',
    'dalancamento': 'Data',
    'tipo_lancamento': 'Tipo',
    'conatureza': 'Natureza',
    'cofonte': 'Fonte',
    'couo': 'UO',
    'coprograma': 'Programa'
};

// Ordem correta dos meses
const ordemMeses = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
    7: 7, 8: 8, 9: 9, 10: 10, 11: 11, 12: 12
};

// Inicialização
$(document).ready(function() {
    console.log('Página carregada, iniciando...');
    carregarFiltros();
    configurarEventos();
});

// Carregar opções dos filtros
function carregarFiltros() {
    console.log('Iniciando carregamento de filtros...');
    
    const url = '/detalha-despesa/api/filtros';
    console.log('URL da API:', url);
    
    $.ajax({
        url: url,
        method: 'GET',
        timeout: 30000, // 30 segundos de timeout
        beforeSend: function() {
            console.log('Enviando requisição...');
            // Desabilitar selects enquanto carrega
            $('#selectAno, #selectConta, #selectUG').prop('disabled', true);
        },
        success: function(data) {
            console.log('Filtros carregados:', data);
            
            // Anos
            $('#selectAno').empty().append('<option value="">Selecione o ano...</option>');
            if (data.anos && data.anos.length > 0) {
                data.anos.forEach(function(ano) {
                    $('#selectAno').append(`<option value="${ano}">${ano}</option>`);
                });
            }
            
            // Contas
            $('#selectConta').empty().append('<option value="">Selecione a conta...</option>');
            if (data.contas && data.contas.length > 0) {
                data.contas.forEach(function(conta) {
                    $('#selectConta').append(`<option value="${conta}">${conta}</option>`);
                });
            }
            
            // UGs Contábeis
            $('#selectUG').empty().append('<option value="">Selecione a UG Contábil...</option>');
            $('#selectUG').append('<option value="CONSOLIDADO">CONSOLIDADO</option>');
            if (data.ugs && data.ugs.length > 0) {
                data.ugs.forEach(function(ug) {
                    if (typeof ug === 'object') {
                        $('#selectUG').append(`<option value="${ug.valor}">${ug.texto}</option>`);
                    } else {
                        $('#selectUG').append(`<option value="${ug}">${ug}</option>`);
                    }
                });
            }
            
            // Mostrar aviso sobre cache
            if (data.cache_disponivel === false) {
                console.warn('Cache não disponível. Considere executar scripts/otimizar_despesas.py');
            }
            
            // Habilitar selects novamente
            $('#selectAno, #selectConta, #selectUG').prop('disabled', false);
        },
        error: function(xhr, textStatus, errorThrown) {
            console.error('Erro ao carregar filtros:', textStatus, errorThrown);
            console.error('Detalhes:', xhr);
            
            let erro = 'Erro desconhecido';
            if (textStatus === 'timeout') {
                erro = 'Tempo limite excedido. Execute scripts/otimizar_despesas.py para melhorar performance.';
            } else if (xhr.responseJSON && xhr.responseJSON.erro) {
                erro = xhr.responseJSON.erro;
            }
            
            mostrarErro('#mensagemInicial', 'Erro ao carregar filtros: ' + erro);
            
            // Habilitar selects novamente
            $('#selectAno, #selectConta, #selectUG').prop('disabled', false);
        }
    });
}

// Configurar eventos
function configurarEventos() {
    $('#formFiltros').on('submit', function(e) {
        e.preventDefault();
        consultarDados();
    });
    
    $('#btnLimpar').on('click', function() {
        limparFiltros();
    });
    
    $('#btnExportar').on('click', function() {
        exportarExcel();
    });
}

// Limpar filtros
function limparFiltros() {
    $('#selectAno').val('');
    $('#selectConta').val('');
    $('#selectUG').val('');
    
    $('#areaResultados').hide();
    $('#mensagemInicial').show();
    
    if (tabelaDados) {
        tabelaDados.destroy();
        $('#divTabela').empty();
    }
    
    // Limpar totais
    $('#totalCreditos').text('R$ 0,00');
    $('#totalDebitos').text('R$ 0,00');
    $('#saldoTotal').text('R$ 0,00');
    $('#qtdCreditos').text('0 lançamentos');
    $('#qtdDebitos').text('0 lançamentos');
    $('#totalLancamentos').text('0');
    $('#formulaSaldo').text('');
    $('#infoLimite').text('');
    $('#avisoLimite').hide();
    $('#cardTopNaturezas').hide();
    
    // Limpar variáveis globais
    dadosAtuais = [];
    totaisGlobais = null;
    temMaisRegistros = false;
}

// Consultar dados
function consultarDados() {
    const ano = $('#selectAno').val();
    const conta = $('#selectConta').val();
    const ug = $('#selectUG').val();
    
    if (!ano || !conta || !ug) {
        alert('Por favor, preencha todos os filtros!');
        return;
    }
    
    $('#modalLoading').modal('show');
    $('#mensagemInicial').hide();
    
    // Buscar dados com limite
    $.ajax({
        url: '/detalha-despesa/api/dados',
        method: 'GET',
        data: {
            ano: ano,
            conta: conta,
            ug: ug,
            limite: 1000  // Limite padrão
        },
        success: function(response) {
            dadosAtuais = response.dados;
            temMaisRegistros = response.tem_mais;
            
            // Mostrar aviso se há mais registros
            if (temMaisRegistros) {
                $('#avisoLimite').show();
                $('#textoAvisoLimite').text(
                    `Exibindo ${response.total.toLocaleString('pt-BR')} de ${response.total_registros.toLocaleString('pt-BR')} lançamentos. ` +
                    `Para visualizar todos os registros, exporte para Excel.`
                );
            } else {
                $('#avisoLimite').hide();
            }
            
            // Buscar totais
            $.ajax({
                url: '/detalha-despesa/api/totais',
                method: 'GET',
                data: {
                    ano: ano,
                    conta: conta,
                    ug: ug
                },
                success: function(totais) {
                    totaisGlobais = totais;
                    atualizarTotais(totais);
                    construirTabela(dadosAtuais);
                    mostrarTopNaturezas(totais.top_naturezas);
                    $('#areaResultados').show();
                    $('#modalLoading').modal('hide');
                },
                error: function(xhr) {
                    $('#modalLoading').modal('hide');
                    console.error('Erro ao buscar totais:', xhr);
                }
            });
        },
        error: function(xhr) {
            $('#modalLoading').modal('hide');
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            mostrarErro('#divTabela', 'Erro ao consultar dados: ' + erro);
            $('#areaResultados').show();
        }
    });
}

// Atualizar cards de totais
function atualizarTotais(totais) {
    $('#totalCreditos').text(formatarMoeda(totais.credito.total));
    $('#totalDebitos').text(formatarMoeda(totais.debito.total));
    $('#saldoTotal').text(formatarMoeda(totais.saldo));
    
    $('#qtdCreditos').text(totais.credito.quantidade.toLocaleString('pt-BR') + ' lançamentos');
    $('#qtdDebitos').text(totais.debito.quantidade.toLocaleString('pt-BR') + ' lançamentos');
    
    const totalLancamentos = totais.credito.quantidade + totais.debito.quantidade;
    $('#totalLancamentos').text(totalLancamentos.toLocaleString('pt-BR'));
    
    // Mostrar informação sobre limite
    if (temMaisRegistros) {
        $('#infoLimite').html('<i class="bi bi-exclamation-triangle"></i> Limitado a 1.000');
    } else {
        $('#infoLimite').text('');
    }
    
    // Mostrar fórmula do saldo baseado na conta
    const conta = $('#selectConta').val();
    if (conta && conta.startsWith('5')) {
        $('#formulaSaldo').text('(Débitos - Créditos)');
    } else {
        $('#formulaSaldo').text('(Créditos - Débitos)');
    }
    
    // Colorir saldo conforme valor
    if (totais.saldo < 0) {
        $('#saldoTotal').removeClass('text-positive').addClass('text-negative');
    } else {
        $('#saldoTotal').removeClass('text-negative').addClass('text-positive');
    }
}

// Mostrar top naturezas de despesa
function mostrarTopNaturezas(naturezas) {
    if (!naturezas || naturezas.length === 0) {
        $('#cardTopNaturezas').hide();
        return;
    }
    
    let html = '';
    const valorMaximo = Math.max(...naturezas.map(n => n.total));
    
    naturezas.forEach(function(nat, index) {
        const percentual = (nat.total / valorMaximo) * 100;
        html += `
            <div class="natureza-item">
                <div style="flex: 1;">
                    <strong>${nat.natureza}</strong>
                    <small class="text-muted">(${nat.quantidade.toLocaleString('pt-BR')} lanç.)</small>
                </div>
                <div style="width: 150px; text-align: right;">
                    ${formatarMoeda(nat.total)}
                </div>
            </div>
            <div class="progress mb-2" style="height: 10px;">
                <div class="progress-bar bg-danger" role="progressbar" 
                     style="width: ${percentual}%" 
                     aria-valuenow="${percentual}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                </div>
            </div>
        `;
    });
    
    $('#divTopNaturezas').html(html);
    $('#cardTopNaturezas').show();
}

// Construir tabela com os dados
function construirTabela(dados) {
    if (!dados || dados.length === 0) {
        $('#divTabela').html('<p class="text-center text-muted py-3">Nenhum lançamento encontrado.</p>');
        return;
    }
    
    // Construir HTML da tabela
    let html = '<table id="tabelaDados" class="table table-striped table-hover">';
    html += '<thead><tr>';
    html += '<th>Mês</th>';
    html += '<th>Documento</th>';
    html += '<th>Evento</th>';
    html += '<th>Natureza</th>';
    html += '<th>Conta Corrente</th>';
    html += '<th>Valor</th>';
    html += '<th>D/C</th>';
    html += '<th>UG</th>';
    html += '<th>Data</th>';
    html += '<th>Tipo</th>';
    html += '</tr></thead><tbody>';
    
    // Adicionar dados
    dados.forEach(function(row) {
        html += '<tr>';
        
        // Mês
        html += `<td data-order="${row.mes}">${formatarMes(row.mes)}</td>`;
        
        // Documento
        html += `<td>${row.nudocumento || '-'}</td>`;
        
        // Evento
        html += `<td>${row.coevento || '-'}</td>`;
        
        // Natureza de Despesa
        if (row.conatureza) {
            html += `<td><span class="natureza-cell">${row.conatureza}</span></td>`;
        } else {
            html += `<td>-</td>`;
        }
        
        // Conta Corrente (truncar se muito grande)
        let contaCorrente = row.cocontacorrente || '-';
        if (contaCorrente.length > 20) {
            html += `<td title="${contaCorrente}">${contaCorrente.substring(0, 20)}...</td>`;
        } else {
            html += `<td>${contaCorrente}</td>`;
        }
        
        // Valor
        let valor = formatarNumero(row.valancamento);
        let classeValor = row.tipo_lancamento === 'CREDITO' ? 'text-positive' : 'text-negative';
        html += `<td class="text-end ${classeValor}">${valor}</td>`;
        
        // D/C
        html += `<td class="text-center">${row.indebitocredito || '-'}</td>`;
        
        // UG
        html += `<td>${row.coug || '-'}</td>`;
        
        // Data
        html += `<td>${row.dalancamento || '-'}</td>`;
        
        // Tipo
        let classeTipo = row.tipo_lancamento === 'CREDITO' ? 'badge-credito' : 'badge-debito';
        html += `<td><span class="badge ${classeTipo}">${row.tipo_lancamento || '-'}</span></td>`;
        
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    $('#divTabela').html(html);
    
    if (tabelaDados) {
        tabelaDados.destroy();
    }
    
    // Inicializar DataTable
    tabelaDados = $('#tabelaDados').DataTable({
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Todos"]],
        dom: 'Blfrtip',
        buttons: [],
        order: [[0, 'asc'], [8, 'asc']], // Ordenar por mês e data
        columnDefs: [
            {
                targets: 0, // Coluna do mês
                type: 'num'
            },
            {
                targets: 5, // Coluna de valor
                type: 'num-fmt'
            }
        ],
        initComplete: function() {
            // Adicionar filtros nas colunas específicas
            this.api().columns().every(function(index) {
                var column = this;
                var title = $(column.header()).text();
                
                // Adicionar filtros apenas nas colunas: Mês, Documento, Evento, Natureza e Conta Corrente
                if (index === 0 || index === 1 || index === 2 || index === 3 || index === 4) {
                    var select = $('<select class="form-select form-select-sm"><option value="">Todos</option></select>')
                        .appendTo($(column.header()))
                        .on('change', function() {
                            var val = $.fn.dataTable.util.escapeRegex($(this).val());
                            column.search(val ? '^' + val + '$' : '', true, false).draw();
                        })
                        .on('click', function(e) {
                            e.stopPropagation();
                        });
                    
                    column.data().unique().sort().each(function(d, j) {
                        if (d && d !== '-') {
                            // Para natureza, remover tags HTML
                            if (index === 3) {
                                d = $(d).text() || d;
                            }
                            select.append('<option value="' + d + '">' + d + '</option>');
                        }
                    });
                }
            });
        }
    });
}

// Formatar mês
function formatarMes(mes) {
    const meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    };
    return meses[mes] || mes;
}

// Formatar número
function formatarNumero(valor) {
    if (valor === null || valor === undefined) return '0,00';
    
    return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
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
    
    let csv = [];
    
    // Cabeçalho
    csv.push(['Mês', 'Documento', 'Evento', 'Natureza', 'Conta Corrente', 'Valor', 'D/C', 'UG', 'Data', 'Tipo', 'Fonte', 'UO', 'Programa'].join(';'));
    
    // Dados
    dadosAtuais.forEach(function(row) {
        let linha = [
            formatarMes(row.mes),
            row.nudocumento || '',
            row.coevento || '',
            row.conatureza || '',
            row.cocontacorrente || '',
            (row.valancamento || 0).toString().replace('.', ','),
            row.indebitocredito || '',
            row.coug || '',
            row.dalancamento || '',
            row.tipo_lancamento || '',
            row.cofonte || '',
            row.couo || '',
            row.coprograma || ''
        ];
        csv.push(linha.join(';'));
    });
    
    // Adicionar totais no final (se temos os totais globais)
    if (totaisGlobais) {
        csv.push(''); // Linha vazia
        csv.push(['RESUMO'].join(';'));
        csv.push(['Tipo', 'Quantidade', 'Valor Total'].join(';'));
        csv.push(['Créditos', totaisGlobais.credito.quantidade, totaisGlobais.credito.total.toFixed(2).replace('.', ',')].join(';'));
        csv.push(['Débitos', totaisGlobais.debito.quantidade, totaisGlobais.debito.total.toFixed(2).replace('.', ',')].join(';'));
        
        const conta = $('#selectConta').val();
        if (conta && conta.startsWith('5')) {
            csv.push(['Saldo (D-C)', '', totaisGlobais.saldo.toFixed(2).replace('.', ',')].join(';'));
        } else {
            csv.push(['Saldo (C-D)', '', totaisGlobais.saldo.toFixed(2).replace('.', ',')].join(';'));
        }
        
        // Adicionar top naturezas se existir
        if (totaisGlobais.top_naturezas && totaisGlobais.top_naturezas.length > 0) {
            csv.push(''); // Linha vazia
            csv.push(['TOP 5 NATUREZAS DE DESPESA'].join(';'));
            csv.push(['Natureza', 'Quantidade', 'Valor Total'].join(';'));
            totaisGlobais.top_naturezas.forEach(function(nat) {
                csv.push([nat.natureza, nat.quantidade, nat.total.toFixed(2).replace('.', ',')].join(';'));
            });
        }
        
        // Aviso sobre limite
        if (temMaisRegistros) {
            csv.push(''); // Linha vazia
            csv.push(['ATENÇÃO: Esta exportação contém apenas os primeiros 1.000 registros.'].join(';'));
            csv.push(['Para exportar todos os registros, utilize a funcionalidade de exportação completa do sistema.'].join(';'));
        }
    }
    
    // Criar arquivo
    let csvContent = '\ufeff' + csv.join('\n');
    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `detalha_despesa_${$('#selectAno').val()}_${$('#selectConta').val()}_${$('#selectUG').val()}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}