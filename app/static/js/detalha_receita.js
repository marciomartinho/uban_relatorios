// JavaScript para Detalha Conta Contábil Receita
console.log('Arquivo detalha_receita.js carregado');

let tabelaDados = null;
let dadosAtuais = [];

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
    'tipo_lancamento': 'Tipo'
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
    
    const url = '/detalha-receita/api/filtros';
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
                    $('#selectUG').append(`<option value="${ug}">${ug}</option>`);
                });
            }
            
            // Habilitar selects novamente
            $('#selectAno, #selectConta, #selectUG').prop('disabled', false);
        },
        error: function(xhr, textStatus, errorThrown) {
            console.error('Erro ao carregar filtros:', textStatus, errorThrown);
            console.error('Detalhes:', xhr);
            
            let erro = 'Erro desconhecido';
            if (textStatus === 'timeout') {
                erro = 'Tempo limite excedido. A consulta está demorando muito.';
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
    
    // Buscar dados
    $.ajax({
        url: '/detalha-receita/api/dados',
        method: 'GET',
        data: {
            ano: ano,
            conta: conta,
            ug: ug
        },
        success: function(response) {
            dadosAtuais = response.dados;
            
            // Buscar totais
            $.ajax({
                url: '/detalha-receita/api/totais',
                method: 'GET',
                data: {
                    ano: ano,
                    conta: conta,
                    ug: ug
                },
                success: function(totais) {
                    atualizarTotais(totais);
                    construirTabela(dadosAtuais);
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
    
    $('#qtdCreditos').text(totais.credito.quantidade + ' lançamentos');
    $('#qtdDebitos').text(totais.debito.quantidade + ' lançamentos');
    $('#totalLancamentos').text(totais.credito.quantidade + totais.debito.quantidade);
    
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
        
        // Conta Corrente
        html += `<td>${row.cocontacorrente || '-'}</td>`;
        
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
        order: [[0, 'asc'], [6, 'asc']], // Ordenar por mês e data
        columnDefs: [
            {
                targets: 0, // Coluna do mês
                type: 'num'
            },
            {
                targets: 4, // Coluna de valor
                type: 'num-fmt'
            }
        ],
        initComplete: function() {
            // Adicionar filtros nas colunas específicas
            this.api().columns().every(function(index) {
                var column = this;
                var title = $(column.header()).text();
                
                // Adicionar filtros apenas nas colunas: Mês, Documento, Evento e Conta Corrente
                if (index === 0 || index === 1 || index === 2 || index === 3) {
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
    csv.push(['Mês', 'Documento', 'Evento', 'Conta Corrente', 'Valor', 'D/C', 'UG', 'Data', 'Tipo'].join(';'));
    
    // Dados
    dadosAtuais.forEach(function(row) {
        let linha = [
            formatarMes(row.mes),
            row.nudocumento || '',
            row.coevento || '',
            row.cocontacorrente || '',
            (row.valancamento || 0).toString().replace('.', ','),
            row.indebitocredito || '',
            row.coug || '',
            row.dalancamento || '',
            row.tipo_lancamento || ''
        ];
        csv.push(linha.join(';'));
    });
    
    // Adicionar totais no final
    csv.push(''); // Linha vazia
    csv.push(['RESUMO'].join(';'));
    csv.push(['Tipo', 'Quantidade', 'Valor Total'].join(';'));
    
    let totalCredito = dadosAtuais.filter(d => d.tipo_lancamento === 'CREDITO').reduce((sum, d) => sum + (d.valancamento || 0), 0);
    let totalDebito = dadosAtuais.filter(d => d.tipo_lancamento === 'DEBITO').reduce((sum, d) => sum + (d.valancamento || 0), 0);
    let qtdCredito = dadosAtuais.filter(d => d.tipo_lancamento === 'CREDITO').length;
    let qtdDebito = dadosAtuais.filter(d => d.tipo_lancamento === 'DEBITO').length;
    
    csv.push(['Créditos', qtdCredito, totalCredito.toFixed(2).replace('.', ',')].join(';'));
    csv.push(['Débitos', qtdDebito, totalDebito.toFixed(2).replace('.', ',')].join(';'));
    csv.push(['Saldo (C-D)', '', (totalCredito - totalDebito).toFixed(2).replace('.', ',')].join(';'));
    
    // Criar arquivo
    let csvContent = '\ufeff' + csv.join('\n');
    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `detalha_receita_${$('#selectAno').val()}_${$('#selectConta').val()}_${$('#selectUG').val()}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}